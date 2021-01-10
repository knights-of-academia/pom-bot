import json
import logging
import math
import random
import re
from datetime import datetime, timedelta
from functools import cache, partial
from pathlib import Path
from typing import Any, List, Union

from discord.ext import commands
from discord.ext.commands import Cog, Context
from discord.ext.commands.bot import Bot
from discord.user import User
import discord.errors

import pombot.errors
from pombot.config import Config, Pomwars, Reactions
from pombot.data import Locations
from pombot.lib.messages import send_embed_message
from pombot.lib.types import DateRange, Team, ActionType
from pombot.storage import Storage
from pombot.state import State
from pombot.scoreboard import Scoreboard

_log = logging.getLogger(__name__)

def _get_user_team(user: User) -> Team:
    team_roles = [
        role for role in user.roles
        if role.name in [Pomwars.KNIGHT_ROLE, Pomwars.VIKING_ROLE]
    ]

    if len(team_roles) != 1:
        raise pombot.errors.InvalidNumberOfRolesError()

    return Team(team_roles[0].name)

class Attack:
    """An attack action as specified by file and directory structure."""
    def __init__(self, directory: Path, is_heavy: bool, is_critical: bool):
        self.name = directory.name
        self.is_heavy = is_heavy
        self.is_critical = is_critical
        self._message = (directory / Locations.MESSAGE).read_text(encoding="utf8")
        self._meta = (directory / Locations.META).read_text(encoding="utf8")

        self.chance_for_this_action = None
        self.damage_multiplier = None
        for key, val in json.loads(self._meta).items():
            setattr(self, key, val)

    @property
    def damage(self):
        """The configured base damage for this action."""
        base_damage = Pomwars.BASE_DAMAGE_FOR_NORMAL_ATTACKS

        if self.is_heavy:
            base_damage = Pomwars.BASE_DAMAGE_FOR_HEAVY_ATTACKS

        return int(base_damage * self.damage_multiplier)

    @property
    def weight(self):
        """The configured base weighted-chance for this action."""
        return self.chance_for_this_action

    def get_message(self, adjusted_damage: int = None) -> str:
        """The markdown-formatted version of the message.txt from the
        action's directory, and its result, as a string.
        """
        action_msgs = [f"** **\n{Pomwars.Emotes.ATTACK} `{{dmg:.2f}} damage!`"]

        if self.is_critical:
            action_msgs += [f"{Pomwars.Emotes.CRITICAL} `Critical attack!`"]

        action = "\n".join(action_msgs).format(
            dmg=adjusted_damage or self.damage,
        )
        story = "*" + re.sub(r"(?<!\n)\n(?!\n)|\n{3,}", " ", self._message) + "*"

        return "\n\n".join([action, story.strip()])

    def get_title(self, user: User) -> str:
        """Title that includes the name of the team user attacked
        """

        title = "You have used{indicator}Attack against {team}!".format(
            indicator = " Heavy " if self.is_heavy else " ",
            team=f"{(~_get_user_team(user)).value}s",
        )

        return title

    def get_colour(self) -> int:
        """
        Change the colour if attack is heavy or not.
        """
        colour = Pomwars.NORMAL_COLOUR

        if self.is_heavy:
            colour = Pomwars.HEAVY_COLOUR

        return colour


class Defend:
    """A defend action as specified by file and directory structure."""
    def __init__(self, directory: Path):
        self.name = directory.name
        self._message = (directory / Locations.MESSAGE).read_text(encoding="utf8")
        self._meta = (directory / Locations.META).read_text(encoding="utf8")

        self.chance_for_this_action = None
        for key, val in json.loads(self._meta).items():
            setattr(self, key, val)

    @property
    def weight(self):
        """The configured base weighted-chance for this action."""
        return self.chance_for_this_action

    def get_message(self, user: User) -> str:
        """The markdown-formatted version of the message.txt from the
        action's directory, and its result, as a string.
        """
        action = "** **\n{emt} `{dfn}% team damage reduction!`".format(
            emt=Pomwars.Emotes.DEFEND,
            dfn=100 * Pomwars.DEFEND_LEVEL_MULTIPLIERS[
                Storage.get_user_by_id(user.id).defend_level
            ]
        )
        story = "*" + re.sub(r"(?<!\n)\n(?!\n)|\n{3,}", " ", self._message) + "*"

        return "\n\n".join([action, story.strip()])


def _load_actions_directories(
    location: Path,
    type_: Union[Attack, Defend],
    *,
    is_heavy: bool = False,
    is_critical: bool = False,
) -> List[Any]:
    actions = []
    location = location / "~criticals" if is_critical else location

    for action_dir in location.iterdir():
        if action_dir.name.startswith("~"):
            continue

        actions.append(
            Attack(action_dir, is_heavy, is_critical) if type_ ==
            Attack else Defend(action_dir))

    return actions


def _is_action_successful(
    user: User,
    timestamp: datetime,
    is_heavy_attack: bool = False,
) -> bool:
    # Tech debt: This function is getting hairy.
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

    def _get_heavy_attack_base_chance(user_id: int) -> float:
        botuser = Storage.get_user_by_id(user_id)
        pity_levels = Pomwars.HEAVY_ATTACK_LEVEL_VALIANT_ATTEMPT_CONDOLENCE_REWARDS
        min_chance, max_chance = pity_levels[botuser.heavy_attack_level]

        # Do not add the +1 to max_chance because it's defaulted to later.
        pity_range = range(*(int(x * 100) for x in (
            min_chance,
            max_chance,
            Pomwars.HEAVY_PITY_INCREMENT,
        )))

        # A modified reducer because functools.reduce() won't break after some
        # condition is met.
        num_misses = 0
        for action in reversed(Storage.get_actions(user=user)):
            if action.was_successful:
                break
            num_misses += 1

        return dict(enumerate(pity_range)).get(num_misses, max_chance * 100) / 100

    @cache
    def _get_normal_attack_success_chance(num_poms: int):
        return 1.0 * _delayed_exponential_drop(num_poms)

    @cache
    def _get_heavy_attack_success_chance(num_poms: int, base_chance: float):
        return base_chance * _delayed_exponential_drop(num_poms)

    if is_heavy_attack:
        base_chance = _get_heavy_attack_base_chance(user.id)
        chance_func = lambda x: _get_heavy_attack_success_chance(x, base_chance)
    else:
        chance_func = _get_normal_attack_success_chance

    date_from_time = lambda x: datetime.strptime(
        datetime.strftime(timestamp, x), "%Y-%m-%d %H:%M:%S")

    this_pom_number = len(Storage.get_actions(user=user, date_range=DateRange(
        date_from_time("%Y-%m-%d 00:00:00"),
        date_from_time("%Y-%m-%d 23:59:59"),
    )))

    return random.random() <= chance_func(this_pom_number)


def _get_defensive_multiplier(team: Team, timestamp: datetime) -> float:
    defend_actions = Storage.get_actions(
        action_type=ActionType.DEFEND,
        team=team,
        was_successful=True,
        date_range=DateRange(
            timestamp - timedelta(minutes=10),
            timestamp,
        ),
    )
    defenders = Storage.get_users_by_id([a.user_id for a in defend_actions])
    multipliers = [Pomwars.DEFEND_LEVEL_MULTIPLIERS[d.defend_level] for d in defenders]

    return min([sum(multipliers), Pomwars.MAXIMUM_TEAM_DEFENCE])


class PomWarsUserCommands(commands.Cog):
    """Commands used by users during a Pom War."""
    HEAVY_QUALIFIERS = ["heavy", "hard", "sharp", "strong"]

    def __init__(self, bot: Bot):
        self.bot = bot

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
            descripts = []

            nrm = [a for a in actions if a.is_normal]
            nrmx = [a for a in nrm if not a.was_successful]
            descripts.append("Normal attacks: {}{}".format(
                len(nrm), f" (missed {len(nrmx)})" if nrmx else "") if nrm else "")

            hvy = [a for a in actions if a.is_heavy]
            hvyx = [a for a in hvy if not a.was_successful]
            descripts.append("Heavy attacks: {}{}".format(
                len(hvy), f" (missed {len(hvyx)})" if hvyx else "") if hvy else "")

            dfn = [a for a in actions if a.is_defend]
            dfnx = [a for a in dfn if not a.was_successful]
            descripts.append("Defends: {}{}".format(
                len(dfn), f" (missed {len(dfnx)})" if dfnx else "") if dfn else "")

            descripts.append(" ")  # &nbsp;

            total = len(actions)
            tot_emote = Reactions.TOMATO
            descripts.append(f"Total poms:  {tot_emote}  _{total}_")

            damage = sum([a.damage for a in actions if a.damage])
            dam_emote = Reactions.CROSSED_SWORDS
            descripts.append(f"Damage dealt:  {dam_emote}  _**{damage:.2f}**_")

            description = "\n".join(d for d in descripts if d)

        try:
            await send_embed_message(
                ctx,
                title=f"Actions for {date_range}",
                description=description,
                icon_url=Pomwars.IconUrls.SWORD,
                colour=Pomwars.ACTION_COLOUR,
                private_message=True,
            )
            await ctx.message.add_reaction(Reactions.CHECKMARK)
        except discord.errors.Forbidden:
            # User disallows DM's from server members.
            await ctx.message.add_reaction(Reactions.WARNING)

    @commands.command()
    async def attack(self, ctx: Context, *args):
        """Attack the other team."""
        heavy_attack = bool(args) and args[0].casefold() in self.HEAVY_QUALIFIERS
        description = " ".join(args[1:] if heavy_attack else args)
        timestamp = datetime.now()

        if len(description) > Config.DESCRIPTION_LIMIT:
            await ctx.message.add_reaction(Reactions.WARNING)
            await ctx.send(f"{ctx.author.mention}, your pom description must "
                           f"be fewer than {Config.DESCRIPTION_LIMIT} characters.")
            return

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

        if not _is_action_successful(ctx.author, timestamp, heavy_attack):
            emote = random.choice(["¯\\_(ツ)_/¯", "(╯°□°）╯︵ ┻━┻"])
            Storage.add_pom_war_action(**action)
            await ctx.send(f"<@{ctx.author.id}>'s attack missed! {emote}")
            return

        action["was_successful"] = True
        action["was_critical"] = random.random() <= Pomwars.BASE_CHANCE_FOR_CRITICAL
        await ctx.message.add_reaction(Reactions.BOOM)

        attacks = _load_actions_directories(
            Locations.HEAVY_ATTACKS_DIR if heavy_attack else Locations.NORMAL_ATTACKS_DIR,
            type_=Attack,
            is_critical=action["was_critical"],
            is_heavy=heavy_attack,
        )
        weights = [attack.weight for attack in attacks]
        attack, = random.choices(attacks, weights=weights)

        defensive_multiplier = _get_defensive_multiplier(
            team=~_get_user_team(ctx.author),
            timestamp=timestamp)

        action["damage"] = attack.damage - attack.damage * defensive_multiplier
        Storage.add_pom_war_action(**action)

        await send_embed_message(
            None,
            title=attack.get_title(ctx.author),
            description=attack.get_message(action["damage"]),
            icon_url=None,
            colour=attack.get_colour(),
            _func=partial(ctx.channel.send, content=ctx.author.mention),
        )

        await State.score.update_msg()

    @commands.command()
    async def defend(self, ctx: Context, *args):
        """Defend your team."""
        timestamp = datetime.now()
        Storage.add_poms_to_user_session(
            ctx.author,
            descript=" ".join(args),
            count=1,
            time_set=timestamp,
        )
        await ctx.message.add_reaction(Reactions.TOMATO)

        action = {
            "user":           ctx.author,
            "team":           _get_user_team(ctx.author),
            "action_type":    ActionType.DEFEND,
            "was_successful": False,
            "was_critical":   None,
            "items_dropped":  "",
            "damage":         None,
            "time_set":       timestamp,
        }

        if not _is_action_successful(ctx.author, timestamp):
            emote = random.choice(["¯\\_(ツ)_/¯", "(╯°□°）╯︵ ┻━┻"])
            await ctx.send(f"<@{ctx.author.id}> defence failed! {emote}")
            Storage.add_pom_war_action(**action)
            return

        action["was_successful"] = True
        await ctx.message.add_reaction(Reactions.SHIELD)

        defends = _load_actions_directories(Locations.DEFENDS_DIR, type_=Defend)
        weights = [defend.weight for defend in defends]
        defend, = random.choices(defends, weights=weights)

        Storage.add_pom_war_action(**action)

        await send_embed_message(
            None,
            title="You have used Defend against {team}!".format(
                team=f"{(~_get_user_team(ctx.author)).value}s",
            ),
            description=defend.get_message(ctx.author),
            colour=Pomwars.DEFEND_COLOUR,
            icon_url=None,
            _func=partial(ctx.channel.send, content=ctx.author.mention),
        )

class PomwarsEventListeners(Cog):
    """Handle global events for the bot."""
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        """Cog startup procedure."""
        for guild in self.bot.guilds:
            for channel in guild.channels:
                if channel.name == Pomwars.JOIN_CHANNEL_NAME:
                    State.SCOREBOARD_CHANNELS.append(channel)

        State.score = Scoreboard(self.bot, State.SCOREBOARD_CHANNELS)

        full_channels, restricted_channels = await State.score.update_msg()

        for channel in full_channels:
            _log.error("Join channel '%s' on '%s' is not empty",
                channel.name, channel.guild.name)

        for channel in restricted_channels:
            _log.error("Join channel '%s' on '%s' is not messagable (Missing Access)",
                channel.name, channel.guild.name)


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
    bot.add_cog(PomwarsEventListeners(bot))
    bot.add_cog(PomWarsAdminCommands(bot))
