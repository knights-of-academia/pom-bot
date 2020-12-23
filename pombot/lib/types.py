from dataclasses import dataclass
from datetime import datetime


@dataclass
class DateRange:
    """An inclusive range of dates."""
    start_date: datetime
    end_date: datetime

    def __str__(self):
        fmt = lambda dt: datetime.strftime(dt, "%B %d, %Y")
        return f"{fmt(self.start_date)} - {fmt(self.end_date)}"


@dataclass
class Pom:
    """A pom, as described, in order, from the database."""
    pom_id: int
    user_id: int
    descript: str
    time_set: datetime
    session: int

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
