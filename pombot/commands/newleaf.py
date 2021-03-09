from discord.ext.commands import Context

from pombot.config import Reactions
from pombot.lib.storage import Storage


async def do_newleaf(ctx: Context):
    """Turn over a new leaf.

    Hide the details of your previously tracked poms and start a new session.
    """
    await Storage.clear_user_session_poms(ctx.author)

    await ctx.send("A new session will be started when you track your "
                    f"next pom, <@!{ctx.author.id}>")
    await ctx.message.add_reaction(Reactions.LEAVES)
