import logging
from typing import Any

from discord.ext import commands as discord_commands
from discord.ext.commands import Context
from discord.message import Message

from pombot.config import Config, Secrets
from pombot.events.on_command_error_handler import on_command_error_handler
from pombot.events.on_message_handler import on_message_handler
from pombot.events.on_ready_handler import on_ready_handler

_log = logging.getLogger(__name__)

bot = discord_commands.Bot(command_prefix=Config.PREFIX, case_insensitive=True)


@bot.event
async def on_ready():
    """Startup procedure after bot has logged into Discord."""
    on_ready_handler(bot)


@bot.event
async def on_command_error(ctx: Context, error: Any):
    """Alert users when using commands to which they have no access. In all
    other cases, log the error and mark it in discord.
    """
    await on_command_error_handler(ctx, error)


@bot.event
async def on_message(message: Message):
    """Limit commands to certain channels."""
    await on_message_handler(bot, message)


def main():
    """Load cogs and start bot."""
    # Set log level asap to record discord.py messages.
    logging.basicConfig(level=logging.INFO)

    extentions = [
        "pombot.cogs.usercommands",
        "pombot.cogs.admincommands",
    ]

    for extention in extentions:
        bot.load_extension(extention)

    bot.run(Secrets.TOKEN)


if __name__ == "__main__":
    main()
