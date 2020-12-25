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
    KNIGHTS_ROLE = os.getenv("KNIGHTS_ROLE")
    VIKINGS_ROLE = os.getenv("VIKINGS_ROLE")
    BASE_DAMAGE_FOR_ATTACKS = _positive_int(os.getenv("BASE_DAMAGE_FOR_ATTACKS"))


class Reactions:
    """Static reaction emojis."""
    ABACUS = "🧮"
    CHECKMARK = "✅"
    ERROR = "🐛"
    FALLEN_LEAF = "🍂"
    LEAVES = "🍃"
    ROBOT = "🤖"
    TOMATO = "🍅"
    UNDO = "↩"
    WARNING = "⚠️"
    WASTEBASKET = "🗑️"


class Secrets:
    """Passwords and server-specific configuration."""
    TOKEN = os.getenv("DISCORD_TOKEN")
    MYSQL_HOST = os.getenv("MYSQL_HOST")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
