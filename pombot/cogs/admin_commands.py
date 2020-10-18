import textwrap
from datetime import datetime

import mysql.connector
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.bot import Bot

from pombot.config import Reactions, Secrets
from pombot.lib.embeds import send_embed_message
from pombot.state import State
from pombot.storage import EventSql


class AdminCommands(commands.Cog):
    """Handlers for admin-level pom commands."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.has_any_role("Guardian", "Helper")
    async def total(self, ctx: Context):
        """Allows guardians and helpers to see the total amount of poms
        completed by KOA users since ever.

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

    @commands.command(name="start", aliases=["start_event"], hidden=True)
    @commands.has_any_role("Guardian", "Helper")
    async def do_start_event(self, ctx: Context, *args):
        """Allows guardians and helpers to start an event.

        This is an admin-only command.
        """
        def _usage(header: str = None):
            cmd = ctx.prefix + ctx.invoked_with

            header = (header
                      or f"Your command `{cmd}` does not meet the usage "
                      "requirements for this command.")

            return textwrap.dedent(f"""\
                {header}
                ```text
                Usage: {cmd} <name> <goal> <start_month> <start_day> <end_month <end_day>

                Where:
                    <name>         Name for this event.
                    <goal>         Number of poms to reach in this event.
                    <start_month>  Event starting month.
                    <start_day>    Event starting day.
                    <end_month>    Event ending month.
                    <end_day>      Event ending day.

                Example:
                    {cmd} The Best Event 100 June 10 July 4
                ```
            """)

        try:
            (*event_name, event_goal, start_month, start_day, end_month,
             end_day) = args
        except ValueError:
            await ctx.message.add_reaction(Reactions.ROBOT)
            await ctx.author.send(_usage())
            return

        event_name = " ".join(event_name)

        dateformat = "%B %d %Y %H:%M:%S"
        year = datetime.today().year
        dates = {
            "start": f"{start_month} {start_day} {year} 00:00:00",
            "end": f"{end_month} {end_day} {year} 23:59:59",
        }

        for date_name, date_str in dates.items():
            try:
                dates[date_name] = datetime.strptime(date_str, dateformat)
            except ValueError:
                await ctx.message.add_reaction(Reactions.ROBOT)
                await ctx.author.send(_usage(f"Invalid date: `{date_str}`"))
                return

        start_date, end_date = dates.values()

        if end_date < start_date:
            end_date = datetime.strptime(
                f"{end_month} {end_day} {year + 1} 23:59:59", dateformat)

        db = mysql.connector.connect(
            host=Secrets.MYSQL_HOST,
            user=Secrets.MYSQL_USER,
            database=Secrets.MYSQL_DATABASE,
            password=Secrets.MYSQL_PASSWORD,
        )
        cursor = db.cursor(buffered=True)

        try:
            cursor.execute(EventSql.EVENT_ADD,
                           (event_name, event_goal, start_date, end_date))
        except mysql.connector.DatabaseError as exc:
            await ctx.message.add_reaction(Reactions.ROBOT)
            await ctx.author.send(_usage(f"Database update failed: {exc.msg}"))
            cursor.close()
            db.close()
            return

        db.commit()
        cursor.close()
        db.close()

        State.goal_reached = False

        await send_embed_message(
            ctx,
            title="New Event!",
            description=textwrap.dedent(f"""\
                Event name: **{event_name}**
                Poms goal:  **{event_goal}**

                Starts: *{start_date.strftime("%B %d, %Y")}*
                Ends:   *{end_date.strftime("%B %d, %Y")}*
            """),
        )


def setup(bot: Bot):
    """Required to load extension."""
    bot.add_cog(AdminCommands(bot))
