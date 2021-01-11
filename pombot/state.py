from typing import List

from discord.channel import TextChannel

class State:  # pylint: disable=too-few-public-methods
    """In-memory state of whether or not the goal of the ongoing-event has
    been reached.

    Techdebt: This value should be stored in the DB and this file should not
    exist.
    """
    goal_reached = False
    SCOREBOARD_CHANNELS: List[TextChannel] = []
    score = None