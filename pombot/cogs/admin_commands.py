import textwrap
from datetime import datetime

from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.bot import Bot

import pombot.lib.errors
from pombot.config import Reactions
from pombot.lib.messages import send_embed_message
from pombot.lib.pomwars import setup_pomwar_scoreboard
from pombot.lib.types import DateRange
from pombot.state import State
from pombot.storage import Storage


class AdminCommands(commands.Cog):
    """Handlers for admin-level pom commands."""
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.has_any_role("Guardian")
    async def total(self, ctx: Context, *args):
        """Display the total poms for all users for a range of dates. If no
        range of dates is given, all poms are tallied.

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
                Usage: {cmd} [<start_month> <start_day> <end_month <end_day>]

                Where:
                    <start_month>  From this month...
                    <start_day>    ...And this day,
                    <end_month>    To this month...
                    <end_day>      ...And this day.

                Example:
                    {cmd}

                    {cmd} january 1 january 31

                    If no range of dates is given, all poms are tallied.
                ```
            """)

        if args:
            try:
                date_range = DateRange(*args[-4:])
            except ValueError as exc:
                await ctx.message.add_reaction(Reactions.ROBOT)
                await ctx.author.send(_usage(header=exc))
                return

            poms = await Storage.get_poms(date_range=date_range)
            msg = f"Total amount of poms in range {date_range}: {len(poms)}"
        else:
            poms = await Storage.get_poms()
            msg = f"Total amount of poms since ever: {len(poms)}"

        await ctx.send(msg)

    @commands.command(aliases=["start", "event", "new_event"], hidden=True)
    @commands.has_any_role("Guardian")
    async def create_new_event(self, ctx: Context, *args):
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

        try:
            date_range = DateRange(start_month, start_day, end_month, end_day)
        except ValueError as exc:
            await ctx.message.add_reaction(Reactions.ROBOT)
            await ctx.author.send(_usage(header=exc))
            return

        overlapping_events = await Storage.get_overlapping_events(date_range)

        if overlapping_events:
            msg = "Found overlapping events: {}".format(", ".join(
                event.event_name for event in overlapping_events))
            await ctx.message.add_reaction(Reactions.ROBOT)
            await ctx.author.send(_usage(msg))
            return

        try:
            await Storage.add_new_event(event_name, pom_goal, date_range)
        except pombot.lib.errors.EventCreationError as exc:
            await ctx.message.add_reaction(Reactions.ROBOT)
            await ctx.author.send(_usage(f"Failed to create event: {exc}"))
            return

        State.goal_reached = False
        fmt = lambda dt: datetime.strftime(dt, "%B %d, %Y")

        await send_embed_message(
            ctx,
            title="New Event!",
            description=textwrap.dedent(f"""\
                Event name: **{event_name}**
                Poms goal:  **{pom_goal}**

                Starts: *{fmt(date_range.start_date)}*
                Ends:   *{fmt(date_range.end_date)}*
            """),
        )

    @commands.command(aliases=["delete_event"], hidden=True)
    @commands.has_any_role("Guardian")
    async def remove_event(self, ctx: Context, *args):
        """Allows guardians to remove an existing event.

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
        await Storage.delete_event(name)
        await ctx.message.add_reaction(Reactions.CHECKMARK)

    @commands.command(hidden=True)
    @commands.has_any_role("Guardian")
    async def load_pom_wars(self, ctx: Context):
        """Manually load the pombot.cogs.pom_wars_commands."""
        await ctx.send("Loading cog.")
        self.bot.load_extension("pombot.cogs.pom_wars_commands")
        # When the extension is loaded dynamically, the on_ready event is not
        # triggered, so set up the Scoreboard explicitly.
        await setup_pomwar_scoreboard(self.bot)


def setup(bot: Bot):
    """Required to load extension."""
    bot.add_cog(AdminCommands(bot))
