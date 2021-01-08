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
        # "pombot.cogs.user_commands",
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

    # pylint: disable=line-too-long
    class IconUrls:
        """Locations of embeddable emojis."""
        KNIGHT = "https://cdn.discordapp.com/attachments/758012800789381331/794257081455869952/if_Knight_2913116_1.png"
        VIKING = "https://cdn.discordapp.com/attachments/758012800789381331/794257094454149130/if_Viking_2913107_1.png"
        AXE = "https://cdn.discordapp.com/attachments/784284292506189845/793860961860583485/david-axe.png"
        SHIELD = "https://cdn.discordapp.com/attachments/791201687410835497/794634532145725440/image0.png"
        SWORD = "https://cdn.discordapp.com/attachments/791201687410835497/794620213374877696/image0.png"
    # pylint: enable=line-too-long

    HEAVY_ATTACK_LEVEL_VALIANT_ATTEMPT_CONDOLENCE_REWARDS = {
        # Level: (Min chance, Max chance)
        1:       (0.25,       0.75),
        2:       (0.30,       0.80),
        3:       (0.30,       0.80),
        4:       (0.33,       0.83),
        5:       (0.37,       0.87),
    }
    HEAVY_PITY_INCREMENT = 0.10

    DEFEND_LEVEL_MULTIPLIERS = {1: 0.02, 2: 0.03, 3: 0.04, 4: 0.05, 5: 0.07}
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
    ABACUS = "🧮"
    BOOM = "💥"
    CHECKMARK = "✅"
    CROSSED_SWORDS= "⚔"
    ERROR = "🐛"
    FALLEN_LEAF = "🍂"
    LEAVES = "🍃"
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
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")


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
