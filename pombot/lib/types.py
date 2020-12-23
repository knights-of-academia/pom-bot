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
        if len(args) == 2 and all(isinstance(_, datetime) for _ in args):
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

        # return super().__new__(cls, beg_date, end_date)
        self.start_date, self.end_date = beg_date, end_date


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
