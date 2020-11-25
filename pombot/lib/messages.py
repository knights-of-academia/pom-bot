from textwrap import indent, dedent

from discord.embeds import Embed
from discord.ext.commands import Context

from pombot.config import Config, Reactions


async def send_embed_message(
        ctx: Context,
        *,
        title: str,
        description: str,
        colour=Config.EMBED_COLOUR,
        icon_url=Config.EMBED_IMAGE_URL,
        private_message: bool = False,
):
    """Send an embedded message using the context."""
    message = Embed(
        description=description,
        colour=colour,
    ).set_author(
        name=title,
        icon_url=icon_url,
    )

    coro = ctx.author.send if private_message else ctx.send
    await coro(embed=message)


async def send_usage_message(ctx: Context, content: str, *, header: str = None) -> str:
    # FIXME
    # FIXME
    # FIXME
    # FIXME
    # FIXME
    # FIXME
    # FIXME
    # FIXME
    # FIXME: should this return a partial/Callable which only needs the header passed?
    # FIXME
    # FIXME
    # FIXME
    # FIXME
    # FIXME
    # FIXME
    """Send the user a pretty-printed usage message."""
    cmd = ctx.prefix + ctx.invoked_with

    header = (header
              or f"Your command `{cmd + ' ' + ' '.join(args)}` does not meet "
              "the usage requirements.")

    message = dedent(f"""\
        {header}
        ```text
        {indent(dedent(content), " " * 8)}
        ```
    """)

    await ctx.message.add_reaction(Reactions.ROBOT)
    await ctx.author.send(message)

    return textwrap.dedent(f"""\
        {header}
        ```text
        Usage: {cmd} <name> <goal> <start_month> <start_day> <end_month <end_day>

        Where:
            <name>         Name for this event.
            <goal>         Number of poms to reach in this event.
            <start_month>  Event starting month.
            <start_day>    Event starting day.
            <end_month>    Event ending month.
            <end_day>      Event ending day.

        Example:
            {cmd} The Best Event 100 June 10 July 4

        At present, events must not overlap; only one concurrent event
        can be ongoing at a time.
        ```
    """)
