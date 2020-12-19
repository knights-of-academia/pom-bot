from enum import IntEnum, auto
from pathlib import Path

import pombot.data
from pombot.data import Locations


class AttackStrength(IntEnum):
    NORMAL = auto()
    HEAVY = auto()


class AttackOutcome(IntEnum):
    FAILURE = 0
    SUCCESS = auto()


class Attack:
    def __init__(self) -> None:
        pass

    def mount(self) -> AttackOutcome:
        return AttackOutcome.SUCCESS


def get_attack(strength: AttackStrength) -> Attack:
    return Attack()  # FIXME
