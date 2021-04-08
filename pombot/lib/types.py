from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


@dataclass
class DateRange:
    """An inclusive range of dates."""
    start_date: datetime
    end_date: datetime

    def __str__(self):
        fmt = lambda dt: datetime.strftime(dt, "%B %d, %Y")
        ignore_time = lambda dt: datetime.strftime(dt, "%B %d")

        if ignore_time(self.start_date) == ignore_time(self.end_date):
            return f"{fmt(self.start_date)}"

        return f"{fmt(self.start_date)} - {fmt(self.end_date)}"

    def __init__(self, *args):
        """Initialise a newly created object.

        The arguments to this function are always coerced into two
        datetime's. You can specify two datetimes directly, or a tuple of
        four strings.

        Args, two datetimes:
            start_date: A datetime object representing the start of the range.
            end_date: A datetime object representing the end of the range.

        Args, four strings:
            start_month: A string matching strftime's "%B" specificer for
                what will eventually become start_date.
            start_day: A string containing a positive integer between 1 and
                the maximum number of days in the previously specified month.
            end_month: A string matching strftime's "%B" specificer for
                what will eventually become end_date.
            end_day: A string containing a positive integer between 1 and the
                maximum number of days in the previously specified month.

        In the former case, exact years and times are used.

        In the latter case:
            - The year is assumed to be "this year" unless the end month/day
              happen to occur before the start.
            - The time of the start day is assumed to be midnight.
            - The time of the end day is assumed to be 1 second before
              midnight of the following day.
        """
        if len(args) == 2 and all(isinstance(arg, datetime) for arg in args):
            self.start_date, self.end_date = args
            return

        # Allow ValueError to bubble up.
        beg_month, beg_day, end_month, end_day = args

        dateformat = "%B %d %Y %H:%M:%S"
        year = datetime.today().year
        dates = {
            "beg": f"{beg_month} {beg_day} {year} 00:00:00",
            "end": f"{end_month} {end_day} {year} 23:59:59",
        }

        for date_name, date_str in dates.items():
            try:
                dates[date_name] = datetime.strptime(date_str, dateformat)
            except ValueError as exc:
                raise ValueError(f"Invalid date: `{date_str}`") from exc

        beg_date, end_date = dates.values()

        if end_date < beg_date:
            end_date = datetime.strptime(
                f"{end_month} {end_day} {year + 1} 23:59:59", dateformat)

        self.start_date, self.end_date = beg_date, end_date


@dataclass
class Pom:
    """A pom, as described, in order, from the database."""
    pom_id: int
    user_id: int
    descript: str
    time_set: datetime
    session: int

    def __lt__(self, other):
        """Return whether the Pom in `other` came before this one.

        This is needed for sorting lists of Poms with `sorted`. `pom_id` is
        used for the comparison because multiple poms can have exactly the
        same time_set and would return false when niether true nor false make
        sense.
        """
        if not isinstance(other, self.__class__):
            raise NotImplementedError(f"Cannot compare with {type(other)}")

        return self.pom_id < other.pom_id

    def is_current_session(self) -> bool:
        """Return whether this pom is in the user's current session."""
        return bool(self.session)


@dataclass
class Event:
    """An event, as described, in order, from the database."""
    event_id: int
    event_name: str
    pom_goal: int
    start_date: datetime
    end_date: datetime


class ActionType(str, Enum):
    """Type of an action in the actions table of the database."""
    # Tech debt: This should be moved to pombot.lib.pom_wars.types.
    NORMAL_ATTACK = 'normal_attack'
    HEAVY_ATTACK = 'heavy_attack'
    DEFEND = 'defend'
    BRIBE = 'bribe'


@dataclass(frozen=True)
class User:
    """A user, as described, in order, from the database."""
    # Tech debt: This should be moved to pombot.lib.pom_wars.types.
    user_id: int
    timezone: timezone
    team: str
    inventory_string: str
    player_level: int
    attack_level: int
    heavy_attack_level: int
    defend_level: int


@dataclass
class Action:
    """An action, as described, in order, from the database."""
    # Tech debt: This should be moved to pombot.lib.pom_wars.types.
    action_id: int
    user_id: int
    team: str
    type: ActionType
    was_successful: bool
    was_critical: bool
    items_dropped: str
    raw_damage: int
    timestamp: datetime

    @property
    def damage(self) -> float:
        """The real damage of this action."""
        if self.raw_damage:
            return self.raw_damage / 100.0

        return 0

    @property
    def is_defend(self) -> bool:
        """Return whether or not the action was a heavy attack."""
        return self.type == ActionType.DEFEND

    @property
    def is_heavy(self) -> bool:
        """Return whether or not the action was a heavy attack."""
        return self.type == ActionType.HEAVY_ATTACK

    @property
    def is_normal(self) -> bool:
        """Return whether or not the action was a heavy attack."""
        return self.type == ActionType.NORMAL_ATTACK


class InstantItem(str, Enum):
    """Type of an instant-use item in the actions table of the database."""
    # Tech debt: This should be moved to pombot.lib.pom_wars.types.
    TEAM_INVINCIBILITY = 'team_invincibility'
    TEAM_DAMAGE_BUFF = 'team_damage_buff'
    TEAM_SUCCESS_CHANCE_BUFF = 'team_success_chance_buff'
