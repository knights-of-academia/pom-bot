from datetime import datetime
from typing import Any

from pombot.lib.types import DateRange


def positive_int(value: Any) -> int:
    """Return the provided value if it is a positive whole number. Raise
    ValueError otherwise.
    """
    if (intval := int(value)) < 0:
        raise ValueError(f"Expected a positive integer, got {value}")

    return intval


def str2bool(value: str) -> bool:
    """Coerce a string to a bool based on its value."""
    return value.casefold() in {"yes", "y", "1", "true", "t"}


def daterange_from_timestamp(timestamp: datetime):
    """Get the DateRange of the day containing the given timestamp."""
    get_timestamp_at_time = lambda time: datetime.strptime(
        datetime.strftime(timestamp, f"%Y-%m-%d {time}"), "%Y-%m-%d %H:%M:%S")

    morning = get_timestamp_at_time("00:00:00")
    evening = get_timestamp_at_time("23:59:59")

    return DateRange(morning, evening)
