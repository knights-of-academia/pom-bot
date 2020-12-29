import random
from datetime import timedelta, timezone

from discord import RawReactionActionEvent
from discord.ext.commands import Bot
from discord.message import Message

from pombot.config import Config, Debug, Pomwars, Reactions
from pombot.lib.types import Team
from pombot.storage import Storage


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
    """Handle reactions being added to messages, assign users to teams when they react."""
    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)

    conditions = [
        bot.is_ready(),
        guild is not None,
        channel is not None,
        payload.user_id != bot.user.id
    ]
    if not all(conditions):
        return

    # Assign the role
    join_conditions = [
        Pomwars.JOIN_CHANNEL_NAME == channel.name,
        Reactions.WAR_JOIN_REACTION == payload.emoji.name
    ]
    if all(join_conditions):
        knight_role = None
        viking_role = None
        for role in guild.roles:
            if role.name == Pomwars.KNIGHT_ROLE:
                knight_role = role
            if role.name == Pomwars.VIKING_ROLE:
                viking_role = role

        if None in [knight_role, viking_role]:
            return

        team = _get_assigned_team(payload.guild_id)

        Storage.add_user(payload.user_id, timezone(timedelta(hours=0)), team)

        assigned_team_role = None
        if team == Team.KNIGHTS:
            assigned_team_role = knight_role
        elif team == Team.VIKINGS:
            assigned_team_role = viking_role

        await payload.member.add_roles(assigned_team_role)

    timezones = {
        Reactions.UTC_MINUS_10_TO_9: "-09:00",
        Reactions.UTC_MINUS_8_TO_7: "-07:00",
        Reactions.UTC_MINUS_6_TO_5: "-05:00",
        Reactions.UTC_MINUS_4_TO_3: "-03:00",
        Reactions.UTC_MINUS_2_TO_1: "-01:00",
        Reactions.UTC_PLUS_1_TO_2: "+02:00",
        Reactions.UTC_PLUS_3_TO_4: "+04:00",
        Reactions.UTC_PLUS_5_TO_6: "+06:00",
        Reactions.UTC_PLUS_7_TO_8: "+08:00",
        Reactions.UTC_PLUS_9_TO_10: "+10:00"
    }
    is_valid_timezone = True if payload.emoji.name in timezones else False
    timezone_conditions = [
        Pomwars.JOIN_CHANNEL_NAME == channel.name,
        is_valid_timezone
    ]
    #Set the timezone
    if all(timezone_conditions):
        Storage.set_user_timezone(payload.user_id, timezones[payload.emoji.name])

    return

def _get_assigned_team(guild_id: int) -> Team:
    """Decide which team a user should be on, based on their guild and the
    team that currently needs more players.

    @param guild_id The ID of the guild the user is part of
    @return The team the user is assigned to
    """
    assigned_team = None
    if guild_id in Pomwars.KNIGHT_ONLY_GUILDS:
        assigned_team = Team.KNIGHTS
    elif guild_id in Pomwars.VIKING_ONLY_GUILDS:
        assigned_team = Team.VIKINGS
    else:
        knights_count, vikings_count = Storage.get_team_populations()
        if knights_count > vikings_count:
            assigned_team = Team.VIKINGS
        elif vikings_count > knights_count:
            assigned_team = Team.KNIGHTS
        else:
            assigned_team = random.choice([Team.KNIGHTS, Team.VIKINGS])

    return assigned_team
