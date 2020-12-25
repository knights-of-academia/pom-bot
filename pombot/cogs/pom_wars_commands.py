import json
import logging
import math
import random
from pathlib import Path
from typing import List

from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.bot import Bot
from discord.user import User

from pombot.data import Locations
from pombot.lib.types import DateRange
from pombot.storage import Storage

_log = logging.getLogger(__name__)


class Attack:
    """An attack as specified by file and directory structure."""
    def __init__(self, directory: Path) -> None:
        self.name = directory.name
        self._message = (directory / Locations.MESSAGE).read_text(encoding="utf8")
        self._meta = (directory / Locations.META).read_text(encoding="utf8")


def _load_attacks(location: Path) -> List[Attack]:
    attacks = []

    for attack_dir in location.iterdir():
        if attack_dir.name.startswith("~"):
            attacks.extend(_load_attacks(attack_dir))
            continue

        attacks.append(Attack(attack_dir))

    return attacks


def _is_attack_successful(user: User, is_heavy_attack: bool) -> bool:
    # FIXME: memoize
    def _get_normal_attack_success_chance(num_poms: int):
        probabilities = {
            range(0, 6): lambda x: 1.0,
            range(6, 11): lambda x: -0.016 * math.pow(x, 2) + 0.16 * x + 0.6,
            range(11, 1000): lambda x: (1 / x),  # FIXME: help me pls :'(
        }

        for range_, function in probabilities.items():
            if num_poms in range_:
                break
        else:
            function = lambda x: 0.0

        return function(num_poms)

    # FIXME: memoize
    def _get_heavy_attack_success_chance(num_poms):
        return 1 / num_poms  # FIXME

    chance_func = (_get_heavy_attack_success_chance
                   if is_heavy_attack else _get_normal_attack_success_chance)

    # We don't need to add 1 to this because, at this point, the poms table
    # will have been updated with the actual pom.
    this_pom_number = len(Storage.get_poms(user=user))  # FIXME: get number of poms so far today.

    return random.random() <= chance_func(this_pom_number)


class PomWarsUserCommands(commands.Cog):
    """Commands used by users during a Pom War."""
    HEAVY_QUALIFIERS = ["heavy", "hard", "sharp", "strong"]

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def attack(self, ctx: Context, *args):
        """Attack the other team."""
        # FIXME: call UserCommands.pom()
        # FIXME: the rest of the args should be the "description" (sans "heavy")

        heavy_attack = args and args[0].casefold() in self.HEAVY_QUALIFIERS

        if not _is_attack_successful(ctx.author, heavy_attack):
            ctx.send("you missed")
            return

        attacks = _load_attacks(Locations.HEAVY_ATTACKS_DIR if heavy_attack
                                else Locations.NORMAL_ATTACKS_DIR)

        _log.info("selected: %s", attacks)
        ctx.send(" ".join(attack.name for attack in attacks))


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
