import textwrap
from datetime import datetime

import mysql.connector
from discord.ext.commands import Context

from pombot.config import Secrets
from pombot.state import State
from pombot.storage import EventSql


async def start_event_handler(
        ctx: Context,
        event_name: str,
        event_goal: str,
        start_month: str,
        start_day: str,
        end_month: str,
        end_day: str,
):
    """Allows guardians and helpers to start an event.

    This is an admin-only command.
    """
    # validate arguments
    if not str.isdigit(event_goal):
        await ctx.send(f"{event_goal} is not a valid number for a pom goal.")
        return
    if not str.isdigit(start_day):
        await ctx.send(f"{start_day} is not a valid start day.")
        return
    if not str.isdigit(end_day):
        await ctx.send(f"{end_day} is not a valid end day.")
        return

    dateformat = "%B %d %Y %H:%M:%S"
    year = str(datetime.today().year)

    start_date_string = f"{start_month} {start_day} {year} 00:00:00"
    end_date_string = f"{end_month} {end_day} {year} 23:59:59"

    # validate start date after putting month and day together
    try:
        start_date = datetime.strptime(start_date_string, dateformat)
    except ValueError:
        await ctx.send(f"{start_month} {start_day} is not a valid start date.")
        return

    # validate end date after putting month and day together
    try:
        end_date = datetime.strptime(end_date_string, dateformat)
    except ValueError:
        await ctx.send(f"{end_month} {end_day} is not a valid end date.")
        return

    # make sure the start date is before the end date
    if start_date >= end_date:
        await ctx.send(f"Invalid dates: the start date must be before the end date.")
        return

    db = mysql.connector.connect(
        host=Secrets.MYSQL_HOST,
        user=Secrets.MYSQL_USER,
        database=Secrets.MYSQL_DATABASE,
        password=Secrets.MYSQL_PASSWORD,
    )
    cursor = db.cursor(buffered=True)

    event = (event_name, event_goal, start_date, end_date)

    cursor.execute(EventSql.EVENT_ADD, event)
    db.commit()
    cursor.close()
    db.close()

    State.goal_reached = False

    await ctx.send(textwrap.dedent(f"""\
        Successfully created event "{event_name}" with a goal of {event_goal} poms,
        starting on {start_date.month}/{start_date.day} and ending on {end_date.month}/{end_date.day}.
    """))
