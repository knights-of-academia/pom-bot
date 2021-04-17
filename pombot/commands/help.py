from typing import Any, Iterator, List, Optional, Tuple

from discord.ext.commands import Context
from discord.ext.commands.errors import MissingAnyRole, NoPrivateMessage

from pombot.config import Config, Reactions
from pombot.lib.messages import EmbedField, send_embed_message
from pombot.lib.tiny_tools import PolyStr, normalize_newlines


def _uniq(iterator: Iterator) -> Any:
    already_yielded = set()

    for item in iterator:
        if item in already_yielded:
            continue

        yield item
        already_yielded.add(item)


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


def _get_help_for_commands(
    ctx: Context,
    is_public: bool,
    *commands: Tuple[str],
) -> Tuple[Optional[List[EmbedField]], Optional[str]]:
    """Get a specific command(s) help information.

    @param ctx Message context.
    @param commands The commands to lookup.
    @return Tuple of (Response field list, Intended footer).
    """
    # FIXME getting help for aliases should work (maybe)
    requested_commands = {c.casefold() for c in commands}
    existing_commands = {c.name.casefold() for c in ctx.bot.commands}
    fields = []

    if command_names_found := requested_commands & existing_commands:
        for command in _uniq(commands):

            # If we simply iterate over command_names_found, then they won't
            # appear in the order requested by the user.
            if command not in command_names_found:
                continue

            checks = next(c.checks for c in ctx.bot.commands
                          if c.name == command)

            try:
                for func in checks:
                    func(ctx)
            except NoPrivateMessage:
                return (None, None)
            except MissingAnyRole:
                continue

            fields += [
                EmbedField(Config.PREFIX + cmd.name,
                           "```" + normalize_newlines(cmd.help) + "```",
                           inline=False) for cmd in ctx.bot.commands
                if cmd.name == command
            ]

    if unknowns := requested_commands - existing_commands:
        footer = PolyStr("I can't help you with {} though.") \
                    .format(", ".join(sorted(unknowns))) \
                    .replace_final_occurence(", ", "or")
    else:
        if is_public:
            footer = None
        else:
            footer = "To see this info in the channel, type: {}".format(
                " ".join((f"{ctx.bot.command_prefix}{ctx.invoked_with}.show",
                          *requested_commands)))

    return fields, footer


async def do_help(ctx: Context, *args):
    """Show this help message.

    Show a specific command by specifying it, for exmaple:
    !help pom
    """
    public_response = ctx.invoked_with in Config.PUBLIC_HELP_ALIASES
    response, fields = None, None

    if args:
        fields, footer = _get_help_for_commands(ctx, public_response, *args)

        if not fields:
            response = "I don't know {that} command{s}, sorry.".format(
                that="that" if len(args) == 1 else "those",
                s="" if len(args) == 1 else "s",
            )
            footer = None
    else:
        response, footer = _get_help_for_all_commands(ctx)

    if not any((response, fields)):
        return

    if not public_response:
        await ctx.message.add_reaction(Reactions.CHECKMARK)

    await send_embed_message(
        None,
        title=f"{ctx.bot.user.display_name}'s Help Info",
        description=response,
        fields=fields,
        footer=footer,
        _func=ctx.reply if public_response else ctx.author.send,
    )
