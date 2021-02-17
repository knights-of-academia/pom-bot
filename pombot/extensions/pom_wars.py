from functools import partial

from discord.ext.commands import Command
from discord.ext.commands.bot import Bot

import pombot.commands.pom_wars as commands
import pombot.listeners.pom_wars as listeners


def setup(bot: Bot):
    """Load general commands and listeners."""
    hidden = {"hidden": True}

    for command in [
        Command(commands.do_actions, name="actions"),
        Command(commands.do_attack,  name="attack"),
        Command(commands.do_bribe,   name="bribe", **hidden),
        Command(commands.do_defend,  name="defend"),
    ]:
        bot.add_command(command)

    # FIXME these are the listeners. the func's and folders should be called
    # handlers.
    for listener in [
        (partial(listeners.handle_on_ready, bot), "on_ready"),
    ]:
        bot.add_listener(*listener)
