from discord.ext.commands.bot import Bot
from discord.message import Message

from pombot.config import Config, Debug


async def on_message_handler(bot: Bot, message: Message):
    """Handle new messages globally."""
    try:
        if Config.POM_CHANNEL_NAMES:
            if message.channel.name not in Config.POM_CHANNEL_NAMES:
                return
    except AttributeError:
        if message.guild is None and not Debug.RESPOND_TO_DM:
            return

    if message.content.startswith(f"{Config.PREFIX} "):
        message.content = "".join(message.content.split(" ", 1))

    await bot.process_commands(message)
