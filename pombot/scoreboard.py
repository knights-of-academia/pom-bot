from collections import Counter

import discord.errors

from pombot.storage import Storage
from pombot.lib.types import ActionType, Team
from pombot.config import Pomwars, Reactions
from pombot.lib.messages import send_embed_message

class Scoreboard:
    """A representation of the scoreboard in join channels."""
    def __init__(self, bot, scoreboard_channels) -> None:
        self.bot = bot
        self.scoreboard_channels = scoreboard_channels
        self.update_vars()

    def update_vars(self) -> None:
        """Updates variables"""
        self.knight_population, self.viking_population = Storage.get_team_populations()
        self.knight_attack_count, self.viking_attack_count = Storage.get_team_attack_counts()
        self.knight_dmg, self.viking_dmg = Storage.get_team_damages()
        self.knight_fav_attack, self.viking_fav_attack = Storage.get_team_fav_attacks()

    async def update_msg(self):
        """
        Updates (or creates) the live scoreboards of all the guilds the bot is in.
        - Differentiates teams
        - Displays current winner
        - Shows amount of damage done by each team
        - Shows number of attacks done by each team
        - Shows populations
        - Shows favorite attacks
        """

        self.update_vars()

        full_channels, restricted_channels = [], []

        winner = ""
        if self.knight_dmg != self.viking_dmg: # To check for ties
            if self.knight_dmg < self.viking_dmg:
                winner = Team.VIKINGS
            else:
                winner = Team.KNIGHTS

        for channel in self.scoreboard_channels:
            history = channel.history(limit=1, oldest_first=True)

            knight_fav_str = 'None'
            if self.knight_fav_attack == ActionType.NORMAL_ATTACK:
                knight_fav_str = 'Normal'
            elif self.knight_fav_attack == ActionType.HEAVY_ATTACK:
                knight_fav_str = 'Heavy'

            knight_values = {
                "dmg": self.knight_dmg,
                "emt": f"{Pomwars.Emotes.ATTACK}",
                "fav": knight_fav_str,
                "attacks": self.knight_attack_count,
                "participants": self.knight_population,
            }

            viking_fav_str = 'None'
            if self.viking_fav_attack == ActionType.NORMAL_ATTACK:
                viking_fav_str = 'Normal'
            elif self.viking_fav_attack == ActionType.HEAVY_ATTACK:
                viking_fav_str = 'Heavy'

            viking_values = {
                "dmg": self.viking_dmg,
                "emt": f"{Pomwars.Emotes.ATTACK}",
                "fav": viking_fav_str,
                "attacks": self.viking_attack_count,
                "participants": self.viking_population,
            }

            lines = [
                "{dmg} damage dealt {emt}",
                "** **",
                "`Attacks:` {attacks} attacks",
                "`Favorite Attack:` {fav}",
                "`Member Count:` {participants} participants",
            ]

            team_fields_inline = True
            msg_fields = [
                [
                    "{emt} Knights{win}".format(
                        emt=Pomwars.Emotes.KNIGHT,
                        win=f" {Pomwars.Emotes.WINNER}" if winner==Team.KNIGHTS else '',
                    ),
                    "\n".join(lines).format(**knight_values),
                    team_fields_inline
                ],
                [
                    "{emt} Vikings{win}".format(
                        emt=Pomwars.Emotes.VIKING,
                        win=f" {Pomwars.Emotes.WINNER}" if winner==Team.VIKINGS else '',
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
