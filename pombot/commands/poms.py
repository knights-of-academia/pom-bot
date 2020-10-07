import textwrap
from collections import Counter
from datetime import datetime

import mysql.connector
from discord.embeds import Embed
from discord.ext.commands import Context

from pombot.config import Reactions, Secrets
from pombot.storage import PomSql


async def poms_handler(ctx: Context):
    """Gives the user an overview of how many poms they've been doing so far.
    """
    db = mysql.connector.connect(
        host=Secrets.MYSQL_HOST,
        user=Secrets.MYSQL_USER,
        database=Secrets.MYSQL_DATABASE,
        password=Secrets.MYSQL_PASSWORD,
    )
    cursor = db.cursor(buffered=True)

    # Fetch all poms for user based on their Discord ID.
    cursor.execute(PomSql.SELECT_ALL_POMS, (ctx.message.author.id,))
    own_poms = cursor.fetchall()

    # If the user has no tracked poms.
    if len(own_poms) == 0 or own_poms is None:
        await ctx.message.add_reaction(Reactions.WARNING)
        await ctx.send("You have no tracked poms.")
        cursor.close()
        db.close()
        return

    # All poms tracked this session by user.
    session_poms = [own_pom for own_pom in own_poms if own_pom[4] == 1]

    # Add a timestamp for session start, if a pom is tracked in this session.
    session_start = "Not started yet"

    if len(session_poms) > 0:
        try:
            time_now = datetime.now()
            time_then = session_poms[0][3]
            duration_in_s = (time_now - time_then).total_seconds()
            days = int(duration_in_s // (24 * 3600))

            duration_in_s = duration_in_s % (24 * 3600)
            hours = int(duration_in_s // 3600)

            duration_in_s %= 3600
            minutes = int(duration_in_s // 60)

            session_start = "{} days, {} hours, {} minutes".format(days, hours, minutes)
        except Exception as exc:
            await ctx.message.add_reaction(Reactions.ERROR)
            f = open('errors.log', 'a')
            f.write(exc)
            f.close()
            print(exc)
            cursor.close()
            db.close()
            raise

    # Group poms by their description.
    session_described_poms = []
    for session_pom in session_poms:
        if session_pom[2]:
            session_described_poms.append(session_pom)
    described_poms_amount = len(session_described_poms)
    session_described_poms = Counter(des_pom[2].capitalize() for des_pom in session_described_poms)

    # Set variable to see how many poms the user has..
    session_pom_amount = len(session_poms)
    total_pom_amount = len(own_poms)

    # Generate the embed for sending to the user.
    embed_title = "Pom statistics for {}".format(ctx.message.author.display_name)
    embed_description = textwrap.dedent(f"""\
        **Pom statistics**
        Session started: *{session_start}*
        Total poms this session: *{session_pom_amount}*
        Accumulated poms: *{total_pom_amount}*

        **Poms this session**
    """)

    # Added description poms, sorted by how common they are.
    for p in session_described_poms.most_common():
        embed_description += "{}: {}\n".format(p[0], p[1])

    # Add non-described count, if applicable.
    undesignated_pom_count = session_pom_amount - described_poms_amount
    if undesignated_pom_count > 0:
        embed_description += "*Undesignated poms: {}*".format(undesignated_pom_count)

    # Generate embed message to send.
    embedded_message = Embed(description=embed_description, colour=0xff6347) \
        .set_author(name=embed_title, icon_url="https://i.imgur.com/qRoH5B5.png" )

    await ctx.author.send(embed=embedded_message)
    await ctx.send("I've sent you a DM with your poms")
    cursor.close()
    db.close()
