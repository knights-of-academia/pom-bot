from datetime import datetime

import mysql.connector
from discord.ext import commands as discord_commands

from pombot.commands.newleaf import newleaf_handler
from pombot.commands.pom import pom_handler
from pombot.commands.poms import poms_handler
from pombot.config import Config, Secrets

bot = discord_commands.Bot(command_prefix='!', case_insensitive=True)


@bot.event
async def on_ready():
    print(f'{bot.user} is ready on Discord')


@bot.command()
async def pom(ctx, *, description: str = None):
    """Adds a new pom, if the first word in the description is a number
    (1-10), multiple poms will be added with the given description.
    """
    await pom_handler(ctx, description=description)


@bot.command()
async def newleaf(ctx):
    """Turn over a new leaf and hide the details of your previously tracked
    poms. Starts a new session.
    """
    await newleaf_handler(ctx)


@bot.command()
async def poms(ctx):
    """See details for your tracked poms and the current session."""
    await poms_handler(ctx)


"""
Gives the user an overview of how many poms they've been doing so far.
"""
@bot.command(name='howmany', help='List your poms with a given description.', pass_context=True)
async def howmany(ctx, *, description: str = None):
    db = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        database=MYSQL_DATABASE,
        password=MYSQL_PASSWORD,
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
        host=MYSQL_HOST,
        user=MYSQL_USER,
        database=MYSQL_DATABASE,
        password=MYSQL_PASSWORD,
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
        host=MYSQL_HOST,
        user=MYSQL_USER,
        database=MYSQL_DATABASE,
        password=MYSQL_PASSWORD,
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
@discord_commands.has_any_role('Guardian', 'Helper')
async def total(ctx):
    db = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        database=MYSQL_DATABASE,
        password=MYSQL_PASSWORD,
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
@discord_commands.has_any_role('Guardian', 'Helper')
async def start_event(ctx, event_name, event_goal, start_month, start_day, end_month, end_day):
    # validate arguments
    if not str.isdigit(event_goal):
        await ctx.send(f'{event_goal} is not a valid number for a pom goal.')
        return
    if not str.isdigit(start_day):
        await ctx.send(f'{start_day} is not a valid start day.')
        return
    if not str.isdigit(end_day):
        await ctx.send(f'{end_day} is not a valid end day.')
        return

    dateformat = '%B %d %Y %H:%M:%S'
    year = str(datetime.today().year)

    start_date_string = f'{start_month} {start_day} {year} 00:00:00'
    end_date_string = f'{end_month} {end_day} {year} 23:59:59'

    # validate start date after putting month and day together
    try:
        start_date = datetime.strptime(start_date_string, dateformat)
    except ValueError:
        await ctx.send(f'{start_month} {start_day} is not a valid start date.')
        return

    # validate end date after putting month and day together
    try:
        end_date = datetime.strptime(end_date_string, dateformat)
    except ValueError:
        await ctx.send(f'{end_month} {end_day} is not a valid end date.')
        return

    # make sure the start date is before the end date
    if not start_date < end_date:
        await ctx.send(f'Invalid dates: the start date must be before the end date.')
        return

    db = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        database=MYSQL_DATABASE,
        password=MYSQL_PASSWORD,
    )
    cursor = db.cursor(buffered=True)

    event = (event_name, event_goal, start_date, end_date)

    cursor.execute(MYSQL_EVENT_ADD, event)
    db.commit()

    cursor.close()
    db.close()
    goalReached = False

    await ctx.send(f"Successfully created event '{event_name}' with a goal of {event_goal} poms, "
                   f"starting on {start_date.month}/{start_date.day} and ending on {end_date.month}/{end_date.day}.")

'''
If user tries to use a command that they do not have access to
'''


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord_commands.errors.CheckFailure):
        await ctx.message.add_reaction("⚠️")
        await ctx.send('You do not have the correct role for this command.')


'''
Limit to certain channels, must process commands afterwards,
or they'll stop working.
'''


@bot.event
async def on_message(message):
    if ("private" in message.channel.type
            or message.channel.name != Config.POM_CHANNEL_NAME):
        return

    await bot.process_commands(message)


bot.run(Secrets.TOKEN)
