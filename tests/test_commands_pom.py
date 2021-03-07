import unittest
from unittest.async_case import IsolatedAsyncioTestCase

from parameterized import parameterized

import pombot
from pombot.config import Config
from pombot.lib.storage import Storage
from tests.helpers import mock_discord


class TestPomCommand(IsolatedAsyncioTestCase):
    """Test the !pom command."""
    async def asyncSetUp(self) -> None:
        """Ensure database tables exist and create contexts for the tests."""
        await Storage.create_tables_if_not_exists()
        await Storage.delete_all_rows_from_all_tables()

    async def asyncTearDown(self) -> None:
        """Cleanup the database."""
        await Storage.delete_all_rows_from_all_tables()

    async def test_pom_command_with_no_args(self):
        """Test the user typing `!pom`."""
        ctx = mock_discord.MockContext()
        ctx.message = mock_discord.MockMessage()

        await pombot.commands.do_pom(ctx)

        pom, = await Storage.get_poms()
        self.assertIsNone(pom.descript)

    async def test_pom_command_with_description(self):
        """Test the user typing `!pom hello world`."""
        ctx = mock_discord.MockContext()
        ctx.message = mock_discord.MockMessage()
        user_provided_description = "hello world"

        args = tuple(user_provided_description.split())
        await pombot.commands.do_pom(ctx, *args)

        pom, = await Storage.get_poms()
        self.assertEqual(user_provided_description, pom.descript)

    @parameterized.expand([
        (1, 1),
        (3, 3),
        (Config.POM_TRACK_LIMIT, Config.POM_TRACK_LIMIT),
        (Config.POM_TRACK_LIMIT + 1, 0),
    ])
    async def test_poms_command_with_numeric_args(
        self,
        number_of_poms,
        expected_number_of_poms,
    ):
        """Test the user typing `!pom <number_of_poms>`."""
        ctx = mock_discord.MockContext()
        ctx.message = mock_discord.MockMessage()

        await pombot.commands.do_pom(ctx, str(number_of_poms))

        poms = await Storage.get_poms()
        self.assertEqual(expected_number_of_poms, len(poms))

    @parameterized.expand([
        (1, 1, "reading"),
        (3, 3, "homework"),
        (Config.POM_TRACK_LIMIT, Config.POM_TRACK_LIMIT, "piano practice"),
        (Config.POM_TRACK_LIMIT + 1, 0, "earth bending"),
    ])
    async def test_poms_command_with_numeric_args_and_descriptions(
        self,
        number_of_poms,
        expected_number_of_poms,
        user_provided_description,
    ):
        """Test the user typing `!pom <number_of_poms> <description>`."""
        ctx = mock_discord.MockContext()
        ctx.message = mock_discord.MockMessage()

        args = tuple((str(number_of_poms), *user_provided_description.split()))
        await pombot.commands.do_pom(ctx, *args)

        poms = await Storage.get_poms()
        self.assertEqual(expected_number_of_poms, len(poms))

        if number_of_poms <= Config.POM_TRACK_LIMIT:
            self.assertTrue(
                all(pom.descript == user_provided_description for pom in poms))


if __name__ == "__main__":
    unittest.main()
