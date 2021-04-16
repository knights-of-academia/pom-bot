from aiomysql import DataError
from discord.ext.commands import Context

from pombot.config import Config, Reactions
from pombot.lib.storage import Storage
from pombot.lib.tiny_tools import normalize_and_dedent
from pombot.lib.types import SessionType


async def rename_poms(ctx: Context, old: str, new: str, session_type: SessionType) -> int:
    """Rename a user's poms.

    @param ctx The context passed by discord.
    @param old Current description in the session.
    @param new New description in the session.
    @param session_type The type of session to affect.
    @return Number of rows changed.
    """
    session_poms_only = session_type == SessionType.CURRENT
    banked_poms_only = session_type == SessionType.BANKED

    try:
        changed = await Storage.update_user_poms_descriptions(
            ctx.author,
            old,
            new,
            session_poms_only=session_poms_only,
            banked_poms_only=banked_poms_only,
        )
    except DataError as exc:
        if "Data too long" not in exc.args[1]:
            raise

        await ctx.author.send(normalize_and_dedent(f"""
            New description is too long: "{new}" ({len(new)} of
            {Config.DESCRIPTION_LIMIT} character maximum).
        """))
        await ctx.message.add_reaction(Reactions.ROBOT)
        return 0

    if not changed:
        await ctx.author.send(normalize_and_dedent(f"""
            No poms found matching "{old}" in your bank.
        """))
        await ctx.message.add_reaction(Reactions.ROBOT)

    await ctx.message.add_reaction(Reactions.CHECKMARK)
    return changed
