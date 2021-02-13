from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

import pombot
from pombot.config import Config
from pombot.lib.storage import Storage


class TestUserCommands(IsolatedAsyncioTestCase):
    """Test the user commands cog."""
    def setUp(self) -> None:
        """Reconfigure Config to use testing tables."""
        Config.POMS_TABLE = "__TEST__poms"
        Config.EVENTS_TABLE = "__TEST__events"
        return super().asyncSetUp()

    async def test_pom_command_happy_day(self):
        """Test positive case for !pom command."""
        ctx = MagicMock()

        await pombot.commands.do_pom(ctx)
        poms = await Storage.get_poms()

        print(poms)
