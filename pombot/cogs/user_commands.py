import os
import textwrap
from collections import Counter
from datetime import datetime
from typing import List

from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.bot import Bot

import pombot.errors
from pombot.config import Config, Reactions
from pombot.lib.messages import send_embed_message
from pombot.state import State
from pombot.storage import Storage
from pombot.lib.types import DateRange, Pom


def _get_duration_message(poms: List[Pom]) -> str:
    """Return how long the user has been in the current pom."""
    if not poms:
        return "Not started yet"

    delta = datetime.now() - poms[0].time_set
    values = {}

    values["d"] = delta.days
    values["h"], _ = divmod(delta.seconds, 60 * 60)
    values["m"], _ = divmod(_, 60)

    return "{d} days, {h} hours, {m} minutes".format(**values)


class UserCommands(commands.Cog):
    """Handlers for user-level pom commands."""
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def pom(self, ctx: Context, *, description: str = None):
        """Add a new pom.

        If the first word in the description is a number (1-10), multiple
        poms will be added with the given description.

        Additionally, find out if there is an ongoing event, and, if so, mark
        the event as completed if this is the final pom in the event.
        """
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
            raise pombot.errors.TooManyEventsError(msg)

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

    @commands.command()
    async def poms(self, ctx: Context):
        """Show your poms.

        See details for your tracked poms and the current session.
        """
        poms = await Storage.get_poms(user=ctx.author)
        title = f"Pom statistics for {ctx.author.display_name}"

        if not poms:
            await send_embed_message(
                ctx,
                title=title,
                description="You have no tracked poms.",
                private_message=True,
            )
            return

        session_poms = [pom for pom in poms if pom.is_current_session()]

        descriptions = [pom.descript for pom in session_poms if pom.descript]
        session_poms_with_description = Counter(descriptions)

        num_session_poms_without_description = len(session_poms) - sum(
            n for n in session_poms_with_description.values())

        await send_embed_message(
            ctx,
            private_message=True,
            title=title,
            description=textwrap.dedent(f"""\
                **Pom statistics**
                Session started: *{_get_duration_message(session_poms)}*
                Total poms this session: *{len(session_poms)}*
                Accumulated poms: *{len(poms)}*

                **Poms this session**
                {os.linesep.join(f"{desc}: {num}"
                    for desc, num in session_poms_with_description.most_common())
                    or "*No designated poms*"}
                {f"Undesignated poms: {num_session_poms_without_description}"
                    if num_session_poms_without_description
                    else "*No undesignated poms*"}
            """),
        )

    @commands.command()
    async def howmany(self, ctx: Context, *, description: str = None):
        """List your poms with a given description."""
        if description is None:
            await ctx.message.add_reaction(Reactions.WARNING)
            await ctx.send("You must specify a description to search for.")
            return

        poms = await Storage.get_poms(user=ctx.author)
        matching_poms = [pom for pom in poms if pom.descript == description]

        if not matching_poms:
            await ctx.message.add_reaction(Reactions.WARNING)
            await ctx.send("You have no tracked poms with that description.")
            return

        await ctx.message.add_reaction(Reactions.ABACUS)
        await ctx.send('You have {num_poms} *"{description}"* pom{s}.'.format(
            num_poms=len(matching_poms),
            description=description,
            s="" if len(matching_poms) == 1 else "s",
        ))

    @commands.command()
    async def undo(self, ctx: Context, *, count: str = None):
        """Undo/remove your latest poms.

        Optionally specify a number to undo that many poms.
        """
        _count = 1

        if count:
            first_word, *_ = count.split(" ", 1)

            try:
                _count = int(first_word)
            except ValueError:
                await ctx.message.add_reaction(Reactions.WARNING)
                await ctx.send(f"Please specify a number of poms to undo.")
                return

            if not 0 < _count <= Config.POM_TRACK_LIMIT:
                await ctx.message.add_reaction(Reactions.WARNING)
                await ctx.send("You can only undo between 1 and "
                               f"{Config.POM_TRACK_LIMIT} poms at once.")
                return

        await Storage.delete_most_recent_user_poms(ctx.author, _count)
        await ctx.message.add_reaction(Reactions.UNDO)

    @commands.command()
    async def newleaf(self, ctx: Context):
        """Turn over a new leaf.

        Hide the details of your previously tracked poms and start a new
        session.
        """
        await Storage.clear_user_session_poms(ctx.author)

        await ctx.send("A new session will be started when you track your "
                       f"next pom, <@!{ctx.author.id}>")
        await ctx.message.add_reaction(Reactions.LEAVES)

    @commands.command(hidden=True)
    async def reset(self, ctx: Context):
        """Permanently deletes all of your poms. This cannot be undone."""
        await Storage.delete_all_user_poms(ctx.author)
        await ctx.message.add_reaction(Reactions.WASTEBASKET)

    @commands.command()
    async def events(self, ctx: Context):
        """See the current and next events."""
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


def setup(bot: Bot):
    """Required to load extension."""
    bot.add_cog(UserCommands(bot))
