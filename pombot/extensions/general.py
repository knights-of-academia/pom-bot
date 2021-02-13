from discord.ext.commands import Command
from discord.ext.commands.bot import Bot

import pombot


def setup(bot: Bot):
    """Load general, uncategorized commands and listeners."""
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
