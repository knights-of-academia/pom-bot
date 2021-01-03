
from discord.ext.commands.bot import Bot
from discord.channel import TextChannel
from typing import List

from pombot.storage import Storage
from pombot.lib.types import Team
from pombot.config import Config, Pomwars
from pombot.lib.messages import send_embed_message

SCOREBOARD_CHANNELS: List[TextChannel] = []

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
        team = self.viking_population if team == Team.VIKINGS else self.knight_population

        return str(team)

    def dmg(self, team) -> str:
        damage = 0
        team = self.viking_actions if team == Team.VIKINGS else self.knight_actions

        for action in team:
            if (action.raw_damage > 0):
                damage += int(action.raw_damage/100)
        
        return str(damage)

    def attack_count(self, team) -> str:
        count = 0
        prettyteam = self.viking_actions if team == Team.VIKINGS else self.knight_actions

        for action in prettyteam:
            if (action.type == 'normal_attack' or action.type == 'heavy_attack'):
                count += 1
        
        return str(count)

    def favorite_attack(self, team) -> str:
        normal_count = 0
        heavy_count = 0

        prettyteam = self.viking_actions if team == Team.VIKINGS else self.knight_actions

        for action in prettyteam:
            if (action.type == 'normal_attack'):
                normal_count += 1
            elif (action.type == 'heavy_attack'):
                heavy_count += 1

        fav = 'Normal' if normal_count >= heavy_count else 'Heavy'
        
        return fav # In the rare case it's equal it will return as normal attack

    async def create_msg(self) -> bool:
        knight_dmg = self.dmg(Team.KNIGHTS)
        viking_dmg = self.dmg(Team.VIKINGS)

        knight_attacks = self.attack_count(Team.KNIGHTS)
        viking_attacks = self.attack_count(Team.VIKINGS)

        winner = ""
        if knight_dmg != viking_dmg: # To check for ties
            winner = 'viking' if int(self.dmg(Team.KNIGHTS)) < int(self.dmg(Team.VIKINGS)) else 'knight'

        for channel in self.scoreboard_channels:
            history = channel.history(limit=1, oldest_first=True)

            try:
                message, = await history.flatten()
                fields = [
                    [
                        "{emt} Knights{win}".format(
                            emt=Pomwars.Emotes.KNIGHT,
                            win=f" {Pomwars.Emotes.WINNER}" if winner=='knight' else '',
                        ),
                        "{dmg} damage dealt {emt}\n** **\n`Attacks:` {attacks} attacks\n`Favorite Attack:` {fav}\n`Member Count:` {participants} participants".format(
                            dmg=knight_dmg,
                            emt=f"{Pomwars.Emotes.ATTACK}",
                            fav=self.favorite_attack(Team.KNIGHTS),
                            attacks=knight_attacks,
                            participants=self.population(Team.KNIGHTS),
                        ),
                        True
                    ],
                    [
                        "{emt} Vikings{win}".format(
                            emt=Pomwars.Emotes.VIKING,
                            win=f" {Pomwars.Emotes.WINNER}" if winner=='viking' else '',
                        ),
                        "{dmg} damage dealt {emt}\n** **\n`Attacks:` {attacks} attacks\n`Favorite Attack:` {fav}\n`Member Count:` {participants} participants".format(
                            dmg=viking_dmg,
                            emt=f"{Pomwars.Emotes.ATTACK}",
                            fav=self.favorite_attack(Team.VIKINGS),
                            attacks=viking_attacks,
                            participants=self.population(Team.VIKINGS),
                        ),
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
                        "{dmg} damage dealt {emt}\n** **\n`Attacks:` {attacks} attacks\n`Favorite Attack:` {fav}\n`Member Count:` {participants} participants".format(
                            dmg=self.dmg(Team.KNIGHTS),
                            emt=f"{Pomwars.Emotes.ATTACK}",
                            fav=self.favorite_attack(Team.KNIGHTS),
                            attacks=self.attack_count(Team.KNIGHTS),
                            participants=self.population(Team.KNIGHTS),
                        ),
                        True
                    ],
                    [
                        "{emt} Vikings{win}".format(
                            emt=Pomwars.Emotes.VIKING,
                            win=f" {Pomwars.Emotes.WINNER}" if winner=='viking' else '',
                        ),
                        "{dmg} damage dealt {emt}\n** **\n`Attacks:` {attacks} attacks\n`Favorite Attack:` {fav}\n`Member Count:` {participants} participants".format(
                            dmg=self.dmg(Team.VIKINGS),
                            emt=f"{Pomwars.Emotes.ATTACK}",
                            fav=self.favorite_attack(Team.VIKINGS),
                            attacks=self.attack_count(Team.VIKINGS),
                            participants=self.population(Team.VIKINGS),
                        ),
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
                    _func=message.send,
                )

        return True