import mysql.connector
from discord.ext.commands import Context

from pombot.config import Reactions, Secrets
from pombot.storage import PomSql


async def newleaf_handler(ctx: Context):
    """Starts a new session for the user, meaning that all the poms in their
    current session will have their current_session property set to false.
    """
    db = mysql.connector.connect(
        host=Secrets.MYSQL_HOST,
        user=Secrets.MYSQL_USER,
        database=Secrets.MYSQL_DATABASE,
        password=Secrets.MYSQL_PASSWORD,
    )
    cursor = db.cursor(buffered=True)
    cursor.execute(PomSql.SELECT_ALL_POMS_CURRENT_SESSION,
                   (ctx.message.author.id, ))
    number_of_poms = len(cursor.fetchall())

    # If the user tries to start a new session before doing anything:
    if number_of_poms == 0:
        await ctx.message.add_reaction(Reactions.FALLEN_LEAF)
        await ctx.send(
            "A new session will be started when you track your first pom.")
        cursor.close()
        db.close()
        return

    # Set all previous poms to not be in the current session.
    cursor.execute(PomSql.UPDATE_SESSION, (ctx.message.author.id,))
    db.commit()

    msg = "A new session will be started when you track your next pom, {name}"
    await ctx.send(msg.format(name=ctx.message.author.display_name))
    await ctx.message.add_reaction(Reactions.LEAVES)

    cursor.close()
    db.close()
