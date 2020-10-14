import logging
import random
import textwrap
from typing import Any

import mysql.connector
from discord.ext.commands import Bot, Cog, Context, errors
from discord.message import Message

from pombot.config import Config, Debug, Reactions, Secrets
from pombot.storage import EventSql, PomSql

_log = logging.getLogger(__name__)


def _setup_tables():
    tables = [
        {"name": Config.POMS_TABLE, "query": PomSql.CREATE_TABLE},
        {"name": Config.EVENTS_TABLE, "query": EventSql.CREATE_TABLE},
    ]

    db = mysql.connector.connect(
        host=Secrets.MYSQL_HOST,
        user=Secrets.MYSQL_USER,
        database=Secrets.MYSQL_DATABASE,
        password=Secrets.MYSQL_PASSWORD,
    )
    cursor = db.cursor()

    for query in (table["query"] for table in tables):
        cursor.execute(query)

    if Debug.DROP_TABLES_ON_RESTART:
        _log.info("Deleting tables... ")

        for table_name in (table["name"] for table in tables):
            cursor.execute(f"DELETE FROM {table_name};")

        _log.info("Tables deleted.")
        db.commit()

    cursor.close()
    db.close()


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

        _setup_tables()

        _log.info("READY ON DISCORD AS: %s", self.bot.user)

    @Cog.listener()
    async def on_message(self, message: Message):
        """Limit commands to certain channels or DMs according to the Config.

        This also checks for a single space after the prefix and removes it in
        an attempt to support autocorrect inserting a space after completing a
        word for mobile users.
        """
        try:
            if Config.POM_CHANNEL_NAMES:
                if message.channel.name not in Config.POM_CHANNEL_NAMES:
                    return
        except AttributeError:
            if message.guild is None and not Debug.RESPOND_TO_DM:
                return

        if message.content.startswith(f"{Config.PREFIX} "):
            message.content = "".join(message.content.split(" ", 1))

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
            _log.error(
                'error: user %s (%s) running "%s" hit: %s',
                ctx.author.display_name,
                ctx.author.name + "#" + ctx.author.discriminator,
                ctx.message.content,
                message,
            )

        await ctx.message.add_reaction(Reactions.ERROR)


def setup(bot: Bot):
    """Required to load extention."""
    bot.add_cog(EventListeners(bot))
