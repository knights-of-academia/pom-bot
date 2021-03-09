from asyncio import ProactorEventLoop


class State:
    """In-memory bot state."""
    # Discord creates an event loop for us. Instead of creating a new one, we
    # can hook into the existing event loop to call our storage later.
    event_loop: ProactorEventLoop = None

    # Scoreboard object to preserve and dynamically update scoreboard channels
    # during Pomwar events.
    # NOTE: The type is not imported to avoid a circular import.
    scoreboard = None

    # Tech debt: This should be a column in the events table of the DB.
    goal_reached: bool = False
