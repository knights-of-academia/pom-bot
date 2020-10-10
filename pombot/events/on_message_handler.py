from discord.channel import DMChannel
from discord.ext.commands.bot import Bot
from discord.message import Message

from pombot.config import Config


async def on_message_handler(bot: Bot, message: Message):
    is_restricted = (Config.POM_CHANNEL_NAMES
                     and message.channel.name not in Config.POM_CHANNEL_NAMES)

    if isinstance(message.channel, DMChannel) or is_restricted:
        return

    await bot.process_commands(message)
