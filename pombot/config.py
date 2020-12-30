import os
from typing import Any

import dotenv

# This file consists of memoized objects with run-time static constants. There
# should be no need for public methods on any class.
# pylint: disable=too-few-public-methods

dotenv.load_dotenv(override=True)


def _str2bool(value: str) -> bool:
    """Coerce a string to a bool based on its value."""
    return value.casefold() in {"yes", "y", "1", "true", "t"}

def _positive_int(value: Any) -> int:
    """Return the provided value if it is a positive whole number. Raise
    ValueError otherwise.
    """
    if (intval := int(value)) < 0:
        raise ValueError(f"Expected a positive integer, got {value}")

    return intval


class Config:
    """Bot instance configuration."""
    # Bot
    MINIMUM_PYTHON_VERSION = (3, 9, 0)
    PREFIX = "!"
    POM_TRACK_LIMIT = 10
    DESCRIPTION_LIMIT = 30
    MULTILINE_DESCRIPTION_DISABLED = True

    # Embeds
    EMBED_COLOUR = 0xff6347
    EMBED_IMAGE_URL = "https://i.imgur.com/qRoH5B5.png"

    # Errors
    ERRORS_CHANNEL_NAME = os.getenv("ERRORS_CHANNEL_NAME")

    # Extensions
    EXTENSIONS = [
        "pombot.cogs.event_listeners",
        "pombot.cogs.user_commands",
        "pombot.cogs.admin_commands",
    ]

    # Logging
    LOGFILE = "./errors.txt"

    # MySQL
    POMS_TABLE = "poms"
    EVENTS_TABLE = "events"
    USERS_TABLE = "users"
    ACTIONS_TABLE = "actions"
    MYSQL_CONNECTION_POOL_SIZE = _positive_int(
        os.getenv("MYSQL_CONNECTION_POOL_SIZE"))

    # Restrictions
    POM_CHANNEL_NAMES = [
        channel.lstrip("#")
        for channel in os.getenv("POM_CHANNEL_NAMES").split(",")
    ]


class Debug:
    """Debugging options."""
    RESPOND_TO_DM = _str2bool(os.getenv("RESPOND_TO_DM", "no"))
    DROP_TABLES_ON_RESTART = _str2bool(os.getenv("DROP_TABLES_ON_RESTART", "no"))


class Pomwars:
    """Configuration for Pom Wars."""
    LOAD_ON_STARTUP = _str2bool(os.getenv("LOAD_ON_STARTUP", "no"))
    KNIGHT_ROLE = os.getenv("KNIGHT_ROLE")
    VIKING_ROLE = os.getenv("VIKING_ROLE")
    BASE_DAMAGE_FOR_NORMAL_ATTACKS = _positive_int(os.getenv("BASE_DAMAGE_FOR_NORMAL_ATTACKS"))
    BASE_DAMAGE_FOR_HEAVY_ATTACKS = _positive_int(os.getenv("BASE_DAMAGE_FOR_HEAVY_ATTACKS"))
    BASE_CHANCE_FOR_CRITICAL = 0.20
    SUCCESSFUL_ATTACK_EMOTE = os.getenv("SUCCESSFUL_ATTACK_EMOTE")

    JOIN_CHANNEL_NAME = os.getenv("JOIN_CHANNEL_NAME").lstrip("#")
    KNIGHT_ONLY_GUILDS = [
        int(guild.strip()) if guild.strip() else 0
        for guild in os.getenv("KNIGHT_ONLY_GUILDS").split(",")
    ]
    VIKING_ONLY_GUILDS = [
        int(guild.strip()) if guild.strip() else 0
        for guild in os.getenv("VIKING_ONLY_GUILDS").split(",")
    ]


class Reactions:
    """Static reaction emojis."""
    ABACUS = "🧮"
    BOOM = "💥"
    CHECKMARK = "✅"
    ERROR = "🐛"
    FALLEN_LEAF = "🍂"
    LEAVES = "🍃"
    ROBOT = "🤖"
    TOMATO = "🍅"
    UNDO = "↩"
    WARNING = "⚠️"
    WASTEBASKET = "🗑️"

    # Reactions related to pom war events
    WAR_JOIN_REACTION = "▶️"
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
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
