import os
import textwrap
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import List

import mysql.connector
from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.bot import Bot

from pombot.config import Config, Reactions, Secrets
from pombot.state import State
from pombot.storage import EventSql, PomSql


@dataclass
class _Pom:
    """A pom, as described in order from the database."""
    pom_id: int
    user_id: int
    descript: str
    time_set: datetime
    session: int

    def is_current_session(self) -> bool:
        """Return whether this pom is in the user's current session."""
        return bool(self.session)


def _get_duration_message(poms: List[_Pom]) -> str:
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

        if cursor.rowcount > 0:
            cursor.execute(PomSql.EVENT_SELECT, (event_start, event_end))
            cursor.fetchall()
            poms = cursor.rowcount
            cursor.close()
            db.close()

            if State.goal_reached:
                return

            if event_goal <= poms:
                State.goal_reached = True

                embed_kwargs = {
                    "colour": Config.EMBED_COLOUR,
                    "description":
                        (f"We've reached our goal of {event_goal} "
                         "poms! Well done and keep up the good work!"),
                }

                author_kwargs = {
                    "name": event_name,
                    "icon_url": Config.EMBED_IMAGE_URL,
                }

                message = Embed(**embed_kwargs).set_author(**author_kwargs)
                await ctx.send(embed=message)

    @commands.command()
    async def poms(self, ctx: Context):
        """Show your poms.

        See details for your tracked poms and the current session.
        """
        db = mysql.connector.connect(
            host=Secrets.MYSQL_HOST,
            user=Secrets.MYSQL_USER,
            database=Secrets.MYSQL_DATABASE,
            password=Secrets.MYSQL_PASSWORD,
        )
        cursor = db.cursor(buffered=True)
        cursor.execute(PomSql.SELECT_ALL_POMS, (ctx.message.author.id, ))
        poms = cursor.fetchall()
        cursor.close()
        db.close()

        if not poms:
            await ctx.message.add_reaction(Reactions.WARNING)
            await ctx.send("You have no tracked poms.")
            return

        session_poms = [
            pom for pom in [_Pom(*pom) for pom in poms] if pom.is_current_session()
        ]

        session_described_poms = Counter(
            des_pom.descript
            for des_pom in [pom for pom in session_poms if pom.descript])

        message = Embed(colour=Config.EMBED_COLOUR,
                        description=textwrap.dedent(f"""\
            **Pom statistics**
            Session started: *{_get_duration_message(session_poms)}*
            Total poms this session: *{len(session_poms)}*
            Accumulated poms: *{len(poms)}*

            **Poms this session**
            {os.linesep.join(f"{desc}: {num}"
                for desc, num in session_described_poms.most_common())
                or "*No designated poms*"}
            Undesignated poms: {len(session_poms) - sum(
                n for n in session_described_poms.values())}
        """)).set_author(name=f"Pom statistics for {ctx.author.display_name}",
                         icon_url=Config.EMBED_IMAGE_URL)

        await ctx.author.send(embed=message)
        await ctx.send("I've sent you a DM with your poms")

    @commands.command()
    async def howmany(self, ctx: Context, *, description: str = None):
        """List your poms with a given description."""
        if description is None:
            await ctx.message.add_reaction(Reactions.WARNING)
            await ctx.send("You must specify a description to search for.")
            return

        db = mysql.connector.connect(
            host=Secrets.MYSQL_HOST,
            user=Secrets.MYSQL_USER,
            database=Secrets.MYSQL_DATABASE,
            password=Secrets.MYSQL_PASSWORD,
        )
        cursor = db.cursor(buffered=True)

        cursor.execute(PomSql.SELECT_ALL_POMS_WITH_DESCRIPT,
                       (ctx.message.author.id, description))
        poms = cursor.fetchall()
        cursor.close()
        db.close()

        if not poms:
            await ctx.message.add_reaction(Reactions.WARNING)
            await ctx.send("You have no tracked poms with that description.")
            return

        await ctx.message.add_reaction(Reactions.ABACUS)
        await ctx.send('You have {num_poms} *"{description}"* pom{s}.'.format(
            num_poms=len(poms),
            description=description,
            s="" if len(poms) == 1 else "s",
        ))

    @commands.command()
    async def undo(self, ctx: Context, *, description: str = None):
        """Undo/remove your latest poms.

        Optionally specify a number to undo that many poms.
        """
        count = 1

        db = mysql.connector.connect(
            host=Secrets.MYSQL_HOST,
            user=Secrets.MYSQL_USER,
            database=Secrets.MYSQL_DATABASE,
            password=Secrets.MYSQL_PASSWORD,
        )
        cursor = db.cursor(buffered=True)

        if description:
            first_word, *_ = description.split(' ', 1)

            try:
                count = int(first_word)
            except ValueError:
                msg = f'Please specify a number of poms to undo.'

                await ctx.message.add_reaction(Reactions.WARNING)
                await ctx.send(msg)
                cursor.close()
                db.close()
                return

            if count > Config.POM_TRACK_LIMIT:
                msg = f"You can only undo up to {Config.POM_TRACK_LIMIT} poms at once."

                await ctx.message.add_reaction(Reactions.WARNING)
                await ctx.send(msg)
                cursor.close()
                db.close()
                return

        cursor.execute(PomSql.SELECT_ALL_POMS_WITH_LIMIT,
                       (ctx.message.author.id, count))

        cursor.executemany(PomSql.DELETE_POMS_WITH_ID,
                           [(ctx.message.author.id, pom_id)
                            for pom_id, *_ in cursor.fetchall()])
        db.commit()

        await ctx.message.add_reaction(Reactions.UNDO)
        cursor.close()
        db.close()

    @commands.command()
    async def newleaf(self, ctx: Context):
        """Turn over a new leaf.

        Hide the details of your previously tracked poms and start a new
        session.
        """
        db = mysql.connector.connect(
            host=Secrets.MYSQL_HOST,
            user=Secrets.MYSQL_USER,
            database=Secrets.MYSQL_DATABASE,
            password=Secrets.MYSQL_PASSWORD,
        )
        cursor = db.cursor(buffered=True)
        cursor.execute(PomSql.SELECT_ALL_POMS_CURRENT_SESSION,
                       (ctx.message.author.id, ))

        no_poms_msg = ("A new session will be started when you track your "
                       f"next pom, {ctx.author.display_name}")

        num_poms = len(cursor.fetchall())
        if num_poms == 0:
            cursor.close()
            db.close()

            await ctx.message.add_reaction(Reactions.FALLEN_LEAF)
            await ctx.send(no_poms_msg)
            return

        cursor.execute(PomSql.UPDATE_REMOVE_ALL_POMS_FROM_SESSION,
                       (ctx.message.author.id, ))
        db.commit()

        await ctx.send(no_poms_msg)
        await ctx.message.add_reaction(Reactions.LEAVES)

        cursor.close()
        db.close()


    @commands.command(hidden=True)
    async def reset(self, ctx: Context):
        """Permanently deletes all of your poms. This cannot be undone."""
        db = mysql.connector.connect(
            host=Secrets.MYSQL_HOST,
            user=Secrets.MYSQL_USER,
            database=Secrets.MYSQL_DATABASE,
            password=Secrets.MYSQL_PASSWORD,
        )
        cursor = db.cursor(buffered=True)

        cursor.execute(PomSql.DELETE_POMS, (ctx.message.author.id,))

        db.commit()
        cursor.close()
        db.close()

        await ctx.message.add_reaction(Reactions.WASTEBASKET)


def setup(bot: Bot):
    """Required to load extention."""
    bot.add_cog(UserCommands(bot))
