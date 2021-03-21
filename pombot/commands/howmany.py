# Tech debt: Deprecated March, 2021
import textwrap

from discord.ext.commands import Context

from pombot.config import Reactions


async def do_howmany(ctx: Context):
    """Deprecated command; see !poms.

    This command is disabled and will be removed soon. See `!help poms`
    instead.
    """
    await ctx.reply(textwrap.dedent("""\
        This command has been disabled. See `!help poms` instead.
    """))
    await ctx.message.add_reaction(Reactions.ROBOT)
