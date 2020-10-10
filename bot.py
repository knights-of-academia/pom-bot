import logging
from typing import Any

from discord.ext import commands as discord_commands
from discord.ext.commands import Context
from discord.message import Message

from pombot.commands.howmany import howmany_handler
from pombot.commands.newleaf import newleaf_handler
from pombot.commands.pom import pom_handler
from pombot.commands.poms import poms_handler
from pombot.commands.reset import reset_handler
from pombot.commands.start_event import start_event_handler
from pombot.commands.total import total_handler
from pombot.commands.undo import undo_handler
from pombot.config import Secrets
from pombot.events.on_command_error_handler import on_command_error_handler
from pombot.events.on_message_handler import on_message_handler
from pombot.events.on_ready_handler import on_ready_handler

bot = discord_commands.Bot(command_prefix='!', case_insensitive=True)

_log = logging.getLogger(__name__)


@bot.command()
async def pom(ctx: Context, *, description: str = None):
    """Adds a new pom, if the first word in the description is a number
    (1-10), multiple poms will be added with the given description.
    """
    await pom_handler(ctx, description=description)


@bot.command()
async def poms(ctx: Context):
    """See details for your tracked poms and the current session."""
    await poms_handler(ctx)


@bot.command()
async def howmany(ctx, *, description: str = None):
    """List your poms with a given description."""
    await howmany_handler(ctx, description=description)


@bot.command()
async def newleaf(ctx: Context):
    """Turn over a new leaf and hide the details of your previously tracked
    poms. Starts a new session.
    """
    await newleaf_handler(ctx)


@bot.command()
async def undo(ctx, *, description: str = None):
    """Undo/remove your x latest poms. If no number is specified, only the
    newest pom will be undone.
    """
    await undo_handler(ctx, description=description)


@bot.command()
async def reset(ctx: Context):
    """Permanently deletes all your poms. WARNING: There's no undoing this!"""
    await reset_handler(ctx)


@bot.command()
@discord_commands.has_any_role('Guardian', 'Helper')
async def total(ctx: Context):
    """List total amount of poms."""
    await total_handler(ctx)


@bot.command()
@discord_commands.has_any_role('Guardian', 'Helper')
async def start(ctx, event_name, event_goal, start_month, start_day, end_month, end_day):
    """A command that allows Helpers or Guardians to create community pom
    events!
    """
    await start_event_handler(ctx, event_name, event_goal, start_month, start_day, end_month, end_day)


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


if __name__ == "__main__":
    # Set log level asap to record discord.py's messages.
    logging.basicConfig(level=logging.INFO)

    bot.run(Secrets.TOKEN)
