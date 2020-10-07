import mysql.connector
from discord.ext.commands import Context

from pombot.config import Reactions, Secrets
from pombot.storage import PomSql


async def howmany_handler(ctx: Context, *, description: str = None):
    """Report to the user an overview of ongoing poms."""
    db = mysql.connector.connect(
        host=Secrets.MYSQL_HOST,
        user=Secrets.MYSQL_USER,
        database=Secrets.MYSQL_DATABASE,
        password=Secrets.MYSQL_PASSWORD,
    )

    cursor = db.cursor(buffered=True)

    if description is None:
        await ctx.message.add_reaction(Reactions.WARNING)
        await ctx.send("You must specify a description to search for.")
        cursor.close()
        db.close()
        return

    # Fetch all poms for user based on their Discord ID
    cursor.execute(PomSql.SELECT_ALL_POMS_WITH_DESCRIPT,
                   (ctx.message.author.id, description))
    own_poms = cursor.fetchall()

    # If the user has no tracked poms
    if len(own_poms) == 0 or own_poms is None:  # FIXME: len(None) will raise.
        await ctx.message.add_reaction(Reactions.WARNING)
        await ctx.send("You have no tracked poms with that description.")
        cursor.close()
        db.close()
        return

    await ctx.message.add_reaction(Reactions.ABACUS)
    await ctx.send('You have {num_poms} *"{description}"* pom{s}.'.format(
        num_poms=len(own_poms),
        s="" if len(own_poms) == 1 else "s",
        description=description,
    ))

    cursor.close()
    db.close()
