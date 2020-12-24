import logging

from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.bot import Bot

_log = logging.getLogger(__name__)


class PomWarsAdminCommands(commands.Cog):
    """Commands used by admins during a Pom War."""
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.has_any_role("Guardian")
    async def unload_pom_wars(self, ctx: Context):
        """Manually unload the pombot.cogs.pom_wars_commands."""
        await ctx.send("Unloading cog.")
        self.bot.unload_extension("pombot.cogs.pom_wars_commands")


class PomWarsUserCommands(commands.Cog):
    """Commands used by users during a Pom War."""
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def attack(self, ctx: Context, *args):
        """Attack the other team."""
        await ctx.send(f"Attack called {' '.join(args)}")


def setup(bot: Bot):
    """Required to load extension."""
    bot.add_cog(PomWarsAdminCommands(bot))
    bot.add_cog(PomWarsUserCommands(bot))
