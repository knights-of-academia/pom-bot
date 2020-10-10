import mysql.connector
from discord.ext.commands import Context

from pombot.config import Reactions, Secrets
from pombot.storage import PomSql


async def howmany_handler(ctx: Context, *, description: str = None):
    """Report to the user an overview of ongoing poms matching a description.
    """
    if description is None:
        await ctx.message.add_reaction(Reactions.WARNING)
        await ctx.send("You must specify a description to search for.")
        return

    db = mysql.connector.connect(
        host=Secrets.MYSQL_HOST,
        user=Secrets.MYSQL_USER,
        database=Secrets.MYSQL_DATABASE,
        password=Secrets.MYSQL_PASSWORD,
    )
    cursor = db.cursor(buffered=True)

    cursor.execute(PomSql.SELECT_ALL_POMS_WITH_DESCRIPT,
                   (ctx.message.author.id, description))
    poms = cursor.fetchall()
    cursor.close()
    db.close()

    if not poms:
        await ctx.message.add_reaction(Reactions.WARNING)
        await ctx.send("You have no tracked poms with that description.")
        return

    await ctx.message.add_reaction(Reactions.ABACUS)
    await ctx.send('You have {num_poms} *"{description}"* pom{s}.'.format(
        num_poms=len(poms),
        description=description,
        s="" if len(poms) == 1 else "s",
    ))
