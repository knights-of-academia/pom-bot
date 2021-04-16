import logging
from functools import partial

from discord.ext.commands import Bot

from pombot import commands
from pombot.config import Config
from pombot.lib.tiny_tools import BotCommand, has_any_role

_log = logging.getLogger(__name__)


def setup(bot: Bot):
    """Load general commands.

    Do not use this to add event handlers as basic and essential debugging
    and logging will be broken. Instead, add them in bot.main.
    """
    admin = {
        "checks": [partial(has_any_role, roles_needed=Config.ADMIN_ROLES)]
    }

    for command in [
        BotCommand(commands.do_events,       name="events"),
        BotCommand(commands.do_fortune,      name="fortune"),
        BotCommand(commands.do_pom,          name="pom"),
        BotCommand(commands.do_undo,         name="undo"),
        BotCommand(commands.do_bank,         name="bank", aliases=[
            *Config.RENAME_POMS_IN_BANK
        ]),
        BotCommand(commands.do_poms,         name="poms", aliases=[
            *Config.PUBLIC_POMS_ALIASES,
            *Config.RENAME_POMS_IN_SESSION,
        ]),

        BotCommand(commands.do_total,        name="total",        **admin),
        BotCommand(commands.do_create_event, name="create_event", **admin),
        BotCommand(commands.do_remove_event, name="remove_event", **admin),

        # Tech debt: These commands are slated for removal.
        BotCommand(commands.do_howmany,      name="howmany"),
        BotCommand(commands.do_newleaf,      name="newleaf"),
        BotCommand(commands.do_reset,        name="reset", hidden=True),
    ]:
        bot.add_command(command)
