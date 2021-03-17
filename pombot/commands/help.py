from typing import Optional, Tuple

from discord.ext.commands import Context
from discord.ext.commands.errors import MissingAnyRole, NoPrivateMessage

from pombot.config import Config, Reactions
from pombot.lib.messages import send_embed_message
from pombot.lib.tiny_tools import normalize_newlines


def _get_help_for_all_commands(ctx: Context) -> Tuple[Optional[str],
                                                      Optional[str]]:
    """Get help information for all commands, grouped by extension.

    @param ctx Message context.
    @return Tuple of (Response string, Intended footer).
    """
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

    response = "```{}```".format("\n".join(response_lines))
    footer = "Type a command to get more information! (e.g. !help pom)"

    return response, footer


def _get_help_for_command(
    ctx: Context,
    *requested_commands: Tuple[str],
) -> Tuple[Optional[str], Optional[str]]:
    """Get a specific command(s) help information.

    @param ctx Message context.
    @param command The command to lookup.
    @return Tuple of (Response string, Intended footer).
    """
    requested_commands = set(c.casefold() for c in requested_commands)
    existing_commands = set(c.name.casefold() for c in ctx.bot.commands)
    names_and_helps = []

    if command_names_found := requested_commands & existing_commands:
        for command_name_found in command_names_found:
            checks = next(c.checks for c in ctx.bot.commands
                          if c.name == command_name_found)

            try:
                for func in checks:
                    func(ctx)
            except NoPrivateMessage:
                return (None, None)
            except MissingAnyRole:
                continue

            names_and_helps += [(cmd.name, normalize_newlines(cmd.help))
                                for cmd in ctx.bot.commands
                                if cmd.name == command_name_found]

    if not names_and_helps:
        return "I don't know {that} command{s}, sorry.".format(
            that="that" if len(requested_commands) == 1 else "those",
            s="" if len(requested_commands) == 1 else "s",
        ), None

    response = "".join("```\n{}: {}```".format(k, v) for k, v in names_and_helps)

    if unknowns := requested_commands - existing_commands:
        footer = "I can't help you with {} though.".format(", ".join(sorted(unknowns)))

        if (last_comma_index := footer.rfind(",")) > 0:
            footer = " ".join((footer[:last_comma_index], "or",
                               footer[last_comma_index + 2:]))
    else:
        footer = "To see this info in the channel, type: {}".format(
            " ".join((f"{ctx.bot.command_prefix}{ctx.invoked_with}.show", *requested_commands))
        )

    return response, footer


async def do_help(ctx: Context, *args):
    """Show this help message.

    Show a specific command by specifying it, for exmaple:
    !help pom
    """
    response, footer = (_get_help_for_command(ctx, *args)
                        if args else _get_help_for_all_commands(ctx))

    if response is None:
        return

    is_public_command = ctx.invoked_with in Config.PUBLIC_HELP_ALIASES

    if is_public_command:
        if args:
            # Footer would look a little awkward here, so just remove it.
            footer = None
    else:
        await ctx.message.add_reaction(Reactions.CHECKMARK)

    await send_embed_message(
        None,
        title=f"{ctx.bot.user.display_name}'s Help Info",
        description=response,
        footer=footer,
        _func=ctx.reply if is_public_command else ctx.author.send,
    )
