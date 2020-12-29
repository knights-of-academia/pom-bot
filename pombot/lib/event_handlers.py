import random

from discord import RawReactionActionEvent
from discord.ext.commands import Bot
from discord.message import Message

from pombot.config import Config, Debug, Pomwars, Reactions


async def on_message_handler(bot: Bot, message: Message):
    """Handle an on_message event.

    First, verify that the bot can respond in the given channel.

    Then remove any spaces after the prefix. This would normally be achieved
    by using a callable prefix, but the Discord.py API does not support the
    use of spaces after symbols, only alphanumeric characters. This is a
    workaround.
    """
    try:
        if Config.POM_CHANNEL_NAMES:
            if message.channel.name not in Config.POM_CHANNEL_NAMES:
                return
    except AttributeError:
        if message.guild is None and not Debug.RESPOND_TO_DM:
            return

    if message.content.startswith(Config.PREFIX + " "):
        message.content = "".join(message.content.split(" ", 1))

    await bot.process_commands(message)

async def on_raw_reaction_add_handler(bot: Bot, payload: RawReactionActionEvent):
    """Handle reactions being added to messages."""
    channel = bot.get_channel(payload.channel_id)

    # Handle reactions in pom war draft channel, assign users to teams
    if bot.is_ready() and channel is not None and payload.user_id is not bot.user.id:
        if Pomwars.JOIN_CHANNEL_NAME == channel.name and \
           Reactions.WAR_JOIN_REACTION == payload.emoji.name:
            guild = bot.get_guild(payload.guild_id)
            knight_role = None
            viking_role = None
            for role in guild.roles:
                if role.name == Pomwars.KNIGHT_ROLE:
                    knight_role = role
                if role.name == Pomwars.VIKING_ROLE:
                    viking_role = role

            if knight_role is not None and viking_role is not None:
                await payload.member.remove_roles(knight_role, viking_role)
                team = knight_role

                if payload.guild_id in Pomwars.KNIGHT_ONLY_GUILDS:
                    team = knight_role
                elif payload.guild_id in Pomwars.VIKING_ONLY_GUILDS:
                    team = viking_role
                else:
                    choice = bool(random.getrandbits(1))
                    team = knight_role if choice else viking_role

                await payload.member.add_roles(team)
