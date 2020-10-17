import logging

from discord.ext import commands as discord_commands
from discord.message import Message

from pombot.config import Config, Secrets

_log = logging.getLogger(__name__)
bot = discord_commands.Bot(command_prefix=Config.PREFIX, case_insensitive=True)


@bot.event
async def on_message(message: Message):
    """Global message handler to remove possible spaces after the prefix.

    This would normally be achieved by using a callable prefix, but the
    Discord.py API does not support the use of spaces after symbols, only
    alphanumeric characters. This is a workaround.
    """
    if message.content.startswith(Config.PREFIX + " "):
        message.content = "".join(message.content.split(" ", 1))

    await bot.process_commands(message)


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
