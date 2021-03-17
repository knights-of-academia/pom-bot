import textwrap
from collections import Counter
from datetime import datetime, timedelta
from enum import Enum
from typing import List

from discord.ext.commands import Context

from pombot.config import Config, Debug, Reactions
from pombot.lib.messages import EmbedField, send_embed_message
from pombot.lib.storage import Storage
from pombot.lib.tiny_tools import normalize_newlines
from pombot.lib.types import Pom

ZERO_WIDTH_SPACE = "\u200b"
LIGHT_HORIZONTAL = "\u2500"

TOTALS_SEPARATOR = LIGHT_HORIZONTAL * 12


async def do_poms(ctx: Context):
    """See your banked poms and your current session.

    Receive a DM of your banked poms and the poms in your current session in
    separate lists, organized by the number of poms of any particular
    description.

    You can also share the details of your current session by typing:
    "!poms.show" (without quotes).
    """
    # FIXME remember to add session goal info to current seesion message

    # FIXME for !howmany-style args, this doesn't need to return all poms.
    # FIXME for public command, this could retun only current session poms.
    poms = await Storage.get_poms(user=ctx.author)

    banked_session, current_session = (
        _Session(_SessionType.BANKED, [p for p in poms if not p.is_current_session()]),
        _Session(_SessionType.CURRENT, [p for p in poms if p.is_current_session()]),
    )

    response_is_public = ctx.invoked_with in Config.PUBLIC_POMS_ALIASES

    if response_is_public:
        await send_embed_message(
            None,
            title=f"Pom statistics for {ctx.author.display_name}",
            icon_url=ctx.author.avatar_url,
            fields=[current_session.get_message_field()],
            description=ZERO_WIDTH_SPACE,
            footer=current_session.get_duration_message(),
            _func=ctx.message.reply,
        )
    else:
        # This spacer ensures there is no irregular spacing on desktop screens,
        # but at least one normal-height separation on mobile screens.
        spacer = EmbedField(name=ZERO_WIDTH_SPACE, value=ZERO_WIDTH_SPACE)

        await send_embed_message(
            None,
            title=f"Your pom statistics",
            icon_url=Config.EMBED_IMAGE_URL,
            fields=[
                banked_session.get_message_field(),
                spacer,
                current_session.get_message_field(),
            ],
            description=ZERO_WIDTH_SPACE,
            footer=current_session.get_duration_message(),
            _func=(ctx.send if Debug.POMS_COMMAND_IS_PUBLIC else ctx.author.send),
        )
        await ctx.message.add_reaction(Reactions.CHECKMARK)


class _SessionType(str, Enum):
    BANKED = "Banked Poms"
    CURRENT = "Current Session"


class _Session:
    """Represent the entire "session" of a series of poms by type.

    There are effectively two different durations of sessions according to
    the `poms` table: those that are in the current session and those that
    are not. This class builds and returns messages for either given a type
    and an iterator.
    """
    def __init__(self, session_type: _SessionType, poms: List[Pom]):
        self.type = session_type
        self.poms = poms

    def get_message_field(self) -> EmbedField:
        """Get the stats of this session as an EmbedField tuple."""
        pom_counts = Counter(pom.descript for pom in self.poms)

        designated_poms = [f"{k}: *{v}*" for k, v in pom_counts.most_common() if k is not None]
        num_undesignated_poms = pom_counts.get(None) or 0

        if designated_lines := designated_poms:
            designated_lines += [ZERO_WIDTH_SPACE]
        else:
            designated_lines = ["*No designated poms!*", ""]

        if not designated_poms and num_undesignated_poms == 0:
            if self.type == _SessionType.BANKED:
                detail_lines = [normalize_newlines(textwrap.dedent("""\
                    After you bank poms in your current session, they will be
                    added here.
                """))]
            else:
                detail_lines = [normalize_newlines(textwrap.dedent("""\
                    Start your session by doing your first !pom
                """))]
        else:
            detail_lines = [
                *designated_lines,
                f"*Undesignated*: *{num_undesignated_poms}*",
                TOTALS_SEPARATOR,
                f"Total: *{len(self.poms)}*\n",
            ]

        return EmbedField(
            name=f"**{self.type}**",
            value="\n".join(detail_lines)
        )

    def get_duration_message(self) -> str:
        """Return the length of this session as a string."""
        if not self.poms:
            return "Start your session with !pom"

        # NOTE: This assumes self.poms is sorted by either ID or timestamp.
        delta = datetime.now() - self.poms[0].time_set

        days       = delta.days
        hours, _   = divmod(delta.seconds, 60 * 60)
        minutes, _ = divmod(_, 60)

        parts = [f"{minutes} minutes"]

        if delta >= timedelta(minutes=60):
            s = "s" if hours != 1 else ""
            parts = [f"{hours} hour{s}", *parts]

        if delta >= timedelta(hours=24):
            s = "s" if days != 1 else ""
            parts = [f"{days} day{s}", *parts]

        return "Time this session: {}".format(", ".join(parts))
