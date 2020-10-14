import os

import dotenv

dotenv.load_dotenv()


def _str2bool(value: str) -> bool:
    """Coerce a string to a bool based on its value."""
    return value.lower() in {"yes", "y", "1", "true", "t"}


class Config:
    """Bot instance configuration."""
    # Bot
    PREFIX = "!"
    POM_TRACK_LIMIT = 10
    DESCRIPTION_LIMIT = 30
    MULTILINE_DESCRIPTION_DISABLED = True

    # Embeds
    EMBED_COLOUR = 0xff6347
    EMBED_IMAGE_URL = "https://i.imgur.com/qRoH5B5.png"

    # Extensions
    EXTENSIONS = [
        "pombot.cogs.usercommands",
        "pombot.cogs.admincommands",
        "pombot.cogs.eventlisteners",
    ]

    # Logging
    LOGFILE = "./errors.txt"

    # MySQL
    POMS_TABLE = "poms"
    EVENTS_TABLE = "events"

    # Restrictions
    POM_CHANNEL_NAMES = [
        channel.lstrip("#")
        for channel in os.getenv("POM_CHANNEL_NAMES", "botspam").split(",")
    ]


class Debug:
    """Debugging options."""
    RESPOND_TO_DM = _str2bool(os.getenv("RESPOND_TO_DM", "no"))
    DROP_TABLES_ON_RESTART = _str2bool(os.getenv("DROP_TABLES_ON_RESTART", "no"))


class Reactions:
    """Static reaction emojis."""
    ABACUS = "🧮"
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
