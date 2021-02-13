from discord.ext.commands import Context

from pombot.config import Reactions
from pombot.lib.storage import Storage


async def do_reset(ctx: Context):
    """Permanently deletes all of your poms. This cannot be undone."""
    await Storage.delete_poms(user=ctx.author)
    await ctx.message.add_reaction(Reactions.WASTEBASKET)
