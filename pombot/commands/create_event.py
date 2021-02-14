import textwrap
from datetime import datetime

from discord.ext.commands import Context

import pombot
from pombot.config import Reactions
from pombot.lib.messages import send_embed_message
from pombot.lib.storage import Storage
from pombot.lib.types import DateRange
from pombot.state import State


async def do_create_event(ctx: Context, *args):
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
