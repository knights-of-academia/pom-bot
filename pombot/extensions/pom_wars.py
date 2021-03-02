from discord.ext.commands.bot import Bot

import pombot.commands.pom_wars as commands
from pombot.lib.tiny_tools import BotCommand


def setup(bot: Bot):
    """Load Pom Wars commands.

    Do not use this to add event handlers as basic and essential debugging
    and logging will be broken. Instead, add them in bot.main.
    """
    for command in [
        BotCommand(commands.do_actions, name="actions"),
        BotCommand(commands.do_attack,  name="attack"),
        BotCommand(commands.do_bribe,   name="bribe", hidden=True),
        BotCommand(commands.do_defend,  name="defend"),
    ]:
        bot.add_command(command)
