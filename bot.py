import logging
import sys

from discord import RawReactionActionEvent
from discord.ext.commands import Bot
from discord.message import Message

from pombot.config import Config, Secrets
from pombot.lib.event_handlers import on_message_handler, on_raw_reaction_add_handler

_log = logging.getLogger(__name__)
bot = Bot(command_prefix=Config.PREFIX, case_insensitive=True)


@bot.event
async def on_message(message: Message):
    """Global on_message handler."""
    await on_message_handler(bot, message)

@bot.event
async def on_raw_reaction_add(payload: RawReactionActionEvent):
    """Handle reactions being added to messages."""
    await on_raw_reaction_add_handler(bot, payload)

def main():
    """Load cogs and start bot."""
    # Set log level asap to record discord.py messages.
    logging.basicConfig(level=logging.INFO)

    if sys.version_info < Config.MINIMUM_PYTHON_VERSION:
        raise RuntimeError("Please update Python to at least {}".format(
            ".".join(str(_) for _ in Config.MINIMUM_PYTHON_VERSION)))

    for extension in Config.EXTENSIONS:
        _log.info("Loading extension: %s", extension)
        bot.load_extension(extension)

    bot.run(Secrets.TOKEN)


if __name__ == "__main__":
    main()
