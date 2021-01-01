from typing import Callable, Optional

from discord.embeds import Embed
from discord.ext.commands import Context

from pombot.config import Config


async def send_embed_message(
        ctx: Optional[Context],
        *,
        title: str,
        description: str,
        colour=Config.EMBED_COLOUR,
        icon_url=Config.EMBED_IMAGE_URL,
        private_message: bool = False,
        _func: Callable = None,
):
    """Send an embedded message using the context."""
    message = Embed(
        description=description,
        colour=colour,
    ).set_author(
        name=title,
        icon_url=icon_url,
    )

    if ctx is None:
        coro = _func
    else:
        coro = ctx.author.send if private_message else ctx.send

    # Allow the TypeError to bubble up when both ctx and _func are None.
    return await coro(embed=message)
