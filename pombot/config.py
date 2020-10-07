import logging
import os

import dotenv

dotenv.load_dotenv()

_log = logging.getLogger(__name__)


class Config:
    # Bot
    POM_TRACK_LIMIT = 10
    DESCRIPTION_LIMIT = 30
    MULTILINE_DESCRIPTION_DISABLED = True

    # Logging
    LOGFILE = "./errors.txt"

    # MySQL
    POMS_TABLE = "poms"
    EVENTS_TABLE = "events"

    # Restrictions
    POM_CHANNEL_NAME = os.getenv('POM_CHANNEL_NAME')


class Reactions:
    ABACUS = "🧮"
    ERROR = "🐛"
    FALLEN_LEAF = "🍂"
    LEAVES = "🍃"
    TOMATO = "🍅"
    WARNING = "⚠️"


class Secrets:
    TOKEN = os.getenv('DISCORD_TOKEN')
    MYSQL_HOST = os.getenv('MYSQL_HOST')
    MYSQL_USER = os.getenv('MYSQL_USER')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')


_log.info("LOADED POM-BOT CONFIGURATION")
_log.info("POM_CHANNEL_NAME: %s", Config.POM_CHANNEL_NAME)
_log.info("MYSQL_DATABASE: %s", Secrets.MYSQL_DATABASE)
