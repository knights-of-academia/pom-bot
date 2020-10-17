import logging

from discord.ext.commands import Bot
from discord.message import Message

from pombot.config import Config, Secrets
from pombot.lib.event_handlers import on_message_handler

_log = logging.getLogger(__name__)
bot = Bot(command_prefix=Config.PREFIX, case_insensitive=True)


@bot.event
async def on_message(message: Message):
    """Global on_message handler."""
    await on_message_handler(bot, message)


def main():
    """Load cogs and start bot."""
    # Set log level asap to record discord.py messages.
    logging.basicConfig(level=logging.INFO)

    for extension in Config.EXTENSIONS:
        _log.info("Loading extension: %s", extension)
        bot.load_extension(extension)

    bot.run(Secrets.TOKEN)


if __name__ == "__main__":
    main()
