from functools import partial
from pathlib import Path
from typing import Any, List, Union

from pombot.lib.pom_wars.types import Attack, Bribe, Defend


def load_actions_directories(
    actions_dir: Path,
    type_: Union[Attack, Defend, Bribe],
    *,
    is_heavy: bool = False,
    is_critical: bool = False,
) -> List[Any]:
    actions = []
    actions_dir = actions_dir / "~criticals" if is_critical else actions_dir

    attack_kwargs = {"is_heavy": is_heavy, "is_critical": is_critical}

    action_types = {
        Attack: partial(Attack, **attack_kwargs),
        Defend: Defend,
        Bribe:  Bribe,
    }

    for subdir in actions_dir.iterdir():
        if subdir.name.startswith("~"):
            continue

        actions.append(action_types[type_](subdir))

    return actions
