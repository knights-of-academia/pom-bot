import logging
import textwrap

import mysql.connector
from discord.ext.commands.bot import Bot

from pombot.config import Config, Debug, Secrets
from pombot.storage import EventSql, PomSql

_log = logging.getLogger(__name__)


def _setup_tables():
    tables = [
        {"name": Config.POMS_TABLE, "query": PomSql.CREATE_TABLE},
        {"name": Config.EVENTS_TABLE, "query": EventSql.CREATE_TABLE},
    ]

    db = mysql.connector.connect(
        host=Secrets.MYSQL_HOST,
        user=Secrets.MYSQL_USER,
        database=Secrets.MYSQL_DATABASE,
        password=Secrets.MYSQL_PASSWORD,
    )
    cursor = db.cursor()

    for query in (table["query"] for table in tables):
        cursor.execute(query)

    if Debug.DROP_TABLES_ON_RESTART:
        _log.info("Deleting tables... ")

        for table_name in (table["name"] for table in tables):
            cursor.execute(f"DELETE FROM {table_name};")

        _log.info("Tables deleted.")
        db.commit()

    cursor.close()
    db.close()


def on_ready_handler(bot: Bot):
    """Synchronously handle the on_ready event from Discord."""
    _log.info("LOADED POM-BOT CONFIGURATION")
    _log.info("MYSQL_DATABASE: %s", Secrets.MYSQL_DATABASE)
    _log.info("POM_CHANNEL_NAMES: %s",
              ", ".join(f"#{channel}" for channel in Config.POM_CHANNEL_NAMES))

    debug_options_enabled = ", ".join([k for k, v in vars(Debug).items() if isinstance(v, bool)])
    if debug_options_enabled:
        debug_enabled_message = textwrap.dedent(f"""
            ************************************************************
            DEBUG OPTIONS ENABLED: {debug_options_enabled}
            ************************************************************
        """)

        for line in debug_enabled_message.split("\n"):
            _log.info(line)

    _setup_tables()

    _log.info("%s is ready on Discord", bot.user)
