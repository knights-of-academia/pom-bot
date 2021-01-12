from typing import List

import discord.errors
from discord.channel import ChannelType

from pombot.config import Pomwars, Reactions
from pombot.lib.messages import send_embed_message
from pombot.lib.types import Team


class Scoreboard:
    """A representation of the scoreboard in join channels."""
    def __init__(self, bot, scoreboard_channels) -> None:
        self.bot = bot
        self.scoreboard_channels = scoreboard_channels

    async def update(self) -> List[ChannelType]:
        """Updates or creates the live scoreboards of all guilds.

        The scoreboard:
            - Differentiates teams.
            - Displays current winner.
            - Shows amount of damage done by each team.
            - Shows number of attacks done by each team.
            - Shows populations.
            - Shows favorite attacks.

        @returns Two lists of channels.
            - The first is a list of channels in which a message has already
              been sent, and it is not authored by the bot.
            - The second list contains channels wherein the bot has no
              permission to post.
        """
        full_channels, restricted_channels = [], []
        knights, vikings = Team.KNIGHTS, Team.VIKINGS
        winner = None

        stats = {
            knights: {
                "damage":      knights.damage,
                "fav_attack":  knights.favorite_action,
                "population":  knights.population,
                "num_attacks": knights.attack_count,
            },
            vikings: {
                "damage":      vikings.damage,
                "fav_attack":  vikings.favorite_action,
                "population":  vikings.population,
                "num_attacks": vikings.attack_count,
            }
        }

        if stats[knights] != stats[vikings]:
            winner = knights if stats[vikings]["damage"] < stats[knights]["damage"] else vikings

        for channel in self.scoreboard_channels:
            history = channel.history(limit=1, oldest_first=True)

            lines = [
                "{dmg} damage dealt {emt}",
                "** **",
                "`Attacks:` {attacks} attacks",
                "`Favorite Attack:` {fav}",
                "`Member Count:` {participants} participants",
            ]

            knight_values = {
                "dmg": stats[knights]["damage"],
                "emt": Pomwars.Emotes.ATTACK,
                "fav": stats[knights]["fav_attack"],
                "attacks": stats[knights]["num_attacks"],
                "participants": stats[knights]["population"],
            }

            viking_values = {
                "dmg": stats[vikings]["damage"],
                "emt": Pomwars.Emotes.ATTACK,
                "fav": stats[vikings]["fav_attack"],
                "attacks": stats[vikings]["num_attacks"],
                "participants": stats[vikings]["population"],
            }

            team_fields_inline = True
            msg_fields = [
                [
                    "{emt} Knights{win}".format(
                        emt=Pomwars.Emotes.KNIGHT,
                        win=f" {Pomwars.Emotes.WINNER}" if winner==knights else "",
                    ),
                    "\n".join(lines).format(**knight_values),
                    team_fields_inline
                ],
                [
                    "{emt} Vikings{win}".format(
                        emt=Pomwars.Emotes.VIKING,
                        win=f" {Pomwars.Emotes.WINNER}" if winner==vikings else "",
                    ),
                    "\n".join(lines).format(**viking_values),
                    team_fields_inline
                ]
            ]

            msg_title = "Pom War Season 3 Warboard"
            msg_footer = f"React with {Reactions.WAR_JOIN_REACTION} to join a team!"

            channel_messages = await history.flatten()
            scoreboard_msg = None

            if channel_messages:
                scoreboard_msg = channel_messages[0]
                if scoreboard_msg.author != self.bot.user:
                    full_channels.append(channel)
                    continue

            try:
                new_msg = await send_embed_message(
                    None,
                    title=msg_title,
                    description=None,
                    fields=msg_fields,
                    footer=msg_footer,
                    colour=Pomwars.ACTION_COLOUR,
                    _func=scoreboard_msg.edit if scoreboard_msg else channel.send
                )
                if new_msg:
                    await new_msg.add_reaction(Reactions.WAR_JOIN_REACTION)
            except discord.errors.Forbidden:
                restricted_channels.append(channel)

        return [full_channels, restricted_channels]
