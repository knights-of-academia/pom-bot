import logging
import random
from typing import Any

from discord.ext.commands import Context, errors as discord_errors

from pombot.config import Config, Reactions

_log = logging.getLogger(__name__)


async def _send_to_errors_channel(ctx: Context, message: str):
    if not Config.ERRORS_CHANNEL_NAME:
        _log.info("ERRORS_CHANNEL_NAME not configured")
        return

    if ctx.guild is None:
        return

    for channel in ctx.guild.channels:
        if channel.name == Config.ERRORS_CHANNEL_NAME:
            await channel.send("```\n" + message + "```")
            break
    else:
        _log.info("ERRORS_CHANNEL_NAME not found on context guild")


async def handle_on_command_error(ctx: Context, error: Any):
    """Alert users when using commands to which they have no permission.
    In unknown cases, log the error and mark it in discord.
    """
    if isinstance(error, discord_errors.CommandNotFound):
        # Multiple bots can run on a single guild. We should not respond to
        # all commands we don't implement.
        return

    if isinstance(error, discord_errors.CheckFailure):
        message, *_ = random.choices([
            "You do not have access to this command.",
            "Sorry, that command is out-of-order.",
            "!!! ACCESS DENIED !!! \\**whale noises\\**",
            "Wir konnten die Smaragde nicht finden!",
            "Do you smell that?",
            "\\**(Windows XP startup sound)\\**",
            "This is not the command you're looking for. \\**waves hand\\**",
            "*noop*",
            "Command permenently moved to a different folder.",
            "This ~~princess~~ command is in another castle.",
            "Okay, let me get my tools.. brb",
            "(╯°□°）╯︵ ¡ƃuoɹʍ ʇuǝʍ ƃuıɥʇǝɯoS",
        ])

        await ctx.message.add_reaction(Reactions.ROBOT)
        await ctx.send(message)
        return

    for message in error.args:
        error_message = 'User {} ({}) running "{}" hit: {}'.format(
            ctx.author.display_name,
            ctx.author.name + "#" + ctx.author.discriminator,
            ctx.message.content,
            message,
        )

        _log.error("%s", error_message)
        await _send_to_errors_channel(ctx, error_message)

    await ctx.message.add_reaction(Reactions.ERROR)
