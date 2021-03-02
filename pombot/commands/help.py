from typing import Optional, Tuple

from discord.ext.commands import Context
from discord.ext.commands.errors import MissingAnyRole, NoPrivateMessage

from pombot.config import Reactions
from pombot.lib.messages import send_embed_message


def _get_help_for_all_commands(ctx: Context) -> Tuple[Optional[str],
                                                      Optional[str]]:
    """Return a response and footer listing all enabled commands."""
    groups = {}

    for command in ctx.bot.commands:
        if command.hidden:
            continue

        try:
            for func in command.checks:
                func(ctx)
        except NoPrivateMessage:
            return (None, None)
        except MissingAnyRole:
            continue

        try:
            groups[command.extension] |= {command.name: command.short_doc}
        except KeyError:
            groups[command.extension] = {command.name: command.short_doc}

    response_lines = []
    offset = " " * 2

    for group in sorted(groups):
        response_lines.append(f"\n{group} commands:".title().replace("_", " "))
        response_lines.extend(f"{offset}{cmd}: {groups[group][cmd]}"
                              for cmd in sorted(groups[group]))

    return ("```{}```".format("\n".join(response_lines)),
            "Get a command's usage by specifying it!")


def _get_help_for_command(ctx: Context, command: str) -> Tuple[Optional[str],
                                                               Optional[str]]:
    return (f"Looking up {command}, hang on...", None)


async def do_help(ctx: Context, *args):
    """Show this message."""
    try:
        response, footer = _get_help_for_command(ctx, args[0])
    except IndexError:
        response, footer = _get_help_for_all_commands(ctx)

    if response is None:
        return

    await send_embed_message(
        ctx,
        title=f"{ctx.bot.user.display_name}'s Help Info",
        description=response,
        footer=footer,
    )
    await ctx.message.add_reaction(Reactions.CHECKMARK)
