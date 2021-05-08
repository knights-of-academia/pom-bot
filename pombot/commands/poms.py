import textwrap
from collections import Counter
from datetime import timedelta
from functools import partial
from typing import Iterator, List, Optional

from discord.ext.commands import Context
from discord.errors import HTTPException

from pombot.config import Config, Debug, Reactions
from pombot.data import Limits
from pombot.lib.messages import EmbedField, send_embed_message
from pombot.lib.rename_poms import rename_poms
from pombot.lib.storage import Storage
from pombot.lib.tiny_tools import normalize_and_dedent
from pombot.lib.types import Pom, SessionType

ZERO_WIDTH_SPACE = "\u200b"
LIGHT_HORIZONTAL = "\u2500"

TOTALS_SEPARATOR = LIGHT_HORIZONTAL * 12

# This spacer ensures there is no irregular spacing on desktop screens, but at
# least one normal-height separation on mobile screens.
SPACER = EmbedField(name=ZERO_WIDTH_SPACE, value=ZERO_WIDTH_SPACE)


async def do_poms(ctx: Context, *args):
    """See the poms in your bank and current session.

    Receive a DM of your banked poms and the poms in your current session in
    separate lists, organized by the number of poms of any particular
    description. You can also share the details of your current session by
    typing: "!poms.show" (without quotes).

    To see only poms of a certain description, specify the description:

    !poms reading

    Or show them publicly:

    !poms.show reading

    Renaming poms:

    Use !poms.rename to redesignate all poms from one description to another.

    !poms.rename readign reading

    This command takes exactly two arguments; if descriptions have spaces,
    then you'll need to enclose them in double quotes, e.g.:

    !poms.rename "sturdy 4 teh fennel" "study for the final"

    Resetting poms:

    Use !poms.reset to reset your current session by deleting all your poms.

    CAUTION: Neither renaming nor resetting can be undone!
    """
    if ctx.invoked_with in Config.RENAME_POMS_IN_SESSION:
        try:
            old, new = args
        except ValueError:
            await ctx.author.send(normalize_and_dedent("""\
                Please specify exactly two descriptions (the old one followed
                by the new one) inside of double quotes. See `!help poms`.
            """))
            await ctx.message.add_reaction(Reactions.ROBOT)

        await rename_poms(ctx, old, new, SessionType.CURRENT)
        return

    if ctx.invoked_with in Config.RESET_POMS_IN_SESSION:
        await Storage.delete_poms(user=ctx.author, session=SessionType.CURRENT)
        await ctx.message.add_reaction(Reactions.WASTEBASKET)
        return

    description = " ".join(args)
    poms = await Storage.get_poms(user=ctx.author, descript=description)

    response_is_public = ctx.invoked_with in Config.PUBLIC_POMS_ALIASES

    session = partial(_Session,
                      description=description,
                      public_response=response_is_public)

    banked_session = session(
        session_type=SessionType.BANKED,
        poms=[p for p in poms if not p.is_current_session()],
    )

    current_session = session(
        session_type=SessionType.CURRENT,
        poms=[p for p in poms if p.is_current_session()],
    )

    if response_is_public:
        try:
            await send_embed_message(
                None,
                title=f"Pom statistics for {ctx.author.display_name}",
                description=current_session.get_session_started_message(),
                thumbnail=ctx.author.avatar_url,
                fields=[current_session.get_message_field()],
                footer=current_session.get_duration_message(),
                _func=ctx.message.reply)
        except HTTPException:
            await ctx.author.send(normalize_and_dedent("""\
                The combined length of the pom descriptions in your current
                session are over Discord's embed character limit. Use !poms
                (without `.show`) to see them and rename a few.
            """))
            await ctx.message.add_reaction(Reactions.ROBOT)
        return

    if description:
        footer = "Total time spent on {description}: {duration}".format(
            description=description,
            duration=_dynamic_duration(len(poms) * Config.POM_LENGTH))
    else:
        footer = "\n".join([
            "Total time spent pomming: {}".format(
                _dynamic_duration(
                    len(banked_session + current_session) *
                    Config.POM_LENGTH)),
            current_session.get_duration_message(),
        ])

    try:
        await send_embed_message(
            None,
            title=f"Your pom statistics",
            description=current_session.get_session_started_message(),
            thumbnail=ctx.author.avatar_url,
            fields=[
                banked_session.get_message_field(),
                SPACER,
                current_session.get_message_field(),
            ],
            footer=footer,
            _func=(ctx.send if Debug.POMS_COMMAND_IS_PUBLIC else ctx.author.send),
        )
    except HTTPException:
        for session in (current_session, banked_session):
            field = session.get_message_field()

            if len(field.value) <= Limits.MAX_EMBED_FIELD_VALUE:
                await send_embed_message(
                    None,
                    title="Your pom statistics",
                    description=current_session.get_session_started_message(),
                    thumbnail=ctx.author.avatar_url,
                    fields=[session.get_message_field()],
                    footer=footer,
                    _func=ctx.author.send if not Debug.POMS_COMMAND_IS_PUBLIC else ctx.send,
                )
                continue

            message = normalize_and_dedent("""
                ```fix

                The combined length of all the pom descriptions in your
                {session_type} is longer than the maximum embed message field
                size for Discord embeds ({length}, Max is {max_length}). Please
                rename a few with !poms.rename (see !help {cmd}).```
            """.format(
                session_type=session.type.value.lower(),
                length=len(session.get_message_field().value),
                max_length=Limits.MAX_EMBED_FIELD_VALUE,
                cmd="poms" if session.type == SessionType.CURRENT else "bank",
            ))

            await (ctx.author.send(message)
                    if not Debug.POMS_COMMAND_IS_PUBLIC else ctx.send(message))

            for message in session.iter_message_field(
                    max_length=Limits.MAX_CHARACTERS_PER_MESSAGE - 100):
                await (ctx.author.send(message)
                       if not Debug.POMS_COMMAND_IS_PUBLIC else ctx.send(message))

        await ctx.message.add_reaction(Reactions.ROBOT)
    else:
        await ctx.message.add_reaction(Reactions.CHECKMARK)


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
        session_type: SessionType,
        poms: List[Pom],
        description: str,
        public_response: bool,
    ):
        self.type = session_type
        self.poms = sorted(poms)
        self.desc = description
        self.is_public = public_response

    def __len__(self):
        return len(self.poms)

    def __add__(self, other):
        if not isinstance(other, self.__class__):
            raise NotImplementedError(f"Cannot add {type(other)}")

        return self.__class__(
            session_type=SessionType.COMBINED,
            poms=self.poms + other.poms,
            description=self.desc,
            public_response=self.is_public,
        )

    def get_message_field(self) -> EmbedField:
        """Get the stats of this session as an EmbedField."""
        pom_counts = Counter(pom.descript for pom in self.poms)

        designated_poms = [f"{k}: *{v:,}*" for k, v in pom_counts.most_common() if k is not None]
        num_undesignated_poms = pom_counts.get(None) or 0

        if designated_lines := designated_poms:
            if not self.desc:
                designated_lines += [ZERO_WIDTH_SPACE]
        else:
            designated_lines = ["*No designated poms!*", ""]

        if not designated_poms and num_undesignated_poms == 0:
            if self.type == SessionType.BANKED:
                if self.desc:
                    detail_lines = [f"No *{self.desc}* poms!"]
                else:
                    detail_lines = [textwrap.dedent("""\
                        Bank the poms in your current
                        session to add them here!
                    """)]
            else:
                if self.desc:
                    detail_lines = [f"No *{self.desc}* poms!"]
                else:
                    detail_lines = [textwrap.dedent("""\
                        Start your session by doing
                        your first !pom.
                    """)]
        else:
            if self.desc:
                detail_lines = designated_lines
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
        return "Time pommed this session: {}".format(
            _dynamic_duration(len(self.poms) * Config.POM_LENGTH))

    def get_session_started_message(self) -> Optional[str]:
        """Return a user-facing timestamp of when this session started, or
        None if the message will eventually be publicly-visible.
        """
        if self.is_public:
            return None

        if not self.poms:
            return "*Session not yet started.*"

        return "Current session started {}".format(
            self.poms[0].time_set.strftime("%B %d, %Y (%H:%M UTC)"))

    def iter_message_field(self, max_length: int) -> Iterator[str]:
        """Generate the list of poms in the field as a plain string of at most
        `max_length` characters.
        """
        code_block_join = lambda s, n="\n": f"```{n.join(s)}```"
        pom_counts = Counter(pom.descript for pom in self.poms if pom.descript is not None)
        descripts_and_counts: List[str] = []

        for descript in sorted(pom_counts, key=str.casefold):
            count = pom_counts[descript]
            descripts_and_counts += [f"{descript} ({count})"]

            if len(candidate := code_block_join(descripts_and_counts)) < max_length:
                continue

            # Last item put response candidate just over the limit.
            last_item = descripts_and_counts.pop()

            yield code_block_join(descripts_and_counts)

            descripts_and_counts = [last_item]

        # Finally, we need to yield the most recent candidate because the
        # length of an embed field value is probably smaller than `max_length`.
        yield candidate


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
