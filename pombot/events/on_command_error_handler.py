import logging
import random
from typing import Any

from discord.ext import commands as discord_commands
from discord.ext.commands import Context

from pombot.config import Reactions

_log = logging.getLogger(__name__)


async def on_command_error_handler(ctx: Context, error: Any):
    """Handle user errors and uncaught exceptions."""
    if isinstance(error, discord_commands.errors.CheckFailure):
        message, *_ = random.choices([
            "You do not have access to this command.",
            "Sorry, that command is out-of-order.",
            "!!! ACCESS DENIED !!! \\**whale noises\\**",
            "Wir konnten die Smaragde nicht finden!",
            "Do you smell that?",
            "\\**(Windows XP startup sound)\\**",
            "This is not the command you're looking for. \\**waves hand\\**",
            "*noop*",
        ])

        await ctx.message.add_reaction(Reactions.WARNING)
        await ctx.send(message)
        return

    for message in error.args:
        _log.error(
            'error: user %s (%s) running "%s" hit: %s',
            ctx.author.display_name,
            ctx.author.name + "#" + ctx.author.discriminator,
            ctx.message.content,
            message,
        )

    await ctx.message.add_reaction(Reactions.ERROR)
