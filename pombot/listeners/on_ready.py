import asyncio
import logging
import textwrap

from discord.ext.commands import Bot

from pombot.state import State
from pombot.config import Config, Debug, Secrets
from pombot.lib.storage import Storage

_log = logging.getLogger(__name__)


async def handle_on_ready(bot: Bot):
    """Startup procedure after bot has logged into Discord."""
    _log.info("MYSQL_DATABASE: %s", Secrets.MYSQL_DATABASE)

    State.event_loop = asyncio.get_event_loop()

    active_channels = ", ".join(f"#{channel}"
                                for channel in Config.POM_CHANNEL_NAMES)

    _log.info("POM_CHANNEL_NAMES: %s", active_channels or "ALL CHANNELS")

    debug_options_enabled = ", ".join([k for k, v in vars(Debug).items() if v is True])
    if debug_options_enabled:
        debug_enabled_message = textwrap.dedent(f"""\
            ************************************************************
            DEBUG OPTIONS ENABLED: {debug_options_enabled}
            ************************************************************\
        """)

        for line in debug_enabled_message.split("\n"):
            _log.info(line)

    await Storage.create_tables_if_not_exists()

    if Debug.DROP_TABLES_ON_RESTART:
        if not __debug__:
            msg = ("This bot is unwilling to drop tables in production. "
                    "Either review your configuration or run with "
                    "development settings (use `make dev`).")

            await bot.close()
            raise RuntimeError(msg)

        await Storage.delete_all_rows_from_all_tables()

    _log.info("READY ON DISCORD AS: %s", bot.user)
