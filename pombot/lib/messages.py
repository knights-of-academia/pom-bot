from discord.embeds import Embed
from discord.ext.commands import Context

from pombot.config import Config


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
