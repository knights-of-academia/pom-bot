import os
import sys
from datetime import datetime

import mysql.connector
from discord.ext.commands import Context

from pombot.config import Config, Reactions, Secrets
from pombot.state import State
from pombot.storage import EventSql, PomSql


async def pom_handler(ctx: Context, *, description: str = None):
    """Tracks a new pom for the user."""
    pom_count = 1
    current_date = datetime.now()

    db = mysql.connector.connect(
        host=Secrets.MYSQL_HOST,
        user=Secrets.MYSQL_USER,
        database=Secrets.MYSQL_DATABASE,
        password=Secrets.MYSQL_PASSWORD,
    )
    cursor = db.cursor(buffered=True)

    try:
        if description:
            # If there is a description, check if the first word is a digit. If
            # it is, split the string to remove the digits length plus 1 for
            # space.
            if description.split(' ', 1)[0].isdigit():
                pom_count = int(description.split(' ', 1)[0])
                if pom_count > Config.POM_TRACK_LIMIT or pom_count < 1:
                    await ctx.message.add_reaction(Reactions.WARNING)
                    await ctx.send('You can only add between 1 and 10 poms at once.')
                    return

                description = description[(len(str(pom_count)) + 1):]

        # Check if the description is too long
        if description is not None and len(description) > Config.DESCRIPTION_LIMIT:
            await ctx.message.add_reaction(Reactions.WARNING)
            await ctx.send('Your pom description must be fewer than 30 characters.')
            return

        if description is not None and "\n" in description and Config.MULTILINE_DESCRIPTION_DISABLED:
            await ctx.message.add_reaction(Reactions.WARNING)
            await ctx.send('Multi line pom descriptions are disabled.')
            return

        poms = [(
            ctx.message.author.id,
            description,
            current_date.strftime('%Y-%m-%d) %H:%M:%S'),
            True,
        ) for _ in range(pom_count)]

        cursor.executemany(PomSql.INSERT_QUERY, poms)

        db.commit()
    except mysql.connector.Error as exc:
        exc_type, _exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        await ctx.message.add_reaction(Reactions.ERROR)
        f = open('errors.txt', 'a')
        f.write(exc)
        f.close()
        print(exc)

    await ctx.message.add_reaction(Reactions.TOMATO)

    cursor.execute(EventSql.SELECT_EVENT, (current_date, current_date))
    event_info = cursor.fetchall()

    if cursor.rowcount > 0:
        cursor.execute(PomSql.EVENT_SELECT, (event_info[0][3], event_info[0][4]))
        cursor.fetchall()
        poms = cursor.rowcount
        pom_goal = event_info[0][2]

        if poms >= event_info[0][2] and State.goal_reached == False:
            await ctx.send("We've reached our goal of {} poms! Well done <@&727974953894543462>!".format(pom_goal))
            State.goal_reached = True
        elif State.goal_reached == True:
            pass
        else:
            toSend = "The community has reached " + str(poms) + "/" + str(pom_goal) + " poms. Keep up the good work!"
            await ctx.send(toSend)

    cursor.close()
    db.close()
