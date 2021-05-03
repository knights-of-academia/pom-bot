import unittest
from unittest.async_case import IsolatedAsyncioTestCase

import pombot
from tests.helpers import mock_discord


class TestFortuneCommand(IsolatedAsyncioTestCase):
    """Test the !fortune command."""
    ctx = None

    async def asyncSetUp(self) -> None:
        """Create contexts for the tests."""
        self.ctx = mock_discord.MockContext()

    async def test_fortune_responds_to_user(self):
        """Test when the user types !fortune.

        In the SUT, the built-in randomizer is "paused" and `datetime` is
        used to generate a new random seed in the interim. Mocking datetime
        is awkward and the chances of it failing are minimal, so a mock is
        omitted. If this test fails at exactly midnight, just run it again.
        """
        # User calls !fortune once.
        await pombot.commands.do_fortune(self.ctx)
        embeds_sent_to_user = [self.ctx.send.call_args.kwargs.get("embed")]

        # User calls !fortune again.
        await pombot.commands.do_fortune(self.ctx)
        embeds_sent_to_user += [self.ctx.send.call_args.kwargs.get("embed")]

        self.assertEqual(2, self.ctx.send.call_count)

        # We expect the message descriptions to change between calls, but the
        # footer's "lucky numbers" should remain constant.
        first, second = (msg.footer.text for msg in embeds_sent_to_user)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
