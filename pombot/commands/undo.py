from pombot.storage import PomSql
import mysql.connector
from discord.ext.commands import Context

from pombot.config import Config, Reactions, Secrets


async def undo_handler(ctx: Context, *, description: str = None):
    """Removes the user's x latest poms. Default is 1 (the latest)."""
    count = 1

    db = mysql.connector.connect(
        host=Secrets.MYSQL_HOST,
        user=Secrets.MYSQL_USER,
        database=Secrets.MYSQL_DATABASE,
        password=Secrets.MYSQL_PASSWORD,
    )
    cursor = db.cursor(buffered=True)

    if description:
        try:
            count = int(description.split(' ', 1)[0])
        except ValueError:
            await ctx.message.add_reaction(Reactions.WARNING)
            await ctx.send("Please specify a number of poms to undo.")
            cursor.close()
            db.close()
            return

        if count > Config.POM_TRACK_LIMIT:
            await ctx.message.add_reaction(Reactions.WARNING)
            await ctx.send(f"You can only undo up to {Config.POM_TRACK_LIMIT} poms at once.")
            cursor.close()
            db.close()
            return

    cursor.execute(PomSql.SELECT_ALL_POMS_LIMIT, (ctx.message.author.id, count))
    cursor.executemany(PomSql.DELETE_POMS, [(ctx.message.author.id, pom[0])
                                            for pom in cursor.fetchall()])
    db.commit()

    await ctx.message.add_reaction(Reactions.UNDO)
    cursor.close()
    db.close()
