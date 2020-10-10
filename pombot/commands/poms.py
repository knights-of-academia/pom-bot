import os
import textwrap
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import List

import mysql.connector
from discord.embeds import Embed
from discord.ext.commands import Context

from pombot.config import Reactions, Secrets
from pombot.storage import PomSql

EMBED_COLOUR = 0xff6347


@dataclass
class Pom:
    """A pom."""
    pom_id: int
    user_id: int
    descript: str
    time_set: datetime
    session: int

    def is_current_session(self) -> bool:
        """Return whether this pom is in the user's current session."""
        return bool(self.session)


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


async def poms_handler(ctx: Context):
    """Give the user an overview of their poms."""
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
        pom for pom in [Pom(*pom) for pom in poms] if pom.is_current_session()
    ]

    session_described_poms = Counter(
        des_pom.descript
        for des_pom in [pom for pom in session_poms if pom.descript])

    message = Embed(colour=EMBED_COLOUR,
                    description=textwrap.dedent(f"""\
        **Pom statistics**
        Session started: *{_get_duration_message(session_poms)}*
        Total poms this session: *{len(session_poms)}*
        Accumulated poms: *{len(poms)}*

        **Designated poms this session**
        {os.linesep.join(f"{desc}: {num}"
            for desc, num in session_described_poms.most_common()) or "None"}

        **Undesignated poms**
        {len(session_poms) - sum(n for n in session_described_poms.values())}
    """)).set_author(name=f"Pom statistics for {ctx.author.display_name}",
                     icon_url="https://i.imgur.com/qRoH5B5.png")

    await ctx.author.send(embed=message)
    await ctx.send("I've sent you a DM with your poms")
