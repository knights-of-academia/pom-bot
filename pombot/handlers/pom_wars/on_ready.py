import logging

from discord.ext.commands import Bot

from pombot.config import Pomwars
from pombot.state import State
from pombot.lib.pom_wars.scoreboard import Scoreboard

_log = logging.getLogger(__name__)


async def on_ready(bot: Bot):
    """Find and remember the static scoreboard for all connected guilds."""
    channels = []

    for guild in bot.guilds:
        for channel in guild.channels:
            if channel.name == Pomwars.JOIN_CHANNEL_NAME:
                channels.append(channel)

    State.scoreboard = Scoreboard(bot, channels)
    full_channels, restricted_channels = await State.scoreboard.update()

    for channel in full_channels:
        _log.error("Join channel '%s' on '%s' is not empty",
            channel.name, channel.guild.name)

    for channel in restricted_channels:
        _log.error("Join channel '%s' on '%s' is not messagable (Missing Access)",
            channel.name, channel.guild.name)
