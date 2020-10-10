import mysql.connector
from discord.ext.commands import Context

from pombot.config import Reactions, Secrets
from pombot.storage import PomSql


async def reset_handler(ctx: Context):
    """Undontionally delete all of the author's poms."""
    db = mysql.connector.connect(
        host=Secrets.MYSQL_HOST,
        user=Secrets.MYSQL_USER,
        database=Secrets.MYSQL_DATABASE,
        password=Secrets.MYSQL_PASSWORD,
    )
    cursor = db.cursor(buffered=True)

    try:
        cursor.execute(PomSql.DELETE_POMS, (ctx.message.author.id,))
        db.commit()

    except mysql.connector.Error as exc:
        await ctx.message.add_reaction(Reactions.ERROR)
        f = open('errors.log', 'a')
        f.write(exc)
        f.close()
        print(exc)

    finally:
        cursor.close()
        db.close()

    await ctx.message.add_reaction(Reactions.RESET)
