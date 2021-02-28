from discord.ext.commands import Command
from discord.ext.commands.bot import Bot

import pombot.commands.pom_wars as commands


def setup(bot: Bot):
    """Load Pom Wars commands.

    Do not use this to add event handlers as basic and essential debugging
    and logging will be broken. Instead, add them in bot.main.
    """
    for command in [
        Command(commands.do_actions, name="actions"),
        Command(commands.do_attack,  name="attack"),
        Command(commands.do_bribe,   name="bribe", hidden=True),
        Command(commands.do_defend,  name="defend"),
    ]:
        bot.add_command(command)
