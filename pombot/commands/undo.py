import mysql.connector
from discord.ext.commands import Context

from pombot.config import Config, Reactions, Secrets
from pombot.storage import PomSql


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
        first_word, *_ = description.split(' ', 1)[0]

        try:
            count = int(first_word)
        except ValueError:
            msg = f'Please specify a number of poms to undo, instead of "{first_word}".'

            await ctx.message.add_reaction(Reactions.WARNING)
            await ctx.send(msg)
            cursor.close()
            db.close()
            return

        if count > Config.POM_TRACK_LIMIT:
            msg = f"You can only undo up to {Config.POM_TRACK_LIMIT} poms at once."

            await ctx.message.add_reaction(Reactions.WARNING)
            await ctx.send(msg)
            cursor.close()
            db.close()
            return

    cursor.execute(PomSql.SELECT_ALL_POMS_WITH_LIMIT,
                   (ctx.message.author.id, count))

    cursor.executemany(PomSql.DELETE_POMS_WITH_ID,
                       [(ctx.message.author.id, pom_id)
                        for pom_id, *_ in cursor.fetchall()])
    db.commit()

    await ctx.message.add_reaction(Reactions.UNDO)
    cursor.close()
    db.close()
