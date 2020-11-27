from enum import IntEnum, auto
from pathlib import Path

import pombot.data
from pombot.data import Locations


class AttackStrength(IntEnum):
    WEAK = auto()
    NORMAL = auto()
    STRONG = auto()
    RAPTORS = auto()


class AttackOutcome(IntEnum):
    FAILURE = 0
    SUCCESS = auto()


class Attack:
    def __init__(self) -> None:
        pass

    def mount() -> AttackOutcome:
        return AttackOutcome.SUCCESS


class Attacks:
    def __init__(self) -> None:
        self._registered_attacks = []

    def __call__(self, **kwargs):
        print(kwargs)

def get_attack(strength: AttackStrength) -> Attack:
    return Attack()
