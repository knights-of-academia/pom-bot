import textwrap

from discord.ext.commands.context import Context

from pombot.config import Reactions
from pombot.lib.storage import Storage


async def do_remove_event(ctx: Context, *args):
    """Remove an existing event.

    This is an admin-only command.
    """
    if not args:
        cmd = ctx.prefix + ctx.invoked_with

        await ctx.author.send(textwrap.dedent(f"""
            Remove an event.
            ```text
            Usage: {cmd} <name>
            ```
        """))

        return

    name = " ".join(args).strip()
    await Storage.delete_event(name)
    await ctx.message.add_reaction(Reactions.CHECKMARK)
