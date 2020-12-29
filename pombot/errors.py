"""Collection of Pombot's errors."""


class EventError(Exception):
    "Base exception for event errors."


class EventCreationError(EventError):
    "Failed to create event."


class TooManyEventsError(EventError):
    "Too many ongoing events."


class PomWarsError(Exception):
    """Base exception for errors relating to Pom Wars."""
    def __init__(self):
        super().__init__(self.__class__.__doc__)


class InvalidNumberOfRolesError(PomWarsError):
    """Either not enough or too many roles are applied to the user."""
