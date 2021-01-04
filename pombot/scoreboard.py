import discord.errors

from pombot.storage import Storage
from pombot.lib.types import ActionType, Team
from pombot.config import Pomwars, Reactions
from pombot.lib.messages import send_embed_message

from collections import Counter

class Scoreboard:
    """A representation of the scoreboard in join channels."""
    def __init__(self, bot, scoreboard_channels) -> None:
        self.bot = bot
        self.scoreboard_channels = scoreboard_channels
        self.knight_population, self.viking_population = Storage.get_team_populations()
        self.knight_actions = Storage.get_actions(
            team=Team.KNIGHTS,
        )
        self.viking_actions = Storage.get_actions(
            team=Team.VIKINGS,
        )

    def update_vars(self) -> None:
        """Updates variables"""
        self.knight_population, self.viking_population = Storage.get_team_populations()
        self.knight_actions = Storage.get_actions(
            team=Team.KNIGHTS,
        )
        self.viking_actions = Storage.get_actions(
            team=Team.VIKINGS,
        )

    def population(self, team) -> int:
        """
        Returns a string of the population of a team
        """
        self.update_vars()

        team = self.viking_population if team == Team.VIKINGS else self.knight_population

        return team

    def dmg(self, team) -> int:
        """
        Returns a string of the total damage done by a team
        """
        self.update_vars()

        damage = 0
        team = self.viking_actions if team == Team.VIKINGS else self.knight_actions

        for action in team:
            if action.raw_damage > 0:
                damage += int(action.raw_damage/100)

        return damage

    def attack_count(self, team) -> int:
        """
        Returns a string of the total attacks (whether successful or not) of a team
        """
        
        self.update_vars()

        team_actions = self.viking_actions if team == Team.VIKINGS else self.knight_actions

        attack_counts = Counter([
            action.type in [ActionType.NORMAL_ATTACK, ActionType.HEAVY_ATTACK] and action.was_successful
            for action in team_actions
        ])

        return attack_counts[1] # Only the actions that were attacks and were successful

    def favorite_attack(self, team) -> str:
        """
        Returns a string of the most common attack done by a team
        """
        
        self.update_vars()

        team_actions = self.viking_actions if team == Team.VIKINGS else self.knight_actions

        type_counts = Counter([action.type for action in team_actions])

        if type_counts['normal_attack'] >= type_counts['heavy_attack']:
            fav = 'Normal'
        else:
            fav = 'Heavy'

        return fav

    async def update_msg(self, handle_exceptions=False):
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

        knight_dmg = self.dmg(Team.KNIGHTS)
        viking_dmg = self.dmg(Team.VIKINGS)

        knight_attacks = self.attack_count(Team.KNIGHTS)
        viking_attacks = self.attack_count(Team.VIKINGS)

        winner = ""
        if knight_dmg != viking_dmg: # To check for ties
            if int(self.dmg(Team.KNIGHTS)) < int(self.dmg(Team.VIKINGS)):
                winner = Team.KNIGHTS
            else:
                winner = Team.VIKINGS

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
                "dmg": knight_dmg,
                "emt": f"{Pomwars.Emotes.ATTACK}",
                "fav": self.favorite_attack(Team.KNIGHTS),
                "attacks": knight_attacks,
                "participants": self.population(Team.KNIGHTS),
            }

            viking_values = {
                "dmg": viking_dmg,
                "emt": f"{Pomwars.Emotes.ATTACK}",
                "fav": self.favorite_attack(Team.VIKINGS),
                "attacks": viking_attacks,
                "participants": self.population(Team.VIKINGS),
            }

            try:
                message, = await history.flatten()

                fields = [
                    [
                        "{emt} Knights{win}".format(
                            emt=Pomwars.Emotes.KNIGHT,
                            win=(f" {Pomwars.Emotes.WINNER}" if winner==Team.KNIGHTS else ''),
                        ),
                        "\n".join(lines).format(**knight_values),
                        True
                    ],
                    [
                        "{emt} Vikings{win}".format(
                            emt=Pomwars.Emotes.VIKING,
                            win=f" {Pomwars.Emotes.WINNER}" if winner==Team.VIKINGS else '',
                        ),
                        "\n".join(lines).format(**viking_values),
                        True
                    ]
                ]
                await send_embed_message(
                    None,
                    title=None,
                    description=None,
                    icon_url=None,
                    fields=fields,
                    colour=Pomwars.ACTION_COLOUR,
                    _func=message.edit,
                )
            except ValueError:
                try:
                    fields = [
                        [
                            "{emt} Knights{win}".format(
                                emt=Pomwars.Emotes.KNIGHT,
                                win=f" {Pomwars.Emotes.WINNER}" if winner==Team.KNIGHTS else '',
                            ),
                            "\n".join(lines).format(**knight_values),
                            True
                        ],
                        [
                            "{emt} Vikings{win}".format(
                                emt=Pomwars.Emotes.VIKING,
                                win=f" {Pomwars.Emotes.WINNER}" if winner==Team.VIKINGS else '',
                            ),
                            "\n".join(lines).format(**viking_values),
                            True
                        ]
                    ]
                    msg = await send_embed_message(
                        None,
                        title=None,
                        description=None,
                        icon_url=None,
                        fields=fields,
                        colour=Pomwars.ACTION_COLOUR,
                        _func=channel.send,
                    )
                    await msg.add_reaction(Reactions.WAR_JOIN_REACTION)
                except discord.errors.Forbidden:
                    restricted_channels.append(channel)
            except discord.errors.Forbidden:
                restricted_channels.append(channel)
            else:
                if message.author != self.bot.user:
                    full_channels.append(channel)

        if handle_exceptions:
            return [full_channels, restricted_channels]
        else:
            return True
            
