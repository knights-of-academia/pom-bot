import logging
from functools import partial

from discord.ext.commands import Bot, Command

from pombot import commands
from pombot.config import Config
from pombot.lib.tiny_tools import has_any_role

_log = logging.getLogger(__name__)


def setup(bot: Bot):
    """Load general commands.

    Do not use this to add event handlers as basic and essential debugging
    and logging will be broken. Instead, add them to bot.py::main().
    """
    admin = {
        "checks": [partial(has_any_role, roles_needed=Config.ADMIN_ROLES)]
    }

    for command in [
        Command(commands.do_events,       name="events"),
        Command(commands.do_howmany,      name="howmany"),
        Command(commands.do_newleaf,      name="newleaf"),
        Command(commands.do_pom,          name="pom"),
        Command(commands.do_poms,         name="poms"),
        Command(commands.do_reset,        name="reset", hidden=True),
        Command(commands.do_undo,         name="undo"),

        Command(commands.do_total,        name="total",        **admin),
        Command(commands.do_create_event, name="create_event", **admin),
        Command(commands.do_remove_event, name="remove_event", **admin),
    ]:
        bot.add_command(command)
