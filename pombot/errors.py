"""Collection of Pombot's errors."""


class EventError(Exception):
    "Base exception for event errors."


class EventCreationError(EventError):
    "Failed to create event."


class TooManyEventsError(EventError):
    "Too many ongoing events."
