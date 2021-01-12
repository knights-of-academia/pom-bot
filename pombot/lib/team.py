from enum import Enum
from pombot.config import Pomwars, Config
from pombot.storage import Storage
from pombot.lib.types import ActionType


class Team(str, Enum):
    """Team that a user can be on."""
    KNIGHTS = Pomwars.KNIGHT_ROLE
    VIKINGS = Pomwars.VIKING_ROLE

    def __invert__(self):
        return self.VIKINGS if self == self.KNIGHTS else self.KNIGHTS

    def get_icon(self):
        """Return the team's configured IconUrl."""
        icons = {
            self.KNIGHTS: Pomwars.IconUrls.KNIGHT,
            self.VIKINGS: Pomwars.IconUrls.VIKING,
        }

        return icons[self]

    @property
    def damage(self) -> int:
        """The team's total damage."""
        return Storage.sum_team_damage(self.value) / 100.0

    @property
    def favorite_action(self) -> ActionType:
        """The team's most-used action."""
        count_actions = lambda type_: Storage.count_rows_in_table(
            Config.ACTIONS_TABLE, action_type=type_, team=self.value)

        # Tech debt: As beautiful as this line is, it's calling the DB one time
        # per ActionType, per Team. It's only downloading a single byte, but if
        # connections are a problem, then we need to figure out a SQL one-liner
        # to get all four bytes in one call per team.
        # https://stackoverflow.com/a/12789493/5161663
        return max({typ: count_actions(typ.value) for typ in ActionType})

    @property
    def attack_count(self) -> int:
        """The team's total number of actions."""
        return Storage.count_rows_in_table(Config.ACTIONS_TABLE, team=self.value)

    @property
    def population(self) -> int:
        """The team's population."""
        return Storage.count_rows_in_table(Config.USERS_TABLE, team=self.value)
