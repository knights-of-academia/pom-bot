from discord.ext.commands import Context

from pombot.config import Reactions
from pombot.lib.storage import Storage


async def do_reset(ctx: Context):
    """Delete all of a user's poms from storage."""
    await Storage.delete_poms(user=ctx.author)
    await ctx.message.add_reaction(Reactions.WASTEBASKET)
