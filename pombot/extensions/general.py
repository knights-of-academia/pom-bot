from functools import partial

from discord.ext.commands import Command
from discord.ext.commands.bot import Bot

import pombot


def setup(bot: Bot):
    """Load general, uncategorized commands and listeners."""
    listeners = [
        (partial(pombot.listeners.handle_on_ready, bot), "on_ready"),
        (pombot.listeners.handle_on_command_error,       "on_command_error"),
    ]

    for listener in listeners:
        bot.add_listener(*listener)

    commands = [
        Command(pombot.commands.do_events,  name="events"),
        Command(pombot.commands.do_howmany, name="howmany"),
        Command(pombot.commands.do_newleaf, name="newleaf"),
        Command(pombot.commands.do_pom,     name="pom"),
        Command(pombot.commands.do_poms,    name="poms"),
        Command(pombot.commands.do_reset,   name="reset"),
        Command(pombot.commands.do_undo,    name="undo"),
    ]

    for command in commands:
        bot.add_command(command)
