from discord.ext.commands import Context

from pombot.config import Reactions
from pombot.lib.storage import Storage


async def do_howmany(ctx: Context, description: str):
    """Send the user a count of the number of their poms matching a
    description.
    """
    if description is None:
        await ctx.message.add_reaction(Reactions.WARNING)
        await ctx.send("You must specify a description to search for.")
        return

    poms = await Storage.get_poms(user=ctx.author)
    matching_poms = [pom for pom in poms if pom.descript == description]

    if not matching_poms:
        await ctx.message.add_reaction(Reactions.WARNING)
        await ctx.send("You have no tracked poms with that description.")
        return

    await ctx.message.add_reaction(Reactions.ABACUS)
    await ctx.send('You have {num_poms} *"{description}"* pom{s}.'.format(
        num_poms=len(matching_poms),
        description=description,
        s="" if len(matching_poms) == 1 else "s",
    ))
