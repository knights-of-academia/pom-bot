from datetime import datetime, timedelta

import discord.errors
from discord.ext.commands import Context

from pombot.config import Debug, IconUrls, Pomwars, Reactions
from pombot.lib.messages import send_embed_message
from pombot.lib.storage import Storage
from pombot.lib.types import DateRange


async def do_actions(ctx: Context, *args):
    """See your actions."""
    date_range = None
    today = datetime.today().strftime("%B %d").split()
    yesterday = (datetime.today() -
                 timedelta(days=1)).strftime("%B %d").split()

    descriptive_dates = {
        "today": DateRange(*today, *today),
        "yesterday": DateRange(*yesterday, *yesterday)
    }

    if args:
        date_range = descriptive_dates.get(args[0].casefold())

    if date_range is None:
        try:
            date_range = DateRange(*args, *args)
        except ValueError:
            today = datetime.today()
            date_range = descriptive_dates["today"]

    actions = await Storage.get_actions(user=ctx.author, date_range=date_range)

    if not actions:
        description = "*No recorded actions.*"
    else:
        descripts = []

        nrm = [a for a in actions if a.is_normal]
        nrmx = [a for a in nrm if not a.was_successful]
        descripts.append("Normal attacks: {}{}".format(
            len(nrm), f" (missed {len(nrmx)})" if nrmx else "") if nrm else "")

        hvy = [a for a in actions if a.is_heavy]
        hvyx = [a for a in hvy if not a.was_successful]
        descripts.append("Heavy attacks: {}{}".format(
            len(hvy), f" (missed {len(hvyx)})" if hvyx else "") if hvy else "")

        dfn = [a for a in actions if a.is_defend]
        dfnx = [a for a in dfn if not a.was_successful]
        descripts.append("Defends: {}{}".format(
            len(dfn), f" (missed {len(dfnx)})" if dfnx else "") if dfn else "")

        descripts.append(" ")  # &nbsp;

        total = len(actions)
        tot_emote = Reactions.TOMATO
        descripts.append(f"Total poms:  {tot_emote}  _{total}_")

        damage = sum([a.damage for a in actions if a.damage])
        dam_emote = Reactions.CROSSED_SWORDS
        descripts.append(f"Damage dealt:  {dam_emote}  _**{damage:.2f}**_")

        description = "\n".join(d for d in descripts if d)

    try:
        await send_embed_message(
            ctx,
            title=f"Actions for {date_range}",
            description=description,
            thumbnail=IconUrls.ATTACK,
            colour=Pomwars.ACTION_COLOUR,
            private_message=not Debug.POMS_COMMAND_IS_PUBLIC,
        )
        await ctx.message.add_reaction(Reactions.CHECKMARK)
    except discord.errors.Forbidden:
        # User disallows DM's from server members.
        await ctx.message.add_reaction(Reactions.WARNING)
