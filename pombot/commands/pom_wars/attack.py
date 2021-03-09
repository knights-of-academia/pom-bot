import random
from datetime import datetime, timedelta
from functools import partial

from discord.ext.commands import Context

from pombot.config import Config, Debug, Pomwars, Reactions
from pombot.data import Locations
from pombot.data.pom_wars import load_actions_directories
from pombot.lib.messages import send_embed_message
from pombot.lib.pom_wars.action_chances import is_action_successful
from pombot.lib.pom_wars.team import get_user_team
from pombot.lib.pom_wars.types import Attack
from pombot.lib.storage import Storage
from pombot.lib.types import ActionType, DateRange
from pombot.state import State


async def _get_defensive_multiplier(team: str, timestamp: datetime) -> float:
    defend_actions = await Storage.get_actions(
        action_type=ActionType.DEFEND,
        team=team,
        was_successful=True,
        date_range=DateRange(
            timestamp - timedelta(minutes=Pomwars.DEFEND_DURATION_MINUTES),
            timestamp,
        ),
    )
    defenders = await Storage.get_users_by_id([a.user_id for a in defend_actions])
    multipliers = [Pomwars.DEFEND_LEVEL_MULTIPLIERS[d.defend_level] for d in defenders]
    multiplier = min([sum(multipliers), Pomwars.MAXIMUM_TEAM_DEFENCE])

    return 1 - multiplier


async def do_attack(ctx: Context, *args):
    """Attack the other team."""
    timestamp = datetime.now()
    heavy_attack = bool(args) and args[0].casefold() in Pomwars.HEAVY_QUALIFIERS
    description = " ".join(args[1:] if heavy_attack else args)

    if len(description) > Config.DESCRIPTION_LIMIT:
        await ctx.message.add_reaction(Reactions.WARNING)
        await ctx.send(f"{ctx.author.mention}, your pom description must "
                        f"be fewer than {Config.DESCRIPTION_LIMIT} characters.")
        return

    await Storage.add_poms_to_user_session(
        ctx.author,
        description,
        count=1,
        time_set=timestamp,
    )
    await ctx.message.add_reaction(Reactions.TOMATO)

    action = {
        "user":           ctx.author,
        "team":           get_user_team(ctx.author).value,
        "action_type":    ActionType.HEAVY_ATTACK if heavy_attack
                            else ActionType.NORMAL_ATTACK,
        "was_successful": False,
        "was_critical":   False,
        "items_dropped":  "",
        "damage":         None,
        "time_set":       timestamp,
    }

    if not await is_action_successful(ctx.author, timestamp, heavy_attack):
        emote = random.choice(["¯\\_(ツ)_/¯", "(╯°□°）╯︵ ┻━┻"])
        await Storage.add_pom_war_action(**action)
        await ctx.send(f"<@{ctx.author.id}>'s attack missed! {emote}")
        return

    action["was_successful"] = True
    action["was_critical"] = random.random() <= Pomwars.BASE_CHANCE_FOR_CRITICAL
    await ctx.message.add_reaction(Reactions.BOOM)

    attacks = load_actions_directories(
        Locations.HEAVY_ATTACKS_DIR if heavy_attack else Locations.NORMAL_ATTACKS_DIR,
        type_=Attack,
        is_critical=action["was_critical"],
        is_heavy=heavy_attack,
    )
    weights = [attack.weight for attack in attacks]
    attack, = random.choices(attacks, weights=weights)

    defensive_multiplier = await _get_defensive_multiplier(
        team=(~get_user_team(ctx.author)).value,
        timestamp=timestamp)

    action["damage"] = attack.damage * defensive_multiplier
    await Storage.add_pom_war_action(**action)

    await send_embed_message(
        None,
        title=attack.get_title(ctx.author),
        description=attack.get_message(action["damage"]),
        icon_url=None,
        colour=attack.get_colour(),
        _func=partial(ctx.channel.send, content=ctx.author.mention),
    )

    await State.scoreboard.update()

    if Debug.BENCHMARK_POMWAR_ATTACK:
        print(f"!attack took: {datetime.now() - timestamp}")
