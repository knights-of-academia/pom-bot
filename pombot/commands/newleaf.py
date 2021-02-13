from discord.ext.commands import Context

from pombot.config import Reactions
from pombot.lib.storage import Storage


async def do_newleaf(ctx: Context):
    """Set all of a user's poms to not be in their current session."""
    await Storage.clear_user_session_poms(ctx.author)

    await ctx.send("A new session will be started when you track your "
                    f"next pom, <@!{ctx.author.id}>")
    await ctx.message.add_reaction(Reactions.LEAVES)
