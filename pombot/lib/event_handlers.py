import random
from datetime import timedelta, timezone

from discord import RawReactionActionEvent
from discord.ext.commands import Bot
from discord.message import Message

import pombot.errors
from pombot.config import Config, Debug, Pomwars, Reactions
from pombot.lib.messages import send_embed_message
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
    """Handle reactions being added to messages, assign users to teams when
    they react."""
    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)
    bot_roles = [Pomwars.KNIGHT_ROLE, Pomwars.VIKING_ROLE]

    if not all([bot.is_ready(),
                guild is not None,
                channel is not None,
                payload.user_id != bot.user.id]):
        return

    if not all([Pomwars.JOIN_CHANNEL_NAME == channel.name,
                Reactions.WAR_JOIN_REACTION == payload.emoji.name]):
        return

    for bot_role in bot_roles:
        if bot_role in (r.name for r in guild.roles):
            continue

        await guild.create_role(name=bot_role)

    team = _get_guild_team_or_random(payload.guild_id)
    dm_description = "Enjoy to the Pom War event! Good luck and have fun!"

    try:
        Storage.add_user(payload.user_id, timezone(timedelta(hours=0)), team)
    except pombot.errors.UserAlreadyExistsError as exc:
        dm_description = "You're already on a team! :open_mouth:"
        user_roles = [r.name for r in payload.member.roles]
        bot_roles_on_user = []

        for bot_role in bot_roles:
            try:
                bot_roles_on_user.append(user_roles[user_roles.index(bot_role)])
            except ValueError:
                continue

        if len(bot_roles_on_user) in [0, 2]:
            team = Team(exc.team)
        else:
            team = Team(bot_roles_on_user[0])

            if team != exc.team:
                dm_description = "It looks like your team has been swapped!"
                Storage.update_user_team(payload.user_id, team)

    await send_embed_message(
        None,
        title=f"Welcome to the {team}s, {payload.member.display_name}!",
        description=dm_description,
        colour=Pomwars.ACTION_COLOUR,
        icon_url=team.get_icon(),
        _func=payload.member.send,
    )

    role, = [r for r in guild.roles if r.name == team.value]
    await payload.member.add_roles(role)

    timezones = {
        Reactions.UTC_MINUS_10_TO_9: -9,
        Reactions.UTC_MINUS_8_TO_7: -7,
        Reactions.UTC_MINUS_6_TO_5: -5,
        Reactions.UTC_MINUS_4_TO_3: -3,
        Reactions.UTC_MINUS_2_TO_1: -1,
        Reactions.UTC_PLUS_1_TO_2: +2,
        Reactions.UTC_PLUS_3_TO_4: +4,
        Reactions.UTC_PLUS_5_TO_6: +6,
        Reactions.UTC_PLUS_7_TO_8: +8,
        Reactions.UTC_PLUS_9_TO_10: +10,
    }

    if (channel.name == Pomwars.JOIN_CHANNEL_NAME and payload.emoji.name in timezones):
        Storage.set_user_timezone(
            payload.user_id,
            timezone(timedelta(hours=timezones[payload.emoji.name])))


def _get_guild_team_or_random(guild_id: int) -> Team:
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
