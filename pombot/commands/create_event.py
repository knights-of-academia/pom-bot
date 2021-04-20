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
    """Create a new event.

    Usage: !create_event <name> <goal> <start_month> <start_day> <end_month <end_day>

    Where:\r
        <name>         Name for this event.\r
        <goal>         Number of poms to reach in this event.\r
        <start_month>  Event starting month.\r
        <start_day>    Event starting day.\r
        <end_month>    Event ending month.\r
        <end_day>      Event ending day.

    Example:\r
        !create_event The Best Event 100 June 10 July 4

    At present, events must not overlap; only one concurrent event
    can be ongoing at a time.
    """
    try:
        *name, pom_goal, start_month, start_day, end_month, end_day = args
    except ValueError:
        await ctx.reply("Your args are out of order or something.")
        await ctx.message.add_reaction(Reactions.ROBOT)
        return

    if not (event_name := " ".join(name)):  # pylint: disable=superfluous-parens
        await ctx.reply("Please specify an event name.")
        await ctx.message.add_reaction(Reactions.ROBOT)
        return

    try:
        pom_goal = int(pom_goal)

        if pom_goal <= 0:
            raise ValueError("Goal must be a positive number.")
    except ValueError as exc:
        await ctx.reply(f"Invalid goal: `{pom_goal}`, {exc}")
        await ctx.message.add_reaction(Reactions.ROBOT)
        return

    try:
        date_range = DateRange(start_month, start_day, end_month, end_day)
    except ValueError as exc:
        await ctx.reply(exc)
        await ctx.message.add_reaction(Reactions.ROBOT)
        return

    if overlapping_events := await Storage.get_overlapping_events(date_range):
        await ctx.reply("Found overlapping events: {}".format(", ".join(
            event.event_name for event in overlapping_events)))
        await ctx.message.add_reaction(Reactions.ROBOT)
        return

    try:
        await Storage.add_new_event(event_name, pom_goal, date_range)
    except pombot.lib.errors.EventCreationError as exc:
        await ctx.reply(f"Failed to create event: {exc}")
        await ctx.message.add_reaction(Reactions.ROBOT)
        return

    State.goal_reached = False
    fmt = lambda dt: datetime.strftime(dt, "%B %d, %Y")

    await send_embed_message(
        None,
        title="New Event!",
        description=textwrap.dedent(f"""\
            Event name: **{event_name}**
            Poms goal:  **{pom_goal}**

            Starts: *{fmt(date_range.start_date)}*
            Ends:   *{fmt(date_range.end_date)}*
        """),
        _func=ctx.reply,
    )
