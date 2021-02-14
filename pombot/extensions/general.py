from functools import partial

import discord
from discord.ext.commands import Command, Context
from discord.ext.commands.errors import MissingAnyRole, NoPrivateMessage
from discord.ext.commands.bot import Bot

import pombot
from pombot.config import Config


def _has_any_role(ctx: Context, roles_needed=None) -> bool:
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


def setup(bot: Bot):
    """Load general commands and listeners."""
    admin = {
        "checks": [partial(_has_any_role, roles_needed=Config.ADMIN_ROLES)]
    }

    for command in [
        Command(pombot.commands.do_events,       name="events"),
        Command(pombot.commands.do_howmany,      name="howmany"),
        Command(pombot.commands.do_newleaf,      name="newleaf"),
        Command(pombot.commands.do_pom,          name="pom"),
        Command(pombot.commands.do_poms,         name="poms"),
        Command(pombot.commands.do_reset,        name="reset"),
        Command(pombot.commands.do_undo,         name="undo"),

        Command(pombot.commands.do_total,        name="total",        **admin),
        Command(pombot.commands.do_create_event, name="create_event", **admin),
        Command(pombot.commands.do_remove_event, name="remove_event", **admin),
    ]:
        bot.add_command(command)

    for listener in [
        (partial(pombot.listeners.handle_on_ready, bot), "on_ready"),
        (pombot.listeners.handle_on_command_error,       "on_command_error"),
    ]:
        bot.add_listener(*listener)
