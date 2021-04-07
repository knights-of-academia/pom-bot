import textwrap

from discord.ext.commands import Context

from pombot.config import Reactions


async def do_newleaf(ctx: Context):
    """Deprecated command; see !bank.

    This command is disabled and will be removed soon. See `!help bank`
    instead.
    """
    await ctx.reply(textwrap.dedent("""\
        This command has been disabled. See `!help bank` instead.
    """))
    await ctx.message.add_reaction(Reactions.ROBOT)
