import logging

from discord.ext import commands as discord_commands

from pombot.config import Config, Secrets

_log = logging.getLogger(__name__)
bot = discord_commands.Bot(command_prefix=Config.PREFIX, case_insensitive=True)


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
