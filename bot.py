import logging
import sys
from functools import partial

from discord.message import Message
from discord.ext.commands import Bot

from pombot import commands
from pombot import handlers
from pombot.config import Config, Pomwars, Secrets
from pombot.lib.tiny_tools import BotCommand

_log = logging.getLogger(__name__)
bot = Bot(command_prefix=Config.PREFIX, case_insensitive=True)


@bot.event
async def on_message(message: Message):
    """Global on_message handler.

    This is a special event.

    The handler for the "on_message" event must be a bot-decorated function
    due to the special property that Discord.py applies wherein the default
    handler for "on_message" is applied, even when `bot.add_listener` is
    called before the default handler is created. This means that without
    this special, bot-decorated handler, the default handler would still be
    applied, causing the bot to bypass all the restrictions we lay out in
    `handlers.on_message`.
    """
    await handlers.on_message(bot, message)


def main():
    """Load cogs and start bot."""
    # Set log level asap to record discord.py messages.
    logging.basicConfig(level=logging.INFO)

    if sys.version_info < Config.MINIMUM_PYTHON_VERSION:
        raise RuntimeError("Please update Python to at least {}".format(
            ".".join(str(_) for _ in Config.MINIMUM_PYTHON_VERSION)))

    # Discord.py breaks debuggers and logging when loading event handlers in
    # the `setup` function of an extension, so load them here.
    for event, handler in [
        ("on_ready",         partial(handlers.on_ready, bot)),
        ("on_command_error", handlers.on_command_error),
    ]:
        bot.add_listener(handler, event)

    if Pomwars.LOAD_POM_WARS:
        for event, handler in [
            ("on_ready", partial(handlers.pom_wars.on_ready, bot)),
            ("on_raw_reaction_add", partial(handlers.pom_wars.on_raw_reaction_add, bot)),
        ]:
            bot.add_listener(handler, event)

        Config.EXTENSIONS.append("pombot.extensions.pom_wars")

    for extension in Config.EXTENSIONS:
        _log.info("Loading extension: %s", extension)
        bot.load_extension(extension)

    # Replace the default help command which marks every command as
    # "Uncategorized" and does no extension separation.
    bot.remove_command("help")
    bot.add_command(BotCommand(commands.do_help, name="help"))

    bot.run(Secrets.TOKEN)


if __name__ == "__main__":
    main()
