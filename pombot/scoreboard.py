from pombot.storage import Storage
from pombot.lib.types import Team
from pombot.config import Pomwars
from pombot.lib.messages import send_embed_message

class Scoreboard:
    """Handle dynamic scoreboard"""
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

    def population(self, team) -> str:
        """
        Returns a string of the population of a team
        """
        team = self.viking_population if team == Team.VIKINGS else self.knight_population

        return str(team)

    def dmg(self, team) -> str:
        """
        Returns a string of the total damage done by a team
        """
        damage = 0
        team = self.viking_actions if team == Team.VIKINGS else self.knight_actions

        for action in team:
            if action.raw_damage > 0:
                damage += int(action.raw_damage/100)

        return str(damage)

    def attack_count(self, team) -> str:
        """
        Returns a string of the total attacks (whether successful or not) of a team
        """
        count = 0
        prettyteam = self.viking_actions if team == Team.VIKINGS else self.knight_actions

        for action in prettyteam:
            action_was_attack = action.type == 'normal_attack' or action.type == 'heavy_attack'
            if action.was_successful and action_was_attack == 1:
                count += 1

        return str(count)

    def favorite_attack(self, team) -> str:
        """
        Returns a string of the most common attack done by a team
        """
        normal_count = 0
        heavy_count = 0

        prettyteam = self.viking_actions if team == Team.VIKINGS else self.knight_actions

        for action in prettyteam:
            if action.type == 'normal_attack':
                normal_count += 1
            elif action.type == 'heavy_attack':
                heavy_count += 1


        if normal_count >= heavy_count:
            fav = 'Normal'
        else:
            fav = 'Heavy'

        return fav # In the rare case it's equal it will return as normal attack

    async def create_msg(self) -> bool:
        """
        Updates (or creates) the live scoreboards of all the guilds the bot is in.
        - Differentiates teams
        - Displays current winner
        - Shows amount of damage done by each team
        - Shows number of attacks done by each team
        - Shows populations
        - Shows favorite attacks
        """
        knight_dmg = self.dmg(Team.KNIGHTS)
        viking_dmg = self.dmg(Team.VIKINGS)

        knight_attacks = self.attack_count(Team.KNIGHTS)
        viking_attacks = self.attack_count(Team.VIKINGS)

        winner = ""
        if knight_dmg != viking_dmg: # To check for ties
            if int(self.dmg(Team.KNIGHTS)) < int(self.dmg(Team.VIKINGS)):
                winner = 'viking'
            else:
                winner = 'knight'

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
                            win=(f" {Pomwars.Emotes.WINNER}" if winner=='knight' else ''),
                        ),
                        "\n".join(lines).format(**knight_values),
                        True
                    ],
                    [
                        "{emt} Vikings{win}".format(
                            emt=Pomwars.Emotes.VIKING,
                            win=f" {Pomwars.Emotes.WINNER}" if winner=='viking' else '',
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
                message, = await history.flatten()
                fields = [
                    [
                        "{emt} Knights{win}".format(
                            emt=Pomwars.Emotes.KNIGHT,
                            win=f" {Pomwars.Emotes.WINNER}" if winner=='knight' else '',
                        ),
                        "\n".join(lines).format(**knight_values),
                        True
                    ],
                    [
                        "{emt} Vikings{win}".format(
                            emt=Pomwars.Emotes.VIKING,
                            win=f" {Pomwars.Emotes.WINNER}" if winner=='viking' else '',
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
                    _func=message.send,
                )

        return True
