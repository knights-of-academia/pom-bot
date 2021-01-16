from asyncio import ProactorEventLoop


class State:
    """In-memory bot state."""
    # Discord creates an event loop for us. Instead of creating a new one, we
    # can hook into the existing event loop to call our storage later.
    event_loop: ProactorEventLoop = None

    # pombot.scoreboard.Scoreboard object to preserve and dynamically update
    # scoreboard channels in Pomwar events.
    scoreboard = None

    # Tech debt: this should be in the database.
    goal_reached: bool = False
