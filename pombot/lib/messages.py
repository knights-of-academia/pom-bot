from typing import Callable, NamedTuple, Optional

from discord.embeds import Embed
from discord.ext.commands import Context
from discord.message import Message

from pombot.config import Config, IconUrls


class EmbedField(NamedTuple):
    """A field represented as a tuple."""
    name: str
    value: str
    inline: bool = True


async def send_embed_message(
        ctx: Optional[Context],
        *,
        title: str,
        description: str,
        colour=Config.EMBED_COLOUR,
        icon_url=IconUrls.POMBOMB,
        fields: list = None,
        footer: str = None,
        image: str = None,
        thumbnail: str = None,
        private_message: bool = False,
        _func: Callable = None,
) -> Message:
    """Send an embedded message using the context.

    @param ctx Ethier the context with which to send the response, or None
        when a coroutine is specified via _func.
    @param colour Colour to line the left side of the embed.
    @param private_messaage Whether or not to send this emabed as a DM to the
        user; does not apply when ctx is None.
    @param _func Coroutine describing how to send the embed.

    All other parameters:

    ┌───────────────────────────────────────┐
    │┌─────┐                                │
    ││icon │ Title                 ┌──────┐ │
    │└─────┘                       │thumb-│ │
    ├─────────────────────────     │nail  │ │
    │                              │      │ │
    │ Description                  └──────┘ │
    │                                       │
    │                                       │
    ├┬──────────────┬┬──────────────┐       │
    ││              ││              │       │
    ││ Field        ││ Field        │       │
    ││ (inline)     ││ (inline)     │       │
    ││              ││              │       │
    ││              ││              │       │
    ├┴──────────────┴┴──────────────┘       │
    │                                       │
    │ ┌──────────────────────────────────┐  │
    │ │                                  │  │
    │ │                                  │  │
    │ │                                  │  │
    │ │                                  │  │
    │ │             Image                │  │
    │ │                                  │  │
    │ │                                  │  │
    │ │                                  │  │
    │ │                                  │  │
    │ │                                  │  │
    │ └──────────────────────────────────┘  │
    │Footer                                 │
    └───────────────────────────────────────┘

    @return The message object that was sent.
    """
    message = Embed(
        description=description,
        colour=colour,
    )

    if icon_url:
        message.set_author(
            name=title,
            icon_url=icon_url,
        )
    else:
        message.title=title
        message.description=description
        message.colour=colour

    if fields:
        for field in fields:
            name, value, inline = field
            message.add_field(name=name, value=value, inline=inline)

    for content, setter, kwarg in (
        (image,     message.set_image,     "url"),
        (footer,    message.set_footer,    "text"),
        (thumbnail, message.set_thumbnail, "url"),
    ):
        if content:
            setter(**{kwarg: content})

    if ctx is None:
        coro = _func
    else:
        coro = ctx.author.send if private_message else ctx.send

    # Allow the TypeError to bubble up when both ctx and _func are None.
    return await coro(embed=message)
