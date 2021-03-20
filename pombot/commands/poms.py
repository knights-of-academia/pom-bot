import textwrap
from collections import Counter
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional

from discord.ext.commands import Context

from pombot.config import Config, Debug, Reactions
from pombot.lib.messages import EmbedField, send_embed_message
from pombot.lib.storage import Storage
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

    response_is_public = ctx.invoked_with in Config.PUBLIC_POMS_ALIASES

    # FIXME for !howmany-style args, this doesn't need to return all poms.
    # FIXME for public command, this could retun only current session poms.
    poms = await Storage.get_poms(user=ctx.author)

    banked_session = _Session(
        session_type=_SessionType.BANKED,
        poms=[p for p in poms if not p.is_current_session()],
        public_response=response_is_public,
    )

    current_session = _Session(
        session_type=_SessionType.CURRENT,
        poms=[p for p in poms if p.is_current_session()],
        public_response=response_is_public,
    )

    if response_is_public:
        await send_embed_message(
            None,
            title=f"Pom statistics for {ctx.author.display_name}",
            icon_url=ctx.author.avatar_url,
            fields=[current_session.get_message_field()],
            description=current_session.get_session_started_message(),
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
            description=current_session.get_session_started_message(),
            footer="\n".join([
                "Total time spent pomming: {}".format(
                    _dynamic_duration(
                        len(banked_session + current_session) * Config.POM_LENGTH)),
                current_session.get_duration_message(),
            ]),
            _func=(ctx.send
                   if Debug.POMS_COMMAND_IS_PUBLIC else ctx.author.send),
        )
        await ctx.message.add_reaction(Reactions.CHECKMARK)


class _SessionType(str, Enum):
    BANKED = "Banked Poms"
    CURRENT = "Current Session"
    COMBINED = "Combined"


class _Session:
    """Represent the entire "session" of a series of poms by type.

    There are effectively two different durations of sessions according to
    the `poms` table: those that are in the current session and those that
    are not. This class builds and returns messages for either given a type
    and an iterator.
    """
    def __init__(
        self,
        *,
        session_type: _SessionType,
        poms: List[Pom],
        public_response: bool,
    ):
        self.type = session_type
        self.poms = sorted(poms)
        self._public = public_response

    def __len__(self):
        return len(self.poms)

    def __add__(self, other):
        if not isinstance(other, self.__class__):
            raise NotImplementedError(f"Cannot add {type(other)}")

        return self.__class__(
            session_type=_SessionType.COMBINED,
            poms=self.poms + other.poms,
            public_response=self._public,
        )

    def get_message_field(self) -> EmbedField:
        """Get the stats of this session as an EmbedField."""
        pom_counts = Counter(pom.descript for pom in self.poms)

        designated_poms = [f"{k}: *{v}*" for k, v in pom_counts.most_common() if k is not None]
        num_undesignated_poms = pom_counts.get(None) or 0

        if designated_lines := designated_poms:
            designated_lines += [ZERO_WIDTH_SPACE]
        else:
            designated_lines = ["*No designated poms!*", ""]

        if not designated_poms and num_undesignated_poms == 0:
            if self.type == _SessionType.BANKED:
                detail_lines = [textwrap.dedent("""\
                    Banking your poms in
                    your current session
                    will add them here!
                """)]
            else:
                detail_lines = [textwrap.dedent("""\
                    Start your session by
                    doing your first !pom
                """)]
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
        """Return the time spent pomming this session as a dynamic string."""
        return "Time this session: {}".format(
            _dynamic_duration(len(self.poms) * Config.POM_LENGTH))

    def get_session_started_message(self) -> Optional[str]:
        """Return a user-facing timestamp of when this session started, or
        None if the message will eventually be publicly-visible.
        """
        if self._public:
            return None

        if not self.poms:
            return "*Session not yet started.*"

        return "Current session started {}".format(
            self.poms[0].time_set.strftime("%B %d, %Y (%H:%M UTC)"))


def _dynamic_duration(delta: timedelta) -> str:
    days       = delta.days
    hours, _   = divmod(delta.seconds, 60 * 60)
    minutes, _ = divmod(_, 60)

    parts = [f"{minutes} minutes"]

    if delta >= timedelta(minutes=60):
        s = "s" if hours != 1 else ""
        parts = [f"{hours} hour{s}", *parts]

    if delta >= timedelta(hours=24):
        s = "s" if days != 1 else ""
        parts = [f"{days:,} day{s}", *parts]

    return ", ".join(parts)
