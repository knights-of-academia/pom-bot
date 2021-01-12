from pombot.scoreboard import Scoreboard


class State:
    """In-memory bot state."""
    # Scoreboard
    scoreboard: Scoreboard = None

    # Tech debt: this should be in the database.
    goal_reached = False
