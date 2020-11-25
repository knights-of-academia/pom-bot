import textwrap
from datetime import datetime

from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.bot import Bot

import pombot.errors
from pombot.config import Reactions
from pombot.lib.messages import send_embed_message, send_usage_message
from pombot.state import State
from pombot.storage import Storage


class AdminCommands(commands.Cog):
    """Handlers for admin-level pom commands."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(hidden=True)
    # @commands.has_any_role("Guardian", "Helper")
    async def total(self, ctx: Context, *args):
        """Display the total poms for all users for a range of dates.

        This is an admin-only command.
        """

        def _usage(header: str = None):
            cmd = ctx.prefix + ctx.invoked_with

            header = (header
                      or f"Your command `{cmd + ' ' + ' '.join(args)}` does "
                      "not meet the usage requirements.")

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

                At present, events must not overlap; only one concurrent event
                can be ongoing at a time.
                ```
            """)

        if args:
            try:
                start_month, start_day, end_month, end_day = args
            except ValueError:
                ctx.send(f'Invalid date range: {" ".join(args)}')
                await ctx.message.add_reaction(Reactions.ROBOT)
                await ctx.author.send(_usage())
                return

        num_poms = Storage.get_num_poms_for_all_users()
        await ctx.send(f"Total amount of poms: {num_poms}")

    @commands.command(name="start", aliases=["start_event", "event"], hidden=True)
    # @commands.has_any_role("Guardian", "Helper")
    async def do_start_event(self, ctx: Context, *args):
        """Allows guardians and helpers to start an event.

        This is an admin-only command.
        """
        def _usage(header: str = None):
            cmd = ctx.prefix + ctx.invoked_with

            header = (header
                      or f"Your command `{cmd + ' ' + ' '.join(args)}` does "
                      "not meet the usage requirements.")

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

                At present, events must not overlap; only one concurrent event
                can be ongoing at a time.
                ```
            """)

        try:
            *name, pom_goal, start_month, start_day, end_month, end_day = args
        except ValueError:
            await ctx.message.add_reaction(Reactions.ROBOT)
            await ctx.author.send(_usage())
            return

        event_name = " ".join(name)

        try:
            pom_goal = int(pom_goal)

            if pom_goal <= 0:
                raise ValueError("Goal must be a positive number.")
        except ValueError as exc:
            await ctx.message.add_reaction(Reactions.ROBOT)
            await ctx.author.send(_usage(f"Invalid goal: `{pom_goal}`, {exc}"))
            return

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

        overlapping_events = Storage.get_overlapping_events(start_date, end_date)

        if any(overlapping_events):
            msg = "Found overlapping events: {}".format(
                ", ".join(event.event_name for event in overlapping_events)
            )
            await ctx.message.add_reaction(Reactions.ROBOT)
            await ctx.author.send(_usage(msg))
            return

        try:
            Storage.add_new_event(event_name, pom_goal, start_date, end_date)
        except pombot.errors.EventCreationError as exc:
            await ctx.message.add_reaction(Reactions.ROBOT)
            await ctx.author.send(_usage(f"Failed to create event: {exc}"))
            return

        State.goal_reached = False

        await send_embed_message(
            ctx,
            title="New Event!",
            description=textwrap.dedent(f"""\
                Event name: **{event_name}**
                Poms goal:  **{pom_goal}**

                Starts: *{start_date.strftime("%B %d, %Y")}*
                Ends:   *{end_date.strftime("%B %d, %Y")}*
            """),
        )

    @commands.command(name="remove_event", aliases=["delete_event"], hidden=True)
    @commands.has_any_role("Guardian", "Helper")
    async def do_remove_event(self, ctx: Context, *args):
        """Allows guardians and helpers to start an event.

        This is an admin-only command.
        """

        if not args:
            cmd = ctx.prefix + ctx.invoked_with

            await ctx.author.send(textwrap.dedent(f"""
                Remove an event.
                ```text
                Usage: {cmd} <name>
                ```
            """))

            return

        name = " ".join(args).strip()
        Storage.delete_event(name)
        await ctx.message.add_reaction(Reactions.CHECKMARK)


def setup(bot: Bot):
    """Required to load extension."""
    bot.add_cog(AdminCommands(bot))
