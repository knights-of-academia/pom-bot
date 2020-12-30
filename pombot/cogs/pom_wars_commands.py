import json
import logging
import math
import random
import re
import textwrap
from datetime import datetime, timedelta
from functools import cache
from pathlib import Path
from typing import List

from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.bot import Bot
from discord.user import User

from pombot import errors
from pombot.config import Pomwars, Reactions
from pombot.data import Locations
from pombot.lib.messages import send_embed_message
from pombot.lib.types import DateRange, Team, ActionType
from pombot.storage import Storage

_log = logging.getLogger(__name__)


def _get_user_team(user: User) -> Team:
    team_roles = [
        role for role in user.roles
        if role.name in [Pomwars.KNIGHT_ROLE, Pomwars.VIKING_ROLE]
    ]

    if len(team_roles) != 1:
        raise errors.InvalidNumberOfRolesError()

    return Team(team_roles[0].name)


class Attack:
    """An attack as specified by file and directory structure."""
    def __init__(self, directory: Path, is_heavy: bool, is_critical: bool):
        self.name = directory.name
        self.is_heavy = is_heavy
        self.is_critical = is_critical
        self._message = (directory / Locations.MESSAGE).read_text(encoding="utf8")
        self._meta = (directory / Locations.META).read_text(encoding="utf8")

        self.chance_for_this_attack = None
        self.damage_multiplier = None
        for key, val in json.loads(self._meta).items():
            setattr(self, key, val)

    @property
    def damage(self):
        """The configured base damage for this attack."""
        base_damage = Pomwars.BASE_DAMAGE_FOR_NORMAL_ATTACKS

        if self.is_heavy:
            base_damage = Pomwars.BASE_DAMAGE_FOR_HEAVY_ATTACKS

        return int(base_damage * self.damage_multiplier)

    @property
    def weight(self):
        """The configured base weighted-chance for this attack."""
        return self.chance_for_this_attack

    def get_message(self, user: User) -> str:
        """The markdown-formatted version of the message.txt from the
        attack's directory, and the resulting action, as a string.
        """
        story = re.sub(r"(?<!\n)\n(?!\n)|\n{3,}", " ", self._message)
        action = "{emt} {you} attacked the {team} for {dmg} damage!".format(
            emt=Pomwars.SUCCESSFUL_ATTACK_EMOTE,
            you=f"<@{user.id}>",
            team=f"{(~_get_user_team(user)).value}s",
            dmg=self.damage,
        )

        return "\n\n".join([story, action])


def _load_attacks(location: Path, *, is_heavy: bool, is_critical=False) -> List[Attack]:
    attacks = []
    location = location / "~criticals" if is_critical else location

    for attack_dir in location.iterdir():
        if attack_dir.name.startswith("~"):
            continue

        attacks.append(Attack(attack_dir, is_heavy, is_critical))

    return attacks


def _is_attack_successful(
    user: User,
    is_heavy_attack: bool,
    timestamp: datetime,
) -> bool:
    def _delayed_exponential_drop(num_poms: int):
        operand = lambda x: math.pow(math.e, ((-(x - 9)**2) / 2)) / (math.sqrt(2 * math.pi))

        probabilities = {
            range(0, 6): lambda x: 1.0,
            range(6, 11): lambda x: -0.016 * math.pow(x, 2) + 0.16 * x + 0.6,
            range(11, 1000): lambda x: operand(x) / operand(9)
        }

        for range_, function in probabilities.items():
            if num_poms in range_:
                break
        else:
            function = lambda x: 0.0

        return function(num_poms)

    @cache
    def _get_normal_attack_success_chance(num_poms: int):
        return 1.0 * _delayed_exponential_drop(num_poms)

    @cache
    def _get_heavy_attack_success_chance(num_poms: int):
        return 0.25 * _delayed_exponential_drop(num_poms)

    chance_func = (_get_heavy_attack_success_chance
                   if is_heavy_attack else _get_normal_attack_success_chance)

    date_from_time = lambda x: datetime.strptime(
        datetime.strftime(timestamp, x), "%Y-%m-%d %H:%M:%S")

    this_pom_number = len(Storage.get_actions(user=user, date_range=DateRange(
        date_from_time("%Y-%m-%d 00:00:00"),
        date_from_time("%Y-%m-%d 23:59:59"),
    )))

    return random.random() <= chance_func(this_pom_number)


class PomWarsUserCommands(commands.Cog):
    """Commands used by users during a Pom War."""
    HEAVY_QUALIFIERS = ["heavy", "hard", "sharp", "strong"]

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def attack(self, ctx: Context, *args):
        """Attack the other team."""
        heavy_attack = bool(args) and args[0].casefold() in self.HEAVY_QUALIFIERS
        description = " ".join(args[1:] if heavy_attack else args)
        timestamp = datetime.now()

        Storage.add_poms_to_user_session(
            ctx.author,
            description,
            count=1,
            time_set=timestamp,
        )
        await ctx.message.add_reaction(Reactions.TOMATO)

        action = {
            "user":           ctx.author,
            "team":           _get_user_team(ctx.author),
            "action_type":    ActionType.HEAVY_ATTACK if heavy_attack
                              else ActionType.NORMAL_ATTACK,
            "was_successful": False,
            "was_critical":   False,
            "items_dropped":  "",
            "damage":         None,
            "time_set":       timestamp,
        }

        if not _is_attack_successful(ctx.author, heavy_attack, timestamp):
            emote = random.choice(["¯\\_(ツ)_/¯", "(╯°□°）╯︵ ┻━┻"])
            await ctx.send(f"<@{ctx.author.id}>'s attack missed! {emote}")
            Storage.add_pom_war_action(**action)
            return

        action["was_successful"] = True
        action["was_critical"] = random.random() <= Pomwars.BASE_CHANCE_FOR_CRITICAL
        await ctx.message.add_reaction(Reactions.BOOM)

        attacks = _load_attacks(
            Locations.HEAVY_ATTACKS_DIR
            if heavy_attack else Locations.NORMAL_ATTACKS_DIR,
            is_critical=action["was_critical"],
            is_heavy=heavy_attack,
        )
        weights = [attack.weight for attack in attacks]
        attack, = random.choices(attacks, weights=weights)

        action["damage"] = attack.damage
        Storage.add_pom_war_action(**action)
        await ctx.send(attack.get_message(ctx.author))

    @commands.command()
    async def actions(self, ctx: Context, *args):
        """Get your current, previous, or specific day's actions."""
        date_range = None
        today = datetime.today().strftime("%B %d").split()
        yesterday = (datetime.today() -
                     timedelta(days=1)).strftime("%B %d").split()

        descriptive_dates = {
            "today": DateRange(*today, *today),
            "yesterday": DateRange(*yesterday, *yesterday)
        }

        if args:
            date_range = descriptive_dates.get(args[0].casefold())

        if date_range is None:
            try:
                date_range = DateRange(*args, *args)
            except ValueError:
                today = datetime.today()
                date_range = descriptive_dates["today"]

        actions = Storage.get_actions(user=ctx.author, date_range=date_range)

        if not actions:
            description = "*No recorded actions.*"
        else:
            normal_attacks = [a for a in actions if not a.heavy_attack]
            missed_normal_attacks = [a for a in normal_attacks if not a.was_successful]

            heavy_attacks = [a for a in actions if a.heavy_attack]
            missed_heavy_attacks = [a for a in heavy_attacks if not a.was_successful]

            total_damage = sum([a.damage for a in actions if a.damage])

            description = textwrap.dedent(f"""\
                Normal attacks: {len(normal_attacks)} (missed {len(missed_normal_attacks)})
                Heavy attacks: {len(heavy_attacks)} (missed {len(missed_heavy_attacks)})

                Damage dealt:  :crossed_swords:  _**{total_damage}**_
            """)

        await send_embed_message(
            ctx,
            title=f"Actions for {date_range}",
            description=description,
            icon_url=Pomwars.SAMATTACK_SWORD_URL,
            colour=Pomwars.ACTION_COLOUR,
        )


class PomWarsAdminCommands(commands.Cog):
    """Commands used by admins during a Pom War."""
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.has_any_role("Guardian")
    async def unload_pom_wars(self, ctx: Context):
        """Manually unload the pombot.cogs.pom_wars_commands."""
        await ctx.send("Unloading cog.")
        self.bot.unload_extension("pombot.cogs.pom_wars_commands")


def setup(bot: Bot):
    """Required to load extension."""
    bot.add_cog(PomWarsUserCommands(bot))
    bot.add_cog(PomWarsAdminCommands(bot))
