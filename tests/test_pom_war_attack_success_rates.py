from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from pombot.cogs.pom_wars_commands import _is_attack_successful

# For vertical alignment.
TRU = True
FLS = False


@patch("pombot.storage.Storage.get_actions")
@patch("random.random")
def test_normal_attack_success_rate(random_mock: Mock, get_actions_mock: Mock):
    """Generically test _is_attack_successful when doing a normal attack."""
    dice_rolls_and_expected_outcomes = {
        1: [(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
            (TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU)],
        2: [(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
            (TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU)],
        3: [(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
            (TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU)],
        4: [(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
            (TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU)],
        5: [(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
            (TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU)],
        6: [(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
            (TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU, FLS)],
        7: [(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
            (TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU, FLS)],
        8: [(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
            (TRU, TRU, TRU, TRU, TRU, TRU, TRU, TRU, FLS, FLS)],
        9: [(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
            (TRU, TRU, TRU, TRU, TRU, TRU, TRU, FLS, FLS, FLS)],
        10: [(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
             (TRU, TRU, TRU, TRU, TRU, TRU, FLS, FLS, FLS, FLS)],
        11: [(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
             (TRU, FLS, FLS, FLS, FLS, FLS, FLS, FLS, FLS, FLS)],
        12: [(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
             (FLS, FLS, FLS, FLS, FLS, FLS, FLS, FLS, FLS, FLS)],
    }
    user = MagicMock()
    is_heavy_attack = False
    timestamp = datetime.now()
    actions = []

    for pom_number, settings in dice_rolls_and_expected_outcomes.items():
        actions.append(pom_number)
        get_actions_mock.return_value = actions
        print(f"len(actions) = {len(actions)}")

        for dice_roll, expected_outcome in zip(*settings):
            random_mock.return_value = dice_roll
            actual_outcome = _is_attack_successful(user, is_heavy_attack, timestamp)

            assert expected_outcome == actual_outcome, \
                f"pom_number: {pom_number}, dice_roll: {dice_roll}"


@patch("pombot.storage.Storage.get_actions")
@patch("random.random")
def test_heavy_attack_success_rate(random_mock: Mock, get_actions_mock: Mock):
    """Generically test _is_attack_successful when doing a heavy attack."""
    dice_rolls_and_expected_outcomes = {
        1: [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        2: [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        3: [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        4: [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        5: [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        6: [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        7: [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        8: [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        9: [(0.1, 0.2, 0.3), (TRU, FLS, FLS)],
        10: [(0.1, 0.2, 0.3), (TRU, FLS, FLS)],
        11: [(0.1, 0.2, 0.3), (FLS, FLS, FLS)],
        12: [(0.1, 0.2, 0.3), (FLS, FLS, FLS)],
    }
    user = MagicMock()
    is_heavy_attack = True
    timestamp = datetime.now()
    actions = []

    for pom_number, settings in dice_rolls_and_expected_outcomes.items():
        actions.append(pom_number)
        get_actions_mock.return_value = actions
        print(f"len(actions) = {len(actions)}")

        for dice_roll, expected_outcome in zip(*settings):
            random_mock.return_value = dice_roll
            actual_outcome = _is_attack_successful(user, is_heavy_attack, timestamp)

            assert expected_outcome == actual_outcome, \
                f"pom_number: {pom_number}, dice_roll: {dice_roll}"
