#!/usr/bin/env python3
# bot.py

import os, sys
from dotenv import load_dotenv
from discord.ext import commands
from discord import embeds
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from collections import Counter
import re

load_dotenv()
goalReached = False
TOKEN = os.getenv('DISCORD_TOKEN')
POM_CHANNEL_ID = int(os.getenv('POM_CHANNEL_ID'))
print(TOKEN)
print(POM_CHANNEL_ID)
POM_TRACK_LIMIT = 10
DESCRIPTION_LIMIT = 30
MULTILINE_DESCRIPTION_DISABLED = True
MYSQL_INSERT_QUERY = """INSERT INTO poms (userID, descript, time_set, current_session) VALUES (%s, %s, %s, %s);"""
MYSQL_EVENT_ADD = """INSERT INTO events (event_name, pom_goal, start_date, end_date) VALUES(%s, %s, %s, %s); """
MYSQL_SELECT_ALL_POMS = """SELECT * FROM poms WHERE userID= %s"""
MYSQL_SELECT_EVENT = """ SELECT * FROM events WHERE start_date <= %s AND end_date >= %s;"""
MYSQL_EVENT_SELECT = """SELECT * FROM poms WHERE time_set >= %s AND time_set <= %s; """
MYSQL_UPDATE_SESSION = """UPDATE poms SET current_session = 0 WHERE userID= %s AND current_session = 1;"""
MYSQL_DELETE_POMS = """DELETE FROM poms WHERE userID= %s"""
bot = commands.Bot(command_prefix='!', case_insensitive=True)

"""
Tracks a new pom for the user.
"""


@bot.command(name='pom',
             help='Adds a new pom, if the first word in the description is a number (1-10), multiple poms will be '
                  'added with the given description.',
             pass_context=True)
async def pom(ctx, *, description: str = None):
    pom_count = 1
    db = mysql.connector.connect(
        host="localhost",
        user="admin",
        database="pom_bot",
        password="KoA1411!!"
    )
    cursor = db.cursor(buffered=True)


    try:
        if description:
            # If there is a description, check if the first word is a digit
            # And if it is, split the string to remove the digits length plus 1 for space.
            if description.split(' ', 1)[0].isdigit():
                pom_count = int(description.split(' ', 1)[0])
                if pom_count > POM_TRACK_LIMIT or pom_count < 1:
                    await ctx.message.add_reaction("⚠️")
                    await ctx.send('You can only add between 1 and 10 poms at once.')
                    return

                description = description[(len(str(pom_count)) + 1):]

        # Check if the description is too long
        if description is not None and len(description) > DESCRIPTION_LIMIT:
            await ctx.message.add_reaction("⚠️")
            await ctx.send('Your pom description must be less than 30 characters.')
            return

        if description is not None and "\n" in description and MULTILINE_DESCRIPTION_DISABLED:
            await ctx.message.add_reaction("⚠️")
            await ctx.send('Multi line pom descriptions are disabled.')
            return

        poms_to_add = []
        currentDate = datetime.now()
        formatted_date = currentDate.strftime('%Y-%m-%d %H:%M:%S')
        for _ in range(pom_count):
            new_added_pom = (ctx.message.author.id, description, formatted_date, True)
            poms_to_add.append(new_added_pom)

        cursor.executemany(MYSQL_INSERT_QUERY, poms_to_add)
        db.commit()
    except mysql.connector.Error as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        await ctx.message.add_reaction("🐛")
        f = open('errors.txt', 'a')
        f.write(e)
        f.close()
        print(e)
    await ctx.message.add_reaction("🍅")

    cursor.execute(MYSQL_SELECT_EVENT, (currentDate, currentDate))
    event_info = cursor.fetchall()
    event = cursor.rowcount

    if event != 0:

        global goalReached
        cursor.execute(MYSQL_EVENT_SELECT, (event_info[0][3], event_info[0][4]))
        cursor.fetchall()
        poms = cursor.rowcount
        pom_goal = event_info[0][2]
        
        if poms >= event_info[0][2] and goalReached == False:
            await ctx.send("We've reached our goal of {} poms! Well done <@&727974953894543462>!".format(pom_goal))
            goalReached = True
        elif goalReached == True:
            pass
        else:
            toSend = "The community has reached " + str(poms) + "/" + str(pom_goal) + " poms. Keep up the good work!"
            await ctx.send(toSend)

    cursor.close()
    db.close()
    


"""
Starts a new session for the user, meaning that all the poms in their current session will have their current_session
property set to false. 
"""


@bot.command(name='newleaf', 
            help='Turn over a new leaf and hide the details of your previously tracked poms. Starts '
                    'a new session.', 
            pass_context=True)
async def new_session(ctx):
    db = mysql.connector.connect(
        host="localhost",
        user="admin",
        database="pom_bot",
        password="KoA1411!!"
    )
    cursor = db.cursor(buffered=True)
    cursor.execute(MYSQL_SELECT_ALL_POMS + ' AND current_session = 1;', (ctx.message.author.id,))
    cursor.fetchall()
    document_count = cursor.rowcount
    
    # If the user tries to start a new session before doing anything
    if document_count == 0:
        await ctx.message.add_reaction("🍂")
        await ctx.send("A new session will be started when you track your first pom.")
        return

    # Set all previous poms to not be in the current session
    cursor.execute(MYSQL_UPDATE_SESSION, (ctx.message.author.id,))
    db.commit()
    await ctx.message.add_reaction("🍃")
    await ctx.send("A new session will be started when you track your next pom, {}."
                   .format(ctx.message.author.display_name))
    cursor.close()
    db.close()

"""
Gives the user an overview of how many poms they've been doing so far.
"""


@bot.command(name='poms', help='See details for your tracked poms and the current session.', pass_context=True)
async def poms(ctx):
    db = mysql.connector.connect(
        host="localhost",
        user="admin",
        database="pom_bot",
        password="KoA1411!!"
    )
    cursor = db.cursor(buffered=True)
    # Fetch all poms for user based on their Discord ID
    cursor.execute(MYSQL_SELECT_ALL_POMS, (ctx.message.author.id,))
    own_poms = cursor.fetchall()
    # If the user has no tracked poms
    if len(own_poms) == 0 or own_poms is None:
        await ctx.message.add_reaction("⚠️")
        await ctx.send("You have no tracked poms.")
        return

    # All poms tracked this session by user
    session_poms = [x for x in own_poms if x[4] == 1]

    # Add a timestamp for session start, if a pom is tracked in this session
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
        except Exception as e:
            await ctx.message.add_reaction("🐛")
            f = open('errors.log', 'a')
            f.write(e)
            f.close()
            print(e)
    else:
        session_start = "Not started yet"

    # Group poms by their description
    session_described_poms = []
    for p in session_poms:
        if p[2]:
            session_described_poms.append(p)
    described_poms_amount = len(session_described_poms)
    session_described_poms = Counter(des_pom[2].capitalize() for des_pom in session_described_poms)
    # Set variable to see how many poms the user has.
    session_pom_amount = len(session_poms)
    total_pom_amount = len(own_poms)

    # Generate the embed for sending to the user
    title_embed = "Pom statistics for {}".format(ctx.message.author.display_name)
    description_embed = "**Pom statistics**\n" \
                        "Session started: *{}*\n" \
                        "Total poms this session: *{}*\n" \
                        "Accumulated poms: *{}*\n" \
                        "\n" \
                        "**Poms this session**\n" \
        .format(session_start, session_pom_amount, total_pom_amount)

    # Added description poms, sorted by how common they are
    for p in session_described_poms.most_common():
        description_embed += "{}: {}\n".format(p[0], p[1])

    # Add non-described count, if applicable
    undesignated_pom_count = session_pom_amount - described_poms_amount
    if undesignated_pom_count > 0:
        description_embed += "*Undesignated poms: {}*".format(undesignated_pom_count)

    # Generate embed message to send
    embedded_message = embeds.Embed(description=description_embed, colour=0xff6347) \
        .set_author(name=title_embed, icon_url="https://i.imgur.com/qRoH5B5.png" )

    await ctx.author.send(embed=embedded_message)
    await ctx.send("I've sent you a DM with your poms")
    cursor.close()
    db.close()

"""
Gives the user an overview of how many poms they've been doing so far.
"""


@bot.command(name='howmany', help='List your poms with a given description.', pass_context=True)
async def howmany(ctx, *, description: str = None):
    db = mysql.connector.connect(
        host="localhost",
        user="admin",
        database="pom_bot",
        password="KoA1411!!"
    )
    cursor = db.cursor(buffered=True)
    if description is None:
        await ctx.message.add_reaction("⚠️")
        await ctx.send("You must specify a description to search for.")
        return
    # Fetch all poms for user based on their Discord ID
    cursor.execute(MYSQL_SELECT_ALL_POMS + ' AND descript=%s;', (ctx.message.author.id, description))
    own_poms = cursor.fetchall()
    # If the user has no tracked poms
    if len(own_poms) == 0 or own_poms is None:
        await ctx.message.add_reaction("⚠️")
        await ctx.send("You have no tracked poms with that description.")
        return
    total_pom_amount = len(own_poms)
    await ctx.message.add_reaction("🧮")
    await ctx.send("You have {} pom(s) with the description {}".format(total_pom_amount, description))
    cursor.close()
    db.close()

"""
Undoes / removes your x latest poms. Default is 1 latest.
"""


@bot.command(name='undo', help="Undo/remove your x latest poms. If no number is specified, only the newest pom will "
                               "be undone.")
async def remove(ctx, *, count: str = None):
    db = mysql.connector.connect(
        host="localhost",
        user="admin",
        database="pom_bot",
        password="KoA1411!!"
    )
    cursor = db.cursor(buffered=True)
    pom_count = 1
    if count:
        if count.split(' ', 1)[0].isdigit():
            pom_count = int(count.split(' ', 1)[0])
            if pom_count > POM_TRACK_LIMIT:
                await ctx.message.add_reaction("⚠️")
                await ctx.send('You can only undo up to 10 poms at once.')
                return

    try:
        cursor.execute(MYSQL_SELECT_ALL_POMS + ' ORDER BY time_set DESC LIMIT %s;', (ctx.message.author.id, pom_count))
        to_delete = cursor.fetchall()

        to_delete_id = []
        for pom_to_delete in to_delete:
            to_delete_id.append((ctx.message.author.id, pom_to_delete[0]))
        cursor.executemany(MYSQL_DELETE_POMS + ' AND id=%s;', to_delete_id)
        db.commit()

    except Exception as e:
        await ctx.message.add_reaction("🐛")
        f = open('errors.log', 'a')
        f.write(e)
        f.close()
        print(e)

    await ctx.message.add_reaction("↩")
    cursor.close()
    db.close()



"""
Remove your x latest poms. Default is 1 latest.
"""


@bot.command(name='reset', help="Permanently deletes all your poms. WARNING: There's no undoing this.")
async def remove(ctx):
    db = mysql.connector.connect(
        host="localhost",
        user="admin",
        database="pom_bot",
        password="KoA1411!!"
    )
    cursor = db.cursor(buffered=True)
    try:
        cursor.execute(MYSQL_DELETE_POMS, (ctx.message.author.id,))
        db.commit()

    except Exception as e:
        await ctx.message.add_reaction("🐛")
        f = open('errors.log', 'a')
        f.write(e)
        f.close()
        print(e)

    await ctx.message.add_reaction("🗑️")
    cursor.close()
    db.close()


"""
ADMIN COMMAND:
Allows guardians and helpers to see the total amount of poms completed by KOA users since ever.
"""


@bot.command(name='total', help='List total amount of poms.')
@commands.has_any_role('Guardians', 'Helper')
async def total(ctx):
    db = mysql.connector.connect(
        host="localhost",
        user="admin",
        database="pom_bot",
        password="KoA1411!!"
    )
    cursor = db.cursor(buffered=True)
    cursor.execute('SELECT * FROM poms;')
    document_count = cursor.rowcount
    await ctx.send("Total amount of poms: {}".format(document_count))
    cursor.close()
    db.close()


"""
ADMIN COMMAND:
Allows guardians and helpers to start an event.
"""


@bot.command(name='start', help='A command that allows Helpers or Guardians to create community pom events!')
@commands.has_any_role('Guardians', 'Helper')
async def start_event(ctx, event_name, event_goal, event_start, event_end):
    # validate arguments
    if not str.isdigit(event_goal):
        await ctx.send('{} is not a valid number for a pom goal!'.format(event_goal))
        return

    db = mysql.connector.connect(
        host="localhost",
        user="admin",
        database="pom_bot",
        password="KoA1411!!"
    )
    cursor = db.cursor(buffered=True)
    
    year = str(datetime.today().year)
    start_date = event_start + ' 01, ' + year + ', 00:00:00'
    end_date = event_end + ' 01, ' + year + ', 00:00:00'

    start_date = datetime.strptime(start_date, '%B %d, %Y, %H:%M:%S')
    end_date = datetime.strptime(end_date, '%B %d, %Y, %H:%M:%S')

    event = (event_name, event_goal, start_date, end_date)

    cursor.execute(MYSQL_EVENT_ADD, event)
    db.commit()

    cursor.close()
    db.close()
    goalReached = False


'''
If user tries to use a command that they do not have access to
'''


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.message.add_reaction("⚠️")
        await ctx.send('You do not have the correct role for this command.')


'''
Limit to certain channels, must process commands afterwards,
or they'll stop working.
'''


@bot.event
async def on_message(message):
    if message.channel.id != POM_CHANNEL_ID:
        return
    await bot.process_commands(message)


bot.run(TOKEN)
