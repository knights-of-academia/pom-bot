import random
import string
import unittest
from unittest.async_case import IsolatedAsyncioTestCase

from discord.embeds import Embed
from parameterized import parameterized

import pombot
from pombot.config import Config
from pombot.lib.storage import Storage
from tests.helpers.mock_discord import MockContext
from tests.helpers.semantics import assert_not_raises


class TestPomsCommand(IsolatedAsyncioTestCase):
    """Test the !poms command."""
    ctx = None

    async def asyncSetUp(self) -> None:
        """Ensure database tables exist and create contexts for the tests."""
        self.ctx = MockContext()
        await Storage.create_tables_if_not_exists()
        await Storage.delete_all_rows_from_all_tables()

    async def asyncTearDown(self) -> None:
        """Cleanup the database."""
        await Storage.delete_all_rows_from_all_tables()

    @parameterized.expand(["!poms", "!poms.show"])
    async def test_poms_command_with_no_args(self, invoked_with: str):
        """Test the user typing `!poms` and `!poms.show` with an empty
        session and bank.
        """
        self.ctx.invoked_with = invoked_with.removeprefix("!")
        await pombot.commands.do_poms(self.ctx)

        if response_is_public := self.ctx.invoked_with in Config.PUBLIC_POMS_ALIASES:
            self.assertEqual(1, self.ctx.message.reply.call_count)
            embed_sent_to_user = self.ctx.message.reply.call_args.kwargs["embed"]
        else:
            self.assertEqual(1, self.ctx.author.send.call_count)
            embed_sent_to_user = self.ctx.author.send.call_args.kwargs["embed"]

        if response_is_public:
            self.assertEqual(Embed.Empty, embed_sent_to_user.description)

            expected_fields_sent_to_user = [
                {
                    "name": "**Current Session**",
                    "value": "Start your session by doing\nyour first !pom.\n",
                    "inline": True,
                },
            ]
        else:
            self.assertIn("Session not yet started.", embed_sent_to_user.description)

            expected_fields_sent_to_user = [
                {
                    "name": "**Banked Poms**",
                    "value": "Bank the poms in your current\nsession to add them here!\n",
                    "inline": True,
                },
                {
                    "name": "\u200b",  # Zero-width space.
                    "value": "\u200b",  # Zero-width space.
                    "inline": True,
                },
                {
                    "name": "**Current Session**",
                    "value": "Start your session by doing\nyour first !pom.\n",
                    "inline": True,
                },
            ]

        self.assertEqual(len(expected_fields_sent_to_user),
                         len(embed_sent_to_user.fields))

        for expected, actual in zip(expected_fields_sent_to_user,
                                    embed_sent_to_user.fields):
            self.assertEqual(expected["name"], actual.name)
            self.assertEqual(expected["value"], actual.value)
            self.assertEqual(expected["inline"], actual.inline)

    async def test_embed_too_long_causes_normal_message(self):
        """Test the user typing `!poms` when the response of the message
        would exceed Discord limits.
        """
        # Deterministically generate pom descriptions.
        random.seed(42)

        # Make our combined pom descriptions over 6,000 characters.
        descriptions = ("".join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(30)) for _ in range(201))
        await Storage.add_poms_to_user_session(self.ctx.author, descriptions, 1)

        with assert_not_raises():
            self.ctx.invoked_with = "poms"
            await pombot.commands.do_poms(self.ctx)

        pass


if __name__ == "__main__":
    unittest.main()
