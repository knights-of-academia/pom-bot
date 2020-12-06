import logging
import random
import textwrap
from typing import Any

from discord.ext.commands import Bot, Cog, Context, errors
from pombot.config import Config, Debug, Reactions, Secrets
from pombot.storage import Storage

_log = logging.getLogger(__name__)


async def _send_to_errors_channel(ctx: Context, message: str):
    if not Config.ERRORS_CHANNEL_NAME:
        _log.info("ERRORS_CHANNEL_NAME not configured")
        return

    if ctx.guild is None:
        return

    for channel in ctx.guild.channels:
        if channel.name == Config.ERRORS_CHANNEL_NAME:
            await channel.send("```\n" + message + "```")
            break
    else:
        _log.info("ERRORS_CHANNEL_NAME not found on context guild")


class EventListeners(Cog):
    """Handle global events for the bot."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        """Startup procedure after bot has logged into Discord."""
        _log.info("MYSQL_DATABASE: %s", Secrets.MYSQL_DATABASE)

        active_channels = ", ".join(f"#{channel}"
                                    for channel in Config.POM_CHANNEL_NAMES)
        _log.info("POM_CHANNEL_NAMES: %s", active_channels or "ALL CHANNELS")

        debug_options_enabled = ", ".join([k for k, v in vars(Debug).items() if v is True])
        if debug_options_enabled:
            debug_enabled_message = textwrap.dedent(f"""\
                ************************************************************
                DEBUG OPTIONS ENABLED: {debug_options_enabled}
                ************************************************************\
            """)

            for line in debug_enabled_message.split("\n"):
                _log.info(line)

        Storage.create_tables_if_not_exists()

        if Debug.DROP_TABLES_ON_RESTART:
            if not __debug__:
                msg = ("This bot is unwilling to drop tables in production. "
                       "Please review your configuration.")

                await self.bot.close()
                raise RuntimeError(msg)

            Storage.delete_all_rows_from_all_tables()

        _log.info("READY ON DISCORD AS: %s", self.bot.user)

    @Cog.listener()
    async def on_command_error(self, ctx: Context, error: Any):
        """Alert users when using commands to which they have no permission.
        In unknown cases, log the error and mark it in discord.
        """
        if isinstance(error, errors.CommandNotFound):
            # Multiple bots can run on a single guild. We should not respond to
            # all commands we don't implement.
            return

        if isinstance(error, errors.CheckFailure):
            message, *_ = random.choices([
                "You do not have access to this command.",
                "Sorry, that command is out-of-order.",
                "!!! ACCESS DENIED !!! \\**whale noises\\**",
                "Wir konnten die Smaragde nicht finden!",
                "Do you smell that?",
                "\\**(Windows XP startup sound)\\**",
                "This is not the command you're looking for. \\**waves hand\\**",
                "*noop*",
                "Command permenently moved to a different folder.",
                "This ~~princess~~ command is in another castle.",
                "Okay, let me get my tools.. brb",
                "(╯°□°）╯︵ ¡ƃuoɹʍ ʇuǝʍ ƃuıɥʇǝɯoS",
            ])

            await ctx.message.add_reaction(Reactions.ROBOT)
            await ctx.send(message)
            return

        for message in error.args:
            error_message = 'User {} ({}) running "{}" hit: {}'.format(
                ctx.author.display_name,
                ctx.author.name + "#" + ctx.author.discriminator,
                ctx.message.content,
                message,
            )

            _log.error("%s", error_message)
            await _send_to_errors_channel(ctx, error_message)

        await ctx.message.add_reaction(Reactions.ERROR)


def setup(bot: Bot):
    """Required to load extension."""
    bot.add_cog(EventListeners(bot))
