import textwrap
from datetime import datetime

from discord.ext.commands import Context

from pombot.lib.storage import Storage
from pombot.lib.messages import send_embed_message


async def do_events(ctx: Context):
    """Show the current and upcoming events."""
    reported_events = []

    try:
        ongoing_event, *_ = await Storage.get_ongoing_events()
    except ValueError:
        pass
    else:
        await send_embed_message(
            ctx,
            title="Ongoing Event!",
            description=textwrap.dedent(f"""\
                Event name: **{ongoing_event.event_name}**
                Poms goal:  **{ongoing_event.pom_goal}**

                Started:  *{ongoing_event.start_date.strftime("%B %d, %Y")}*
                Ending:   *{ongoing_event.end_date.strftime("%B %d, %Y")}*
            """),
        )

        reported_events.append(ongoing_event)

    all_events = await Storage.get_all_events()

    try:
        upcoming_event, *_ = [
            event for event in all_events
            if event.start_date > datetime.now()
        ]
    except ValueError:
        pass
    else:
        await send_embed_message(
            ctx,
            title="Upcoming Event!",
            description=textwrap.dedent(f"""\
                Event name: **{upcoming_event.event_name}**
                Poms goal:  **{upcoming_event.pom_goal}**

                Starts:  *{upcoming_event.start_date.strftime("%B %d, %Y")}*
                Ends:    *{upcoming_event.end_date.strftime("%B %d, %Y")}*
            """),
        )

        reported_events.append(upcoming_event)

    if not any(reported_events):
        await send_embed_message(
            ctx,
            title="Events!",
            description="No ongoing or upcoming events :confused:",
        )
