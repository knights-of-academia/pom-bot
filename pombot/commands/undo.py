from discord.ext.commands import Context

from pombot.lib.storage import Storage
from pombot.config import Reactions


async def do_undo(ctx: Context):
    """Undo/remove your latest pom(s)."""
    try:
        last_pom, = await Storage.get_poms(user=ctx.author, limit=1)
    except ValueError:
        await ctx.send("You don't have any poms to undo!")
        await ctx.message.add_reaction(Reactions.ROBOT)
        return

    num_removed = await Storage.delete_poms(user=ctx.author,
                                            time_set=last_pom.time_set)

    msg = "Removed {count} {description} pom{s}.".format(
        count=num_removed,
        description=last_pom.descript or "*undesignated*",
        s="" if num_removed == 1 else "s"
    )

    await ctx.send(msg)
    await ctx.message.add_reaction(Reactions.UNDO)
