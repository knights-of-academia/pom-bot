import random
from datetime import timedelta, timezone

from discord import RawReactionActionEvent
from discord.ext.commands import Bot
from discord.guild import Guild
from discord.message import Message

import pombot.errors
from pombot.config import Config, Debug, Pomwars, Reactions, TIMEZONES
from pombot.lib.messages import send_embed_message
from pombot.lib.types import Team
from pombot.storage import Storage


async def _create_roles_on_guild(roles: list, guild: Guild):
    for role in roles:
        if role in (r.name for r in guild.roles):
            continue

        await guild.create_role(name=role)


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

    if channel.name != Pomwars.JOIN_CHANNEL_NAME:
        return

    if payload.emoji.name == Reactions.WAR_JOIN_REACTION:
        await _create_roles_on_guild(bot_roles, guild)

        team = _get_guild_team_or_random(payload.guild_id)
        dm_description = "Enjoy the Pom War event! Good luck and have fun!"

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

    if payload.emoji.name in TIMEZONES:
        user = Storage.get_user_by_id(payload.user_id)
        if len(user) == 0:
            Storage.set_user_timezone(
                payload.user_id,
                timezone(timedelta(hours=TIMEZONES[payload.emoji.name]))
            )
        else:
            await send_embed_message(
                None,
                title=f"Oops! Looks like i had some problem setting your timezone.",
                description="You first need to join the event",
                _func=payload.member.send
            )


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
