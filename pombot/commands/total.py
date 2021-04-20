from discord.ext.commands import Context

from pombot.config import Reactions
from pombot.lib.storage import Storage
from pombot.lib.types import DateRange


async def do_total(ctx: Context, *args):
    """Count the total poms for all users.

    Usage: !total [<start_month> <start_day> <end_month <end_day>]

    Where:\r
        <start_month>  From this month...\r
        <start_day>    ...And this day,\r
        <end_month>    To this month...\r
        <end_day>      ...And this day.

    Example:\r
        !total \r
        !total january 1 january 31

    The range of dates is optional. When omitted, all poms are counted.
    """
    if args:
        try:
            date_range = DateRange(*args[-4:])
        except ValueError as exc:
            await ctx.reply(exc)
            await ctx.message.add_reaction(Reactions.ROBOT)
            return

        poms = await Storage.get_poms(date_range=date_range)
        msg = f"Total amount of poms in range {date_range}: {len(poms)}"
    else:
        poms = await Storage.get_poms()
        msg = f"Total amount of poms since ever: {len(poms)}"

    await ctx.reply(msg)
