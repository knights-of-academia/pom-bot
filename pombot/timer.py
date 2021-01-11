import asyncio
from functools import partial

from discord.user import User
from discord.channel import TextChannel

from pombot.config import Pomwars, Config
from pombot.lib.messages import send_embed_message

class Timer:
    """Alerts the user when the timer is up."""
    def __init__(self, bot, user: User, title: str, channel: TextChannel) -> None:
        self.bot = bot
        self.user = user
        self.title = title
        self.channel = channel

    async def start_timer(self) -> None:
        """Starts a new timer, creating a new entry in the database and waiting for 25 minutes to ping you."""
        time = Config.POM_TIME * 60

        await asyncio.sleep(time)

        await self.alert()

    async def alert(self) -> None:
        """Alerts you when the timer is done."""
        await send_embed_message(
            None,
            title="Your timer is up!",
            description='Your `{title}` timer has finished! You can now log a pom using any action of your choosing!'.format(
                title=self.title,
            ),
            colour=Pomwars.ACTION_COLOUR,
            icon_url=None,
            _func=partial(self.channel.send, content=self.user.mention),
        )