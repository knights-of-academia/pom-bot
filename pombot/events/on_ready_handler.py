import logging

from discord.ext.commands.bot import Bot

from pombot.config import Config, Secrets

_log = logging.getLogger(__name__)


def on_ready_handler(bot: Bot):
    """Synchronously handle the on_ready event from Discord."""
    _log.info("LOADED POM-BOT CONFIGURATION")
    _log.info("MYSQL_DATABASE: %s", Secrets.MYSQL_DATABASE)
    _log.info("POM_CHANNEL_NAMES: %s",
              ", ".join(f"#{channel}" for channel in Config.POM_CHANNEL_NAMES))

    _log.info("%s is ready on Discord", bot.user)
