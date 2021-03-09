import math
import random
from datetime import datetime
from functools import cache

from discord.user import User

from pombot.config import Debug, Pomwars
from pombot.lib.storage import Storage
from pombot.lib.tiny_tools import daterange_from_timestamp


async def is_action_successful(
    user: User,
    timestamp: datetime,
    is_heavy_attack: bool = False,
) -> bool:
    """Considering the time, user choices and previous user actions,
    determine if current attack is successful.
    """
    actions = await Storage.get_actions(
        user=user,
        date_range=daterange_from_timestamp(timestamp),
    )

    def _delayed_exponential_drop(num_poms: int):
        operand = lambda x: math.pow(math.e, ((-(x - 9)**2) / 2)) / (math.sqrt(2 * math.pi))

        probabilities = {
            range(0, 6):     lambda x: 1.0,
            range(6, 11):    lambda x: -0.016 * math.pow(x, 2) + 0.16 * x + 0.6,
            range(11, 1000): lambda x: operand(x) / operand(9)
        }

        for range_, function in probabilities.items():
            if num_poms in range_:
                break
        else:
            function = lambda x: 0.0

        return function(num_poms)

    async def _get_heavy_attack_base_chance(user_id: int) -> float:
        nonlocal actions

        botuser = await Storage.get_user_by_id(user_id)
        pity_levels = Pomwars.HEAVY_ATTACK_LEVEL_VALIANT_ATTEMPT_CONDOLENCE_REWARDS
        min_chance, max_chance = pity_levels[botuser.heavy_attack_level]

        # Do not add the +1 to max_chance because it's defaulted to later.
        pity_range = range(*(int(x * 100) for x in (
            min_chance,
            max_chance,
            Pomwars.HEAVY_PITY_INCREMENT,
        )))

        # A modified reducer because functools.reduce() won't break after some
        # condition is met.
        num_misses = 0
        for action in reversed(actions):
            if action.was_successful:
                break
            num_misses += 1

        return dict(enumerate(pity_range)).get(num_misses, max_chance * 100) / 100

    @cache
    def _get_normal_attack_success_chance(num_poms: int):
        return 1.0 * _delayed_exponential_drop(num_poms)

    @cache
    def _get_heavy_attack_success_chance(num_poms: int, base_chance: float):
        return base_chance * _delayed_exponential_drop(num_poms)

    if is_heavy_attack:
        base_chance = await _get_heavy_attack_base_chance(user.id)
        chance_func = lambda x: _get_heavy_attack_success_chance(x, base_chance)
    else:
        chance_func = _get_normal_attack_success_chance

    return random.random() <= chance_func(
        len(actions) if not Debug.BENCHMARK_POMWAR_ATTACK else 1)
