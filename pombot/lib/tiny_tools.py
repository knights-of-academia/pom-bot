import inspect
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any

import discord
from discord.ext.commands import Command, Context
from discord.ext.commands.errors import MissingAnyRole, NoPrivateMessage

from pombot.lib.types import DateRange


def positive_int(value: Any) -> int:
    """Return the provided value if it is a positive whole number. Raise
    ValueError otherwise.
    """
    if (intval := int(value)) < 0:
        raise ValueError(f"Expected a positive integer, got {value}")

    return intval


def str2bool(value: str) -> bool:
    """Coerce a string to a bool based on its value."""
    return value.casefold() in {"yes", "y", "1", "true", "t"}


def daterange_from_timestamp(timestamp: datetime):
    """Get the DateRange of the day containing the given timestamp."""
    get_timestamp_at_time = lambda time: datetime.strptime(
        datetime.strftime(timestamp, f"%Y-%m-%d {time}"), "%Y-%m-%d %H:%M:%S")

    morning = get_timestamp_at_time("00:00:00")
    evening = get_timestamp_at_time("23:59:59")

    return DateRange(morning, evening)


def has_any_role(ctx: Context, roles_needed=None) -> bool:
    """A non-decorator reimplementation of discord.ext.commands.has_any_role,
    but with dignity.
    """
    roles_needed = roles_needed or []

    if not isinstance(ctx.channel, discord.abc.GuildChannel):
        raise NoPrivateMessage()

    get_user_roles = partial(discord.utils.get, ctx.author.roles)

    if not any(get_user_roles(id=role_needed) is not None
            if isinstance(role_needed, int)
            else get_user_roles(name=role_needed) is not None
                for role_needed in roles_needed):
        raise MissingAnyRole(roles_needed)

    return True


class BotCommand(Command):
    """Wrapper around discord.ext.commands.Command which maps the calling
    module's __name__ to the custom attribute `extension`.
    """
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)
        self.extension = Path(inspect.stack()[1].filename).stem
