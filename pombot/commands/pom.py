from discord.ext.commands import Context

import pombot.lib.errors
from pombot.config import Config, Reactions
from pombot.lib.messages import send_embed_message
from pombot.lib.storage import Storage
from pombot.lib.types import DateRange
from pombot.state import State


async def do_pom(ctx: Context, *description):
    """Add a new pom.

    If the first word in the description is a number (1-10), multiple poms
    will be added with the given description.

    Additionally, find out if there is an ongoing event, and, if so, mark the
    event as completed if this is the final pom in the event.
    """
    description = " ".join(description)
    count = 1

    if description:
        head, *tail = description.split(" ", 1)

        try:
            count = int(head)
        except ValueError:
            pass
        else:
            if not 0 < count <= Config.POM_TRACK_LIMIT:
                await ctx.message.add_reaction(Reactions.WARNING)
                await ctx.send("You can only add between 1 and "
                                f"{Config.POM_TRACK_LIMIT} poms at once.")
                return

            description = " ".join(tail)

        if len(description) > Config.DESCRIPTION_LIMIT:
            await ctx.message.add_reaction(Reactions.WARNING)
            await ctx.send("Your pom description must be fewer than "
                            f"{Config.DESCRIPTION_LIMIT} characters.")
            return

    has_multiline_description = description is not None and "\n" in description

    if has_multiline_description and Config.MULTILINE_DESCRIPTION_DISABLED:
        await ctx.message.add_reaction(Reactions.WARNING)
        await ctx.send("Multi-line pom descriptions are disabled.")
        return

    await Storage.add_poms_to_user_session(ctx.author, description, count)
    await ctx.message.add_reaction(Reactions.TOMATO)

    if State.goal_reached:
        return

    try:
        ongoing_event, *other_ongoing_events = await Storage.get_ongoing_events()
    except ValueError:
        # No ongoing events.
        return

    if any(other_ongoing_events):
        msg = "Only one ongoing event supported."
        raise pombot.lib.errors.TooManyEventsError(msg)

    current_poms_for_event = await Storage.get_poms(date_range=DateRange(
        ongoing_event.start_date, ongoing_event.end_date))

    if len(current_poms_for_event) >= ongoing_event.pom_goal:
        State.goal_reached = True

        await send_embed_message(
            ctx,
            title=ongoing_event.event_name,
            description=(
                f"We've reached our goal of {ongoing_event.pom_goal} poms! "
                "Well done and keep up the good work!"),
        )
