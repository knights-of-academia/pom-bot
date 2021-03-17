import textwrap

from discord.ext.commands import Context

from pombot.config import Reactions
from pombot.lib.storage import Storage
from pombot.lib.tiny_tools import get_default_usage_header
from pombot.lib.types import DateRange


async def do_total(ctx: Context, *args):
    """Count the total poms for all users.

    Optionally accepts a range of dates. If no range of dates is given, all
    poms are tallied.

    This is an admin-only command.
    """
    def _usage(header: str = None):
        cmd = ctx.prefix + ctx.invoked_with
        header = header or get_default_usage_header(cmd, args)

        return textwrap.dedent(f"""\
            {header}
            ```text
            Usage: {cmd} [<start_month> <start_day> <end_month <end_day>]

            Where:
                <start_month>  From this month...
                <start_day>    ...And this day,
                <end_month>    To this month...
                <end_day>      ...And this day.

            Example:
                {cmd}

                {cmd} january 1 january 31

                If no range of dates is given, all poms are tallied.
            ```
        """)

    if args:
        try:
            date_range = DateRange(*args[-4:])
        except ValueError as exc:
            await ctx.message.add_reaction(Reactions.ROBOT)
            await ctx.author.send(_usage(header=exc))
            return

        poms = await Storage.get_poms(date_range=date_range)
        msg = f"Total amount of poms in range {date_range}: {len(poms)}"
    else:
        poms = await Storage.get_poms()
        msg = f"Total amount of poms since ever: {len(poms)}"

    await ctx.send(msg)
