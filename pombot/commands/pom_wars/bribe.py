import random
from datetime import datetime

from discord.ext.commands import Context

from pombot.data import Locations
from pombot.data.pom_wars import load_actions_directories
from pombot.lib.pom_wars.team import get_user_team
from pombot.lib.pom_wars.types import Bribe
from pombot.lib.storage import Storage
from pombot.lib.types import ActionType


async def do_bribe(ctx: Context):
    """What? I don't take bribes..."""
    bribes = load_actions_directories(Locations.BRIBES_DIR, type_=Bribe)
    weights = [bribe.weight for bribe in bribes]
    bribe, = random.choices(bribes, weights=weights)

    timestamp = datetime.now()

    action = {
        "user":           ctx.author,
        "team":           get_user_team(ctx.author).value,
        "action_type":    ActionType.BRIBE,
        "was_successful": True,
        "was_critical":   None,
        "items_dropped":  "",
        "damage":         None,
        "time_set":       timestamp,
    }

    await Storage.add_pom_war_action(**action)
    await ctx.reply(bribe.get_message(ctx.author, ctx.bot))
