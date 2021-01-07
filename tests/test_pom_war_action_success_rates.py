from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

from pombot.cogs.pom_wars_commands import _is_action_successful
from pombot.lib.types import User as PombotUser

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
            actual_outcome = _is_action_successful(user, timestamp, is_heavy_attack)

            assert expected_outcome == actual_outcome, \
                f"pom_number: {pom_number}, dice_roll: {dice_roll}"


@patch("pombot.storage.Storage.get_actions")
@patch("pombot.storage.Storage.get_user_by_id")
@patch("random.random")
def test_heavy_attack_success_rate(
    random_mock: Mock,
    get_user_by_id_mock: Mock,
    get_actions_mock: Mock,
):
    """Generically test _is_attack_successful when doing a heavy attack."""
    class MockPom(MagicMock):
        """A fake Pom object.

        When gathering chances for heavy attacks, the previous heavy attack
        is consulted. For each previous unsuccesful attack, there is a
        configurable increase in the chance for the next attack.

        For this test, we expect the futures chances to remain constant, so
        each previous attack must be successful.
        """
        @staticmethod
        def was_successful():
            """Report this action to be successful."""
            return True

    get_user_by_id_mock.return_value = PombotUser(
        1234, timezone(timedelta()), "Team", "inventory", 1, 1, 1, 1)

    dice_rolls_and_expected_outcomes = {
        MockPom(1): [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        MockPom(2): [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        MockPom(3): [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        MockPom(4): [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        MockPom(5): [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        MockPom(6): [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        MockPom(7): [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        MockPom(8): [(0.1, 0.2, 0.3), (TRU, TRU, FLS)],
        MockPom(9): [(0.1, 0.2, 0.3), (TRU, FLS, FLS)],
        MockPom(10): [(0.1, 0.2, 0.3), (TRU, FLS, FLS)],
        MockPom(11): [(0.1, 0.2, 0.3), (FLS, FLS, FLS)],
        MockPom(12): [(0.1, 0.2, 0.3), (FLS, FLS, FLS)],
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
            actual_outcome = _is_action_successful(user, timestamp, is_heavy_attack)

            assert expected_outcome == actual_outcome, \
                f"pom_number: {pom_number}, dice_roll: {dice_roll}"


@patch("pombot.storage.Storage.get_actions")
@patch("random.random")
def test_defend_success_rate(random_mock: Mock, get_actions_mock: Mock):
    """Generically test _is_attack_successful when doing a defend."""
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
            actual_outcome = _is_action_successful(user, timestamp, is_heavy_attack)

            assert expected_outcome == actual_outcome, \
                f"pom_number: {pom_number}, dice_roll: {dice_roll}"
