import textwrap

from discord.ext.commands import Context

from pombot.config import Reactions


async def do_newleaf(ctx: Context):
    """Deprecated command.

    This command is disabled and will be removed soon. See `!help bank`
    instead.
    """
    await ctx.reply(textwrap.dedent("""\
        This command has been disabled. See `!help bank` instead.
    """))
    await ctx.message.add_reaction(Reactions.ROBOT)


# FIXME
# async def do_newleaf(ctx: Context):
#     """Turn over a new leaf.

#     Hide the details of your previously tracked poms and start a new session.
#     """
#     await Storage.clear_user_session_poms(ctx.author)

#     await ctx.send("A new session will be started when you track your "
#                     f"next pom, <@!{ctx.author.id}>")
#     await ctx.message.add_reaction(Reactions.LEAVES)
