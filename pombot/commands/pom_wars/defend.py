import random
from datetime import datetime
from functools import partial

from discord.ext.commands import Context

from pombot.config import Config, Pomwars, Reactions
from pombot.data import Locations
from pombot.data.pom_wars import load_actions_directories
from pombot.lib.messages import send_embed_message
from pombot.lib.pom_wars.action_chances import is_action_successful
from pombot.lib.pom_wars.team import get_user_team
from pombot.lib.pom_wars.types import Defend
from pombot.lib.storage import Storage
from pombot.lib.types import ActionType


async def do_defend(ctx: Context, *args):
    """Defend your team."""
    description = " ".join(args)
    timestamp = datetime.now()

    if len(description) > Config.DESCRIPTION_LIMIT:
        await ctx.message.add_reaction(Reactions.WARNING)
        await ctx.send(f"{ctx.author.mention}, your pom description must "
                        f"be fewer than {Config.DESCRIPTION_LIMIT} characters.")
        return

    await Storage.add_poms_to_user_session(
        ctx.author,
        descript=description,
        count=1,
        time_set=timestamp,
    )
    await ctx.message.add_reaction(Reactions.TOMATO)

    action = {
        "user":           ctx.author,
        "team":           get_user_team(ctx.author).value,
        "action_type":    ActionType.DEFEND,
        "was_successful": False,
        "was_critical":   None,
        "items_dropped":  "",
        "damage":         None,
        "time_set":       timestamp,
    }

    if not await is_action_successful(ctx.author, timestamp):
        emote = random.choice(["¯\\_(ツ)_/¯", "(╯°□°）╯︵ ┻━┻"])
        await ctx.send(f"<@{ctx.author.id}> defence failed! {emote}")
        await Storage.add_pom_war_action(**action)
        return

    action["was_successful"] = True
    await ctx.message.add_reaction(Reactions.SHIELD)

    defends = load_actions_directories(Locations.DEFENDS_DIR, type_=Defend)
    weights = [defend.weight for defend in defends]
    defend, = random.choices(defends, weights=weights)

    await Storage.add_pom_war_action(**action)

    await send_embed_message(
        None,
        title="You have used Defend against {team}s!".format(
            team=(~get_user_team(ctx.author)).value,
        ),
        description=await defend.get_message(ctx.author),
        colour=Pomwars.DEFEND_COLOUR,
        icon_url=None,
        _func=partial(ctx.channel.send, content=ctx.author.mention),
    )
