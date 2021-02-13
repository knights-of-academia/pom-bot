from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.bot import Bot

import pombot


class UserCommands(commands.Cog):
    """Handlers for user-level pom commands."""
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def pom(self, ctx: Context, *, description: str = None):
        """Add a new pom.

        If the first word in the description is a number (1-10), multiple
        poms will be added with the given description.

        Additionally, find out if there is an ongoing event, and, if so, mark
        the event as completed if this is the final pom in the event.
        """
        await pombot.commands.do_pom(ctx, description)

    @commands.command()
    async def poms(self, ctx: Context):
        """See your poms.

        See details for your tracked poms and the current session.
        """
        await pombot.commands.do_poms(ctx)

    @commands.command()
    async def howmany(self, ctx: Context, *, description: str = None):
        """List your poms with a given description."""
        await pombot.commands.do_howmany(ctx, description)

    @commands.command()
    async def undo(self, ctx: Context):
        """Undo/remove your latest poms."""
        await pombot.commands.do_undo(ctx)

    @commands.command()
    async def newleaf(self, ctx: Context):
        """Turn over a new leaf.

        Hide the details of your previously tracked poms and start a new
        session.
        """
        await pombot.commands.do_newleaf(ctx)

    @commands.command(hidden=True)
    async def reset(self, ctx: Context):
        """Permanently deletes all of your poms. This cannot be undone."""
        await pombot.commands.do_reset(ctx)

    @commands.command()
    async def events(self, ctx: Context):
        """See the current and next events."""
        await pombot.commands.do_events(ctx)


def setup(bot: Bot):
    """Required to load extension."""
    bot.add_cog(UserCommands(bot))
