from functools import partial

from discord.ext.commands import Context

from pombot.config import Config, Reactions
from pombot.lib.messages import send_embed_message
from pombot.lib.rename_poms import rename_poms
from pombot.lib.storage import Storage
from pombot.lib.tiny_tools import normalize_and_dedent
from pombot.lib.types import SessionType


async def do_bank(ctx: Context, *args):
    """Bank your poms.

    Your "Bank" is your archive of poms after you've ended a session. This
    command will move the poms in your current session to your bank; You can
    see your bank with !poms.

    Renaming poms:

    Use !bank.rename to redesignate all poms from one description to another.

    !bank.rename readign reading

    This command takes exactly two arguments; if descriptions have spaces,
    then you'll need to enclose them in double quotes, e.g.:

    !bank.rename "sturdy 4 teh fennel" "study for the final"

    Resetting poms:

    Use !bank.reset to reset your bank by deleting all your poms.

    CAUTION: Neither renaming nor resetting can be undone!
    """
    if ctx.invoked_with in Config.RENAME_POMS_IN_BANK:
        try:
            old, new = args
        except ValueError:
            await ctx.author.send(normalize_and_dedent(f"""
                Please specify exactly two descriptions (the old one followed
                by the new one) inside of double quotes. See `!help bank`.
            """))
            await ctx.message.add_reaction(Reactions.ROBOT)
            return

        await rename_poms(ctx, old, new, SessionType.BANKED)
        return

    if ctx.invoked_with in Config.RESET_POMS_IN_BANK:
        await Storage.delete_poms(user=ctx.author, session=SessionType.BANKED)
        await ctx.message.add_reaction(Reactions.WASTEBASKET)
        return

    reply_with_embed = partial(send_embed_message, ctx=None, _func=ctx.reply)

    if num_poms_banked := await Storage.bank_user_session_poms(ctx.author):
        await reply_with_embed(
            title="Poms Banked",
            description="You have successfully banked {n} pom{s}!".format(
                n=num_poms_banked,
                s="s" if num_poms_banked != 1 else "",
            ))
        await ctx.message.add_reaction(Reactions.BANK)
    else:
        await reply_with_embed(
            title="Oops!",
            description="No poms to bank! Start your session by doing your first !pom.")
