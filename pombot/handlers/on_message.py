from discord.ext.commands import Bot
from discord.message import Message

from pombot.config import Config, Debug

async def on_message(bot: Bot, message: Message):
    """Handle an on_message event.

    First, verify that the bot can respond in the given channel.

    Then remove any spaces after the prefix. This would normally be achieved
    by using a callable prefix, but the Discord.py API does not support the
    use of spaces after symbols, only alphanumeric characters. This is a
    workaround.
    """
    try:
        if any(Config.POM_CHANNEL_NAMES):
            if message.channel.name not in Config.POM_CHANNEL_NAMES:
                return
    except AttributeError:
        if message.guild is None and not Debug.RESPOND_TO_DM:
            return

    if message.content.startswith(Config.PREFIX + " "):
        message.content = "".join(message.content.split(" ", 1))

    await bot.process_commands(message)
