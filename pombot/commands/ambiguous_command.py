from discord.ext.commands import Context

from pombot.config import Reactions
from pombot.lib.tiny_tools import PolyStr


async def do_ambiguous_command(ctx: Context, *_):
    """Specified command is ambiguous."""
    matches = []
    base_command = next(
        cmd for cmd in ctx.bot.commands
        if cmd.name == ctx.invoked_with[:ctx.invoked_with.index(".")])

    for possible_match in (possible_matches := [
            a for a in base_command.aliases if a.startswith(ctx.invoked_with)]):
        if len([m for m in possible_matches if m.startswith(possible_match)]) > 1:
            continue

        matches += [possible_match]

    await ctx.reply(PolyStr("`{}` is ambiguous. You might have meant {}") \
        .format(ctx.invoked_with, ", ".join(f"`{m}`" for m in matches)) \
        .replace_final_occurence(", ", "or"))
    await ctx.message.add_reaction(Reactions.ROBOT)
