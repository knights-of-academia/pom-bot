import mysql.connector
from discord.ext.commands import Context

from pombot.config import Secrets


async def total_handler(ctx: Context):
    """Allows guardians and helpers to see the total amount of poms completed
    by KOA users since ever.

    This is an admin-only command.
    """
    db = mysql.connector.connect(
        host=Secrets.MYSQL_HOST,
        user=Secrets.MYSQL_USER,
        database=Secrets.MYSQL_DATABASE,
        password=Secrets.MYSQL_PASSWORD,
    )
    cursor = db.cursor(buffered=True)
    cursor.execute('SELECT * FROM poms;')
    num_poms = cursor.rowcount
    cursor.close()
    db.close()

    await ctx.send(f"Total amount of poms: {num_poms}")
