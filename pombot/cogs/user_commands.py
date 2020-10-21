import os
import textwrap
from collections import Counter
from datetime import datetime
from typing import List

import mysql.connector
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.bot import Bot

from pombot.config import Config, Reactions, Secrets
from pombot.lib.embeds import send_embed_message
from pombot.state import State
from pombot.storage import EventSql, PomSql, Storage, Pom


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
        """
        #FIXME you are here
        pom_count = 1
        current_date = datetime.now()

        db = mysql.connector.connect(
            host=Secrets.MYSQL_HOST,
            user=Secrets.MYSQL_USER,
            database=Secrets.MYSQL_DATABASE,
            password=Secrets.MYSQL_PASSWORD,
        )
        cursor = db.cursor(buffered=True)

        if description:
            # If there is a description, check if the first word is a digit. If
            # it is, split the string to remove the digits length plus 1 for
            # space.
            if description.split(' ', 1)[0].isdigit():
                pom_count = int(description.split(' ', 1)[0])
                if pom_count > Config.POM_TRACK_LIMIT or pom_count < 1:
                    await ctx.message.add_reaction(Reactions.WARNING)
                    await ctx.send('You can only add between 1 and 10 poms at once.')
                    cursor.close()
                    db.close()
                    return

                description = description[(len(str(pom_count)) + 1):]

        if description is not None and len(description) > Config.DESCRIPTION_LIMIT:
            await ctx.message.add_reaction(Reactions.WARNING)
            await ctx.send('Your pom description must be fewer than 30 characters.')
            cursor.close()
            db.close()
            return

        has_multiline_description = description is not None and "\n" in description

        if  has_multiline_description and Config.MULTILINE_DESCRIPTION_DISABLED:
            await ctx.message.add_reaction(Reactions.WARNING)
            await ctx.send('Multi line pom descriptions are disabled.')
            cursor.close()
            db.close()
            return

        poms = [(
            ctx.message.author.id,
            description,
            current_date.strftime('%Y-%m-%d) %H:%M:%S'),
            True,
        ) for _ in range(pom_count)]

        cursor.executemany(PomSql.INSERT_QUERY, poms)

        db.commit()

        await ctx.message.add_reaction(Reactions.TOMATO)

        cursor.execute(EventSql.SELECT_EVENT, (current_date, current_date))
        event_info = cursor.fetchall()

        try:
            _, event_name, event_goal, event_start, event_end = event_info[0]
        except IndexError:
            # No event for current_date.
            cursor.close()
            db.close()
            return

        cursor.execute(PomSql.EVENT_SELECT, (event_start, event_end))
        cursor.fetchall()
        poms = cursor.rowcount
        cursor.close()
        db.close()

        if State.goal_reached:
            return

        if event_goal <= poms:
            State.goal_reached = True

            await send_embed_message(
                ctx,
                title=event_name,
                description=(f"We've reached our goal of {event_goal} "
                             "poms! Well done and keep up the good work!"),
            )

    @commands.command()
    async def poms(self, ctx: Context):
        """Show your poms.

        See details for your tracked poms and the current session.
        """
        poms = Storage.get_all_poms_for_user(ctx.author)
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

        poms = Storage.get_all_poms_for_user(ctx.author)
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

        Storage.delete_most_recent_user_poms(ctx.author, _count)
        await ctx.message.add_reaction(Reactions.UNDO)

    @commands.command()
    async def newleaf(self, ctx: Context):
        """Turn over a new leaf.

        Hide the details of your previously tracked poms and start a new
        session.
        """
        Storage.clear_user_session_poms(ctx.author)

        await ctx.send("A new session will be started when you track your "
                       f"next pom, <@!{ctx.author.id}>")
        await ctx.message.add_reaction(Reactions.LEAVES)


    @commands.command(hidden=True)
    async def reset(self, ctx: Context):
        """Permanently deletes all of your poms. This cannot be undone."""
        Storage.delete_all_user_poms(ctx.author)
        await ctx.message.add_reaction(Reactions.WASTEBASKET)


def setup(bot: Bot):
    """Required to load extension."""
    bot.add_cog(UserCommands(bot))
