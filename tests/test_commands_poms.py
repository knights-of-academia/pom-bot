import unittest
from unittest.async_case import IsolatedAsyncioTestCase

import pombot
from pombot.lib.storage import Storage
from tests.helpers.mock_discord import MockContext


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

    async def test_poms_command_with_no_args(self):
        """Test the user typing `!poms` with an empty session and bank."""
        self.ctx.invoked_with = "poms"
        await pombot.commands.do_poms(self.ctx)

        # The user was DM'd an embed.
        self.assertTrue(self.ctx.author.send)
        embed_sent_to_user = self.ctx.author.send.call_args.kwargs["embed"]

        # The embed tells the user that no session is active.
        self.assertIn("Session not yet started.", embed_sent_to_user.description)

        # It contains three fields.
        self.assertEqual(3, len(embed_sent_to_user.fields))

        # And the fields contents are as follows.
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

        for expected, actual in zip(expected_fields_sent_to_user,
                                    embed_sent_to_user.fields):
            self.assertEqual(expected["name"], actual.name)
            self.assertEqual(expected["value"], actual.value)
            self.assertEqual(expected["inline"], actual.inline)


if __name__ == "__main__":
    unittest.main()
