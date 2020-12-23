import logging
import random
from typing import Tuple

from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.bot import Bot

from pombot.lib.pom_wars import attacks
from pombot.lib.pom_wars.attacks import AttackStrength as Strength
import os

_log = logging.getLogger(__name__)


class PomWarsCommands(commands.Cog):
    """Handlers for user-level pom commands."""
    def __init__(self, bot: Bot):
        self.bot = bot
        self._previous_attack_strength = None
        self._current_multiplier = 0.0

    @commands.command()
    async def attack(self, ctx: Context, *args: Tuple[str]):
        """Attack the opposing castle."""
        try:
            strength, *_ = args
        except ValueError:
            strength = None

        if strength is not None:
            strength = strength.casefold()

        if strength in AttackDescriptons.WEAK_ATTACKS:
            attack = attacks.fetch_random(strength=Strength.WEAK)
        elif strength in AttackDescriptons.STRONG_ATTACKS:
            attack = attacks.fetch_random(strength=Strength.STRONG)

            if "raptors" in args:
                # Partly cloudy with a chance of vicious, blood-thirsty cretin.
                you_get_raptors = random.random() * 100 // 1 < 2

                if you_get_raptors:
                    attack = attacks.fetch_one(name="raptors")
        else:
            attack = attacks.fetch_random(strength=Strength.NORMAL)

        # Happy Easter!
        if strength == "raptors" and random.random() < 0.3:
            # FIXME: verify that if the chance for raptors does not occur, then
            # a normal attack is still mounted.
            attack = attacks.fetch_random(strength=Strength.RAPTORS)

        if attack_was_successful := attack.mount():
            _log.info("successful attack")
        else:
            _log.info("failed attack")


def setup(bot: Bot):
    """Required to load extension."""
    bot.add_cog(PomWarsCommands(bot))
