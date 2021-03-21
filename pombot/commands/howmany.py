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


# FIXME
# async def do_howmany(ctx: Context, description: str):
#     """Count your poms with a given description."""
#     if description is None:
#         await ctx.message.add_reaction(Reactions.WARNING)
#         await ctx.send("You must specify a description to search for.")
#         return

#     # Tech debt: `description` could be added to the SQL query for a smaller
#     # network response.
#     poms = await Storage.get_poms(user=ctx.author)
#     matching_poms = [pom for pom in poms if pom.descript == description]

#     if not matching_poms:
#         await ctx.message.add_reaction(Reactions.WARNING)
#         await ctx.send("You have no tracked poms with that description.")
#         return

#     await ctx.message.add_reaction(Reactions.ABACUS)
#     await ctx.send('You have {num_poms} *"{description}"* pom{s}.'.format(
#         num_poms=len(matching_poms),
#         description=description,
#         s="" if len(matching_poms) == 1 else "s",
#     ))
