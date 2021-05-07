import os
import sys
from datetime import timedelta

import dotenv

from pombot.lib.tiny_tools import (classproperty, explode_after_char,
                                   positive_int, str2bool)

dotenv.load_dotenv(override=True)


class Config:
    """Bot instance configuration."""
    # Aliases
    PUBLIC_POMS_ALIASES = explode_after_char("poms.show", ".")
    RENAME_POMS_IN_SESSION = explode_after_char("poms.rename", ".")
    RESET_POMS_IN_SESSION = explode_after_char("poms.reset", ".")

    PUBLIC_HELP_ALIASES = explode_after_char("help.show", ".")

    RENAME_POMS_IN_BANK = explode_after_char("bank.rename", ".")
    RESET_POMS_IN_BANK = explode_after_char("bank.reset", ".")

    # Bot
    MINIMUM_PYTHON_VERSION = (3, 9, 0)
    PREFIX = "!"
    POM_TRACK_LIMIT = 10
    DESCRIPTION_LIMIT = 30
    POM_LENGTH = timedelta(minutes=25)

    # Embeds
    EMBED_COLOUR = 0xff6347

    # Errors
    ERRORS_CHANNEL_NAME = os.getenv("ERRORS_CHANNEL_NAME")

    # Extensions
    EXTENSIONS = [
        "pombot.extensions.general",
    ]

    # Logging
    LOGFILE = "./errors.txt"

    # MySQL
    LIVE_DATABASE = os.getenv("MYSQL_DATABASE")
    POMS_TABLE = "poms"
    EVENTS_TABLE = "events"
    USERS_TABLE = "users"
    ACTIONS_TABLE = "actions"

    # Restrictions
    ADMIN_ROLES = os.getenv("ADMIN_ROLES").split(",")
    # Tech debt: Pom Wars channels should be configured elsewhere.
    POM_CHANNEL_NAMES = [
        channel.strip().lstrip("#")
        for channel in os.getenv("POM_CHANNEL_NAMES").split(",")
    ]

    # Testing
    TEST_DATABASE = os.getenv("TEST_DATABASE")


class Debug:
    """Debugging options."""
    RESPOND_TO_DM = str2bool(os.getenv("RESPOND_TO_DM", "no"))
    DROP_TABLES_ON_RESTART = str2bool(os.getenv("DROP_TABLES_ON_RESTART", "no"))
    BENCHMARK_POMWAR_ATTACK = str2bool(os.getenv("BENCHMARK_POMWAR_ATTACK", "no"))
    POMS_COMMAND_IS_PUBLIC = str2bool(os.getenv("POMS_COMMAND_IS_PUBLIC", "no"))

    @classmethod
    def disable(cls) -> None:
        """Override settings from environment variables and set all boolean
        debug options to false. Useful for unit tests.
        """
        for attr, _ in filter(lambda p: isinstance(p[1], bool),
                              ((p, getattr(cls, p)) for p in dir(cls))):
            setattr(cls, attr, False)


class IconUrls:
    """Locations of Pombot's custom reactions and icons."""
    # The Pomato
    POMBOMB = "https://koa-assets.s3-us-west-2.amazonaws.com/pombomb.png"

    # Actions
    ATTACK = "https://koa-assets.s3-us-west-2.amazonaws.com/attack.png"
    DEFEND = "https://koa-assets.s3-us-west-2.amazonaws.com/defend.png"
    AND_MY_AXE = "https://koa-assets.s3-us-west-2.amazonaws.com/axe.png"

    # Actors
    KNIGHT = "https://koa-assets.s3-us-west-2.amazonaws.com/knight.png"
    VIKING = "https://koa-assets.s3-us-west-2.amazonaws.com/viking.png"
    WIZARD = "https://koa-assets.s3-us-west-2.amazonaws.com/wizard.png"

    # Potions
    MANA = "https://koa-assets.s3-us-west-2.amazonaws.com/mana.png"
    HEALTH = "https://koa-assets.s3-us-west-2.amazonaws.com/health.png"
    POISON = "https://koa-assets.s3-us-west-2.amazonaws.com/poison.png"


class Pomwars:
    """Configuration for Pom Wars."""
    LOAD_POM_WARS = str2bool(os.getenv("LOAD_POM_WARS", "no"))
    KNIGHT_ROLE = os.getenv("KNIGHT_ROLE")
    VIKING_ROLE = os.getenv("VIKING_ROLE")
    BASE_DAMAGE_FOR_NORMAL_ATTACKS = positive_int(os.getenv("BASE_DAMAGE_FOR_NORMAL_ATTACKS"))
    BASE_DAMAGE_FOR_HEAVY_ATTACKS = positive_int(os.getenv("BASE_DAMAGE_FOR_HEAVY_ATTACKS"))
    BASE_CHANCE_FOR_CRITICAL = 0.20
    SUCCESSFUL_ATTACK_EMOTE = os.getenv("SUCCESSFUL_ATTACK_EMOTE")
    SUCCESSFUL_DEFEND_EMOTE = os.getenv("SUCCESSFUL_DEFEND_EMOTE")
    ACTION_COLOUR = 0xF5F5DC
    HEAVY_COLOUR = 0xFFD700
    NORMAL_COLOUR = 0xec5c5b # Normal attack
    DEFEND_COLOUR = 0x55aedd

    JOIN_CHANNEL_NAME = os.getenv("JOIN_CHANNEL_NAME").lstrip("#")
    KNIGHT_ONLY_GUILDS = [
        int(guild.strip()) if guild.strip() else 0
        for guild in os.getenv("KNIGHT_ONLY_GUILDS").split(",")
    ]
    VIKING_ONLY_GUILDS = [
        int(guild.strip()) if guild.strip() else 0
        for guild in os.getenv("VIKING_ONLY_GUILDS").split(",")
    ]

    HEAVY_ATTACK_LEVEL_VALIANT_ATTEMPT_CONDOLENCE_REWARDS = {
        # Level: (Min chance, Max chance)
        1:       (0.25,       0.75),
        2:       (0.30,       0.80),
        3:       (0.30,       0.80),
        4:       (0.33,       0.83),
        5:       (0.37,       0.87),
    }
    HEAVY_PITY_INCREMENT = 0.10
    HEAVY_QUALIFIERS = ["heavy", "hard", "sharp", "strong"]

    DEFEND_LEVEL_MULTIPLIERS = {1: 0.05, 2: 0.08, 3: 0.07, 4: 0.08, 5: 0.09}
    DEFEND_DURATION_MINUTES = 30
    MAXIMUM_TEAM_DEFENCE = 0.25

    class Emotes:
        """Emotes for use in embeds."""
        KNIGHT = "<:knights:622832507766702100>"
        VIKING = "<:vikings:705822896978919594>"
        WINNER = "<a:winner:795418467908976671>"
        ATTACK = "<:attack:794694043015446530>"
        CRITICAL = "<:criticalhit:794710983536672788>"
        DEFEND = "<:defend:794694015861260308>"


class Reactions:
    """Static reaction emojis."""
    BANK = "🏦"
    BOOM = "💥"
    CHECKMARK = "✅"
    CROSSED_SWORDS= "⚔"
    ERROR = "🐛"
    ROBOT = "🤖"
    SHIELD = "🛡"
    TOMATO = "🍅"
    UNDO = "↩"
    WARNING = "⚠️"
    WASTEBASKET = "🗑️"

    # Reactions related to pom war events
    WAR_JOIN_REACTION = "✅"  # dotenv does not read as Unicode.
    UTC_MINUS_10_TO_9 = "1️⃣"
    UTC_MINUS_8_TO_7 = "2️⃣"
    UTC_MINUS_6_TO_5 = "3️⃣"
    UTC_MINUS_4_TO_3 = "4️⃣"
    UTC_MINUS_2_TO_1 = "5️⃣"
    UTC_PLUS_1_TO_2 = "6️⃣"
    UTC_PLUS_3_TO_4 = "7️⃣"
    UTC_PLUS_5_TO_6 = "8️⃣"
    UTC_PLUS_7_TO_8 = "9️⃣"
    UTC_PLUS_9_TO_10 = "🔟"


class Secrets:
    """Passwords and server-specific configuration."""
    TOKEN = os.getenv("DISCORD_TOKEN")
    MYSQL_HOST = os.getenv("MYSQL_HOST")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

    @classproperty
    def MYSQL_DATABASE(self) -> str:  # pylint: disable=invalid-name
        """Return the database needed based on whether we're running in a
        unit test.

        This will determine if we're running inside of a unit test by looking
        for the name "unittest" in the loaded modules, which should only be
        true during unit testing. Introspection is not used because the
        indices we would need to retrieve in the call stack are likely to
        change between Python releases and runtimes.
        """
        return Config.TEST_DATABASE if "unittest" in sys.modules else Config.LIVE_DATABASE


TIMEZONES = {
    Reactions.UTC_MINUS_10_TO_9: -9,
    Reactions.UTC_MINUS_8_TO_7: -7,
    Reactions.UTC_MINUS_6_TO_5: -5,
    Reactions.UTC_MINUS_4_TO_3: -3,
    Reactions.UTC_MINUS_2_TO_1: -1,
    Reactions.UTC_PLUS_1_TO_2: +2,
    Reactions.UTC_PLUS_3_TO_4: +4,
    Reactions.UTC_PLUS_5_TO_6: +6,
    Reactions.UTC_PLUS_7_TO_8: +8,
    Reactions.UTC_PLUS_9_TO_10: +10,
}
