import os
import textwrap
from collections import Counter
from datetime import datetime
from typing import List

from discord.ext.commands import Context

from pombot.config import Debug, Reactions
from pombot.lib.messages import send_embed_message
from pombot.lib.storage import Storage
from pombot.lib.types import Pom


def _get_duration_message(user_poms: List[Pom]) -> str:
    """Return how long the user has been in their current session as a
    user-facing string.
    """
    if not user_poms:
        return "Not started yet"

    delta = datetime.now() - user_poms[0].time_set
    values = {}

    values["d"]    = delta.days
    values["h"], _ = divmod(delta.seconds, 60 * 60)
    values["m"], _ = divmod(_, 60)

    return "{d} days, {h} hours, {m} minutes".format(**values)


async def do_poms(ctx: Context):
    """Fetch poms for a user and send them a detailed DM."""
    user_poms = await Storage.get_poms(user=ctx.author)
    title = f"Pom statistics for {ctx.author.display_name}"

    if not user_poms:
        await send_embed_message(
            ctx,
            title=title,
            description="You have no tracked poms.",
            private_message=True,
        )
        return

    session_poms = [pom for pom in user_poms if pom.is_current_session()]

    descriptions = [pom.descript for pom in session_poms if pom.descript]
    session_poms_with_description = Counter(descriptions)

    num_session_poms_without_description = len(session_poms) - sum(
        n for n in session_poms_with_description.values())

    await send_embed_message(
        ctx,
        private_message=not Debug.POMS_COMMAND_IS_PUBLIC,
        title=title,
        description=textwrap.dedent(f"""\
            **Pom statistics**
            Session started: *{_get_duration_message(session_poms)}*
            Total poms this session: *{len(session_poms)}*
            Accumulated poms: *{len(user_poms)}*

            **Poms this session**
            {os.linesep.join(f"{desc}: {num}"
                for desc, num in session_poms_with_description.most_common())
                or "*No designated poms*"}
            {f"Undesignated poms: {num_session_poms_without_description}"
                if num_session_poms_without_description
                else "*No undesignated poms*"}
        """),
    )
    await ctx.message.add_reaction(Reactions.CHECKMARK)
