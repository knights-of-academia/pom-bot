import logging
import random
from datetime import datetime
from typing import Any

import mysql.connector
from discord.ext import commands as discord_commands
from discord.ext.commands import Context

from pombot.commands.howmany import howmany_handler
from pombot.commands.newleaf import newleaf_handler
from pombot.commands.pom import pom_handler
from pombot.commands.poms import poms_handler
from pombot.config import Config, Reactions, Secrets

bot = discord_commands.Bot(command_prefix='!', case_insensitive=True)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@bot.event
async def on_ready():
    """Startup procedure after bot has logged into Discord."""
    _log.info("%s is ready on Discord", bot.user)


@bot.command()
async def pom(ctx: Context, *, description: str = None):
    """Adds a new pom, if the first word in the description is a number
    (1-10), multiple poms will be added with the given description.
    """
    await pom_handler(ctx, description=description)


@bot.command()
async def poms(ctx: Context):
    """See details for your tracked poms and the current session."""
    await poms_handler(ctx)


@bot.command()
async def howmany(ctx, *, description: str = None):
    """List your poms with a given description."""
    await howmany_handler(ctx, description=description)


@bot.command()
async def newleaf(ctx: Context):
    """Turn over a new leaf and hide the details of your previously tracked
    poms. Starts a new session.
    """
    await newleaf_handler(ctx)


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
                cursor.close()
                db.close()
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



@bot.event
async def on_command_error(ctx: Context, error: Any):
    """Alert users when using commands to which they have no access. In all
    other cases, log the error and mark it in discord.
    """
    if isinstance(error, discord_commands.errors.CheckFailure):
        message, *_ = random.choices([
            "You do not have access to this command.",
            "Sorry, that command is out-of-order.",
            "!!! ACCESS DENIED !!! \\**whale noises\\**",
            "Wir konnten die Smaragde nicht finden!",
            "Do you smell that?",
            "\\**(Windows XP startup sound)\\**",
            "This is not the command you're looking for. \\**waves hand\\**",
            "*noop*",
        ])

        await ctx.message.add_reaction(Reactions.WARNING)
        await ctx.send(message)
        return

    for message in error.args:
        _log.error(
            'error: user %s (%s) running "%s" hit: %s',
            ctx.author.display_name,
            ctx.author.name + "#" +ctx.author.discriminator,
            ctx.message.content,
            message,
        )

    await ctx.message.add_reaction(Reactions.ERROR)


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
