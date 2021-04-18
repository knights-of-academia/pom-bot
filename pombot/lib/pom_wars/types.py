import json
from pathlib import Path
from string import Template

from discord.ext.commands import Bot
from discord.user import User as DiscordUser

from pombot.config import Pomwars
from pombot.data import Locations
from pombot.lib.types import User as BotUser
from pombot.lib.pom_wars.team import get_user_team
from pombot.lib.tiny_tools import normalize_newlines


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

        return base_damage * self.damage_multiplier

    @property
    def weight(self):
        """The configured base weighted-chance for this action."""
        return self.chance_for_this_action

    def get_message(self, adjusted_damage: int = None) -> str:
        """The markdown-formatted version of the message.txt from the
        action's directory, and its result, as a string.
        """
        dmg = adjusted_damage or self.damage
        dmg_str = f"{dmg:.1f}" if dmg % 1 else str(int(dmg))
        message_lines = [f"** **\n{Pomwars.Emotes.ATTACK} `{dmg_str} damage!`"]

        if self.is_critical:
            message_lines += [f"{Pomwars.Emotes.CRITICAL} `Critical attack!`"]

        action_result = "\n".join(message_lines)
        formatted_story = "*" + normalize_newlines(self._message) + "*"

        return "\n\n".join([action_result, formatted_story])

    def get_title(self, user: DiscordUser) -> str:
        """Title that includes the name of the team user attacked."""

        title = "You have used{indicator}Attack against {team}!".format(
            indicator = " Heavy " if self.is_heavy else " ",
            team=f"{(~get_user_team(user)).value}s",
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

    def get_message(self, user: BotUser) -> str:
        """The markdown-formatted version of the message.txt from the
        action's directory, and its result, as a string.
        """
        formatted_story = "*" + normalize_newlines(self._message) + "*"
        action_result = "** **\n{emt} `{dfn:.0f}% team damage reduction!`".format(
            emt=Pomwars.Emotes.DEFEND,
            dfn=100 * Pomwars.DEFEND_LEVEL_MULTIPLIERS[user.defend_level],
        )

        return "\n\n".join([action_result, formatted_story])


class Bribe:
    """Fun replies when users try and bribe the bot."""
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

    def get_message(self, user: DiscordUser, bot: Bot) -> str:
        """The markdown-formatted version of the message.txt from the
        action's directory, and its result, as a string.
        """

        story = Template(normalize_newlines(self._message))

        return story.safe_substitute(
            DISPLAY_NAME=user.display_name,
            DISCRIMINATOR=user.discriminator,
            BOTNAME=bot.user.name
        )
