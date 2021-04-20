from enum import Enum

from discord.user import User

from pombot.config import Config, IconUrls, Pomwars
from pombot.lib.pom_wars import errors as war_crimes
from pombot.lib.storage import Storage
from pombot.lib.types import ActionType


def get_user_team(user: User) -> str:
    team_roles = [
        role for role in user.roles
        if role.name in [Pomwars.KNIGHT_ROLE, Pomwars.VIKING_ROLE]
    ]

    if len(team_roles) != 1:
        raise war_crimes.InvalidNumberOfRolesError()

    return Team(team_roles[0].name)


class Team(str, Enum):
    """Team that a user can be on."""
    KNIGHTS = Pomwars.KNIGHT_ROLE
    VIKINGS = Pomwars.VIKING_ROLE

    def __invert__(self):
        return self.VIKINGS if self == self.KNIGHTS else self.KNIGHTS

    def get_icon(self):
        """Return the team's configured IconUrl."""
        icons = {
            self.KNIGHTS: IconUrls.VIKING,
            self.VIKINGS: IconUrls.VIKING,
        }

        return icons[self]

    @property
    async def damage(self) -> int:
        """The team's total damage."""
        return int(await Storage.sum_team_damage(self.value) / 100.0)

    @property
    async def favorite_action(self) -> ActionType:
        """The team's most-used action."""
        async def _count_actions(typ: ActionType):
            await Storage.count_rows_in_table(Config.ACTIONS_TABLE,
                action_type=typ,
                team=self.value,
            )

        return max({typ: await _count_actions(typ) for typ in ActionType})

    @property
    async def attack_count(self) -> int:
        """The team's total number of actions."""
        return await Storage.count_rows_in_table(Config.ACTIONS_TABLE, team=self.value)

    @property
    async def population(self) -> int:
        """The team's population."""
        return await Storage.count_rows_in_table(Config.USERS_TABLE, team=self.value)
