"""mock_discord.py - A set of custom mock objects to aid in creating unit
tests.

Gracelessly borrowed from `python-discord` and modified to work for this
bot's unit tests.

https://github.com/python-discord/bot/blob/master/tests/helpers.py (commit
688908d on Dec 19, 2020)

Modifications to the original work:
    - Discord license agreement added to beginning of discord code.
    - Some functionality disabled.
    - Some MagicMocks converted to AsyncMockMixins.
    - `pending` attribute removed from CustomMockMixin.
    - Default `discriminator` attribute added to MockMember
    - Default `message` attribute added to MockContext.
    - Subclass AsyncMock to API exceptions (AsyncCheckRaiseResponse)
    - AsyncCheckRaiseResponse `send` attribute added to MockContext.
    - AsyncCheckRaiseResponse `reply` attribute added to MockMessage.
    - Various Pylint warnings ignored.
"""
# pylint: disable=access-member-before-definition
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-ancestors

### python-discord/bot/tests/helpers.py ########################################
# MIT License
#
# Copyright (c) 2018 Python Discord
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from __future__ import annotations

import collections
import itertools
import logging
import unittest.mock
from asyncio import AbstractEventLoop
from typing import Iterable, Optional

import discord
# from aiohttp import ClientSession
from discord.ext.commands import Bot, Context

# from bot.api import APIClient
# from bot.async_stats import AsyncStatsClient
# from bot.bot import Bot
# from tests._autospec import autospec  # noqa: F401 other modules import it via this module
from pombot.data import Limits
from pombot.lib.tiny_tools import normalize_and_dedent


for logger in logging.Logger.manager.loggerDict.values():
    # Set all loggers to CRITICAL by default to prevent screen clutter during testing

    if not isinstance(logger, logging.Logger):
        # There might be some logging.PlaceHolder objects in there
        continue

    logger.setLevel(logging.CRITICAL)


class AsyncCheckRaiseResponse(unittest.mock.AsyncMock):
    """Mock what would be Discord API errors as Python exceptions in the same
    way that Disocrd.py will at runtime.

    See:
    https://canary.discord.com/developers/docs/resources/channel#embed-limits
    """
    async def __await__(self, *args, **kwargs):
        """Become awaitable."""

    # `__call__` is only used in Discord mocking even though everything is
    # awaited, so we need to ignore Pylint warnings and make the rest of the
    # mock object awaitable.
    async def __call__(self, *args, **kwargs):  # pylint: disable=invalid-overridden-method
        """Inspect the passed arguements and raise HTTPException where the
        Discord API would respond with HTTP 400 in the wild.
        """
        # Call super() first because it sets call counts and called args. We
        # still want to investigate that stuff even if we raise.
        super().__call__(*args, **kwargs)

        if args and sum(len(a) for a in args) > Limits.MAX_CHARACTERS_PER_MESSAGE:
            self.raise_bad_request("args")

        if not (embed := kwargs.get("embed")):
            return

        total_embed_length = 0

        for attr, max_attr_length in (
            ("title",       Limits.MAX_EMBED_TITLE),
            ("description", Limits.MAX_EMBED_DESCRIPTION),
            ("fields",      Limits.MAX_NUM_EMBED_FIELDS),
            ("footer",      Limits.MAX_EMBED_FOOTER_TEXT),
        ):
            try:
                attr_length = len(getattr(embed, attr, None))
            except TypeError:
                continue
            if attr_length > max_attr_length:
                self.raise_bad_request(f"embed {attr}")
            total_embed_length += attr_length

        # When `fields` is not specified, it's an empty list.
        for index, field in enumerate(embed.fields):
            for attr, max_attr_length in (
                ("name",  Limits.MAX_EMBED_FIELD_NAME),
                ("value", Limits.MAX_EMBED_FIELD_VALUE),
            ):
                try:
                    attr_length = len(getattr(field, attr, None))
                except TypeError:
                    continue
                if attr_length > max_attr_length:
                    await self.raise_bad_request(normalize_and_dedent(f"""\
                        Attribute too big: embed.fields[{index}].{attr}:
                        {attr_length} (MAX {max_attr_length})
                    """))
                total_embed_length += attr_length

        if author_name := getattr(embed.author, "name", None):
            if len(author_name) > Limits.MAX_EMBED_AUTHOR_NAME:
                self.raise_bad_request("embed author name")
            total_embed_length += len(author_name)

        if total_embed_length > Limits.MAX_CHARACTERS_PER_EMBED:
            self.raise_bad_request("total embed length is OVER 6,000!")

    @staticmethod
    async def raise_bad_request(data_category: str):
        response = unittest.mock.MagicMock()
        response.status = 400
        message = f"Bad Request data too big: {data_category}"
        raise discord.errors.HTTPException(response, message)


class HashableMixin(discord.mixins.EqualityComparable):
    """
    Mixin that provides similar hashing and equality functionality as discord.py's `Hashable` mixin.

    Note: discord.py`s `Hashable` mixin bit-shifts `self.id` (`>> 22`); to prevent hash-collisions
    for the relative small `id` integers we generally use in tests, this bit-shift is omitted.
    """

    def __hash__(self):
        return self.id


class ColourMixin:
    """A mixin for Mocks that provides the aliasing of color->colour like discord.py does."""

    @property
    def color(self) -> discord.Colour:
        return self.colour

    @color.setter
    def color(self, color: discord.Colour) -> None:
        self.colour = color


class CustomMockMixin:
    """
    Provides common functionality for our custom Mock types.

    The `_get_child_mock` method automatically returns an AsyncMock for coroutine methods of the mock
    object. As discord.py also uses synchronous methods that nonetheless return coroutine objects, the
    class attribute `additional_spec_asyncs` can be overwritten with an iterable containing additional
    attribute names that should also mocked with an AsyncMock instead of a regular MagicMock/Mock. The
    class method `spec_set` can be overwritten with the object that should be uses as the specification
    for the mock.

    Mock/MagicMock subclasses that use this mixin only need to define `__init__` method if they need to
    implement custom behavior.
    """

    child_mock_type = unittest.mock.MagicMock
    discord_id = itertools.count(0)
    spec_set = None
    additional_spec_asyncs = None

    def __init__(self, **kwargs):
        name = kwargs.pop('name', None)  # `name` has special meaning for Mock classes, so we need to set it manually.
        super().__init__(spec_set=self.spec_set, **kwargs)

        if self.additional_spec_asyncs:
            self._spec_asyncs.extend(self.additional_spec_asyncs)

        if name:
            self.name = name

    def _get_child_mock(self, **kw):
        """
        Overwrite of the `_get_child_mock` method to stop the propagation of our custom mock classes.

        Mock objects automatically create children when you access an attribute or call a method on them. By default,
        the class of these children is the type of the parent itself. However, this would mean that the children created
        for our custom mock types would also be instances of that custom mock type. This is not desirable, as attributes
        of, e.g., a `Bot` object are not `Bot` objects themselves. The Python docs for `unittest.mock` hint that
        overwriting this method is the best way to deal with that.

        This override will look for an attribute called `child_mock_type` and use that as the type of the child mock.
        """
        _new_name = kw.get("_new_name")
        if _new_name in self.__dict__['_spec_asyncs']:
            return unittest.mock.AsyncMock(**kw)

        _type = type(self)
        if issubclass(_type, unittest.mock.MagicMock) and _new_name in unittest.mock._async_method_magics:
            # Any asynchronous magic becomes an AsyncMock
            klass = unittest.mock.AsyncMock
        else:
            klass = self.child_mock_type

        if self._mock_sealed:
            attribute = "." + kw["name"] if "name" in kw else "()"
            mock_name = self._extract_mock_name() + attribute
            raise AttributeError(mock_name)

        return klass(**kw)


# Create a guild instance to get a realistic Mock of `discord.Guild`
guild_data = {
    'id': 1,
    'name': 'guild',
    'region': 'Europe',
    'verification_level': 2,
    'default_notications': 1,
    'afk_timeout': 100,
    'icon': "icon.png",
    'banner': 'banner.png',
    'mfa_level': 1,
    'splash': 'splash.png',
    'system_channel_id': 464033278631084042,
    'description': 'mocking is fun',
    'max_presences': 10_000,
    'max_members': 100_000,
    'preferred_locale': 'UTC',
    'owner_id': 1,
    'afk_channel_id': 464033278631084042,
}
guild_instance = discord.Guild(data=guild_data, state=unittest.mock.MagicMock())


class MockGuild(CustomMockMixin, unittest.mock.Mock, HashableMixin):
    """
    A `Mock` subclass to mock `discord.Guild` objects.

    A MockGuild instance will follow the specifications of a `discord.Guild` instance. This means
    that if the code you're testing tries to access an attribute or method that normally does not
    exist for a `discord.Guild` object this will raise an `AttributeError`. This is to make sure our
    tests fail if the code we're testing uses a `discord.Guild` object in the wrong way.

    One restriction of that is that if the code tries to access an attribute that normally does not
    exist for `discord.Guild` instance but was added dynamically, this will raise an exception with
    the mocked object. To get around that, you can set the non-standard attribute explicitly for the
    instance of `MockGuild`:

    >>> guild = MockGuild()
    >>> guild.attribute_that_normally_does_not_exist = unittest.mock.MagicMock()

    In addition to attribute simulation, mocked guild object will pass an `isinstance` check against
    `discord.Guild`:

    >>> guild = MockGuild()
    >>> isinstance(guild, discord.Guild)
    True

    For more info, see the `Mocking` section in `tests/README.md`.
    """
    spec_set = guild_instance

    def __init__(self, roles: Optional[Iterable[MockRole]] = None, **kwargs) -> None:
        default_kwargs = {'id': next(self.discord_id), 'members': []}
        super().__init__(**collections.ChainMap(kwargs, default_kwargs))

        self.roles = [MockRole(name="@everyone", position=1, id=0)]
        if roles:
            self.roles.extend(roles)


# Create a Role instance to get a realistic Mock of `discord.Role`
role_data = {'name': 'role', 'id': 1}
role_instance = discord.Role(guild=guild_instance, state=unittest.mock.MagicMock(), data=role_data)


class MockRole(CustomMockMixin, unittest.mock.Mock, ColourMixin, HashableMixin):
    """
    A Mock subclass to mock `discord.Role` objects.

    Instances of this class will follow the specifications of `discord.Role` instances. For more
    information, see the `MockGuild` docstring.
    """
    spec_set = role_instance

    def __init__(self, **kwargs) -> None:
        default_kwargs = {
            'id': next(self.discord_id),
            'name': 'role',
            'position': 1,
            'colour': discord.Colour(0xdeadbf),
            'permissions': discord.Permissions(),
        }
        super().__init__(**collections.ChainMap(kwargs, default_kwargs))

        if isinstance(self.colour, int):
            self.colour = discord.Colour(self.colour)

        if isinstance(self.permissions, int):
            self.permissions = discord.Permissions(self.permissions)

        if 'mention' not in kwargs:
            self.mention = f'&{self.name}'

    def __lt__(self, other):
        """Simplified position-based comparisons similar to those of `discord.Role`."""
        return self.position < other.position

    def __ge__(self, other):
        """Simplified position-based comparisons similar to those of `discord.Role`."""
        return self.position >= other.position


# Create a Member instance to get a realistic Mock of `discord.Member`
member_data = {'user': 'lemon', 'roles': [1]}
state_mock = unittest.mock.MagicMock()
member_instance = discord.Member(data=member_data, guild=guild_instance, state=state_mock)


class MockMember(CustomMockMixin, unittest.mock.Mock, ColourMixin, HashableMixin):
    """
    A Mock subclass to mock Member objects.

    Instances of this class will follow the specifications of `discord.Member` instances. For more
    information, see the `MockGuild` docstring.
    """
    spec_set = member_instance

    def __init__(self, roles: Optional[Iterable[MockRole]] = None, **kwargs) -> None:
        default_kwargs = {
            'name': 'member',
            'id': next(self.discord_id),
            'bot': False,
            'discriminator': '1234',
        }
        super().__init__(**collections.ChainMap(kwargs, default_kwargs))

        self.roles = [MockRole(name="@everyone", position=1, id=0)]
        if roles:
            self.roles.extend(roles)

        if 'mention' not in kwargs:
            self.mention = f"@{self.name}"

        self.send = AsyncCheckRaiseResponse()


# Create a User instance to get a realistic Mock of `discord.User`
user_instance = discord.User(data=unittest.mock.MagicMock(), state=unittest.mock.MagicMock())


class MockUser(CustomMockMixin, unittest.mock.Mock, ColourMixin, HashableMixin):
    """
    A Mock subclass to mock User objects.

    Instances of this class will follow the specifications of `discord.User` instances. For more
    information, see the `MockGuild` docstring.
    """
    spec_set = user_instance

    def __init__(self, **kwargs) -> None:
        default_kwargs = {'name': 'user', 'id': next(self.discord_id), 'bot': False}
        super().__init__(**collections.ChainMap(kwargs, default_kwargs))

        if 'mention' not in kwargs:
            self.mention = f"@{self.name}"


# class MockAPIClient(CustomMockMixin, unittest.mock.MagicMock):
#     """
#     A MagicMock subclass to mock APIClient objects.

#     Instances of this class will follow the specifications of `bot.api.APIClient` instances.
#     For more information, see the `MockGuild` docstring.
#     """
#     spec_set = APIClient


def _get_mock_loop() -> unittest.mock.Mock:
    """Return a mocked asyncio.AbstractEventLoop."""
    loop = unittest.mock.create_autospec(spec=AbstractEventLoop, spec_set=True)

    # Since calling `create_task` on our MockBot does not actually schedule the coroutine object
    # as a task in the asyncio loop, this `side_effect` calls `close()` on the coroutine object
    # to prevent "has not been awaited"-warnings.
    loop.create_task.side_effect = lambda coroutine: coroutine.close()

    return loop


class MockBot(CustomMockMixin, unittest.mock.MagicMock):
    """
    A MagicMock subclass to mock Bot objects.

    Instances of this class will follow the specifications of `discord.ext.commands.Bot` instances.
    For more information, see the `MockGuild` docstring.
    """
    spec_set = Bot(
        command_prefix=unittest.mock.MagicMock(),
        loop=_get_mock_loop(),
        redis_session=unittest.mock.MagicMock(),
    )
    additional_spec_asyncs = ("wait_for", "redis_ready")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.loop = _get_mock_loop()
        # self.api_client = MockAPIClient(loop=self.loop)
        # self.http_session = unittest.mock.create_autospec(spec=ClientSession, spec_set=True)
        # self.stats = unittest.mock.create_autospec(spec=AsyncStatsClient, spec_set=True)


# Create a TextChannel instance to get a realistic MagicMock of `discord.TextChannel`
channel_data = {
    'id': 1,
    'type': 'TextChannel',
    'name': 'channel',
    'parent_id': 1234567890,
    'topic': 'topic',
    'position': 1,
    'nsfw': False,
    'last_message_id': 1,
}
state = unittest.mock.MagicMock()
guild = unittest.mock.MagicMock()
channel_instance = discord.TextChannel(state=state, guild=guild, data=channel_data)


class MockTextChannel(CustomMockMixin, unittest.mock.Mock, HashableMixin):
    """
    A MagicMock subclass to mock TextChannel objects.

    Instances of this class will follow the specifications of `discord.TextChannel` instances. For
    more information, see the `MockGuild` docstring.
    """
    spec_set = channel_instance

    def __init__(self, **kwargs) -> None:
        default_kwargs = {'id': next(self.discord_id), 'name': 'channel', 'guild': MockGuild()}
        super().__init__(**collections.ChainMap(kwargs, default_kwargs))

        if 'mention' not in kwargs:
            self.mention = f"#{self.name}"


# Create data for the DMChannel instance
state = unittest.mock.MagicMock()
me = unittest.mock.MagicMock()
dm_channel_data = {"id": 1, "recipients": [unittest.mock.MagicMock()]}
dm_channel_instance = discord.DMChannel(me=me, state=state, data=dm_channel_data)


class MockDMChannel(CustomMockMixin, unittest.mock.Mock, HashableMixin):
    """
    A MagicMock subclass to mock TextChannel objects.

    Instances of this class will follow the specifications of `discord.TextChannel` instances. For
    more information, see the `MockGuild` docstring.
    """
    spec_set = dm_channel_instance

    def __init__(self, **kwargs) -> None:
        default_kwargs = {'id': next(self.discord_id), 'recipient': MockUser(), "me": MockUser()}
        super().__init__(**collections.ChainMap(kwargs, default_kwargs))


# Create a Message instance to get a realistic MagicMock of `discord.Message`
message_data = {
    'id': 1,
    'webhook_id': 431341013479718912,
    'attachments': [],
    'embeds': [],
    'application': 'Python Discord',
    'activity': 'mocking',
    'channel': unittest.mock.MagicMock(),
    'edited_timestamp': '2019-10-14T15:33:48+00:00',
    'type': 'message',
    'pinned': False,
    'mention_everyone': False,
    'tts': None,
    'content': 'content',
    'nonce': None,
}
state = unittest.mock.MagicMock()
channel = unittest.mock.MagicMock()
message_instance = discord.Message(state=state, channel=channel, data=message_data)


# Create a Context instance to get a realistic MagicMock of `discord.ext.commands.Context`
context_instance = Context(message=unittest.mock.MagicMock(), prefix=unittest.mock.MagicMock())


class MockContext(CustomMockMixin, unittest.mock.AsyncMockMixin):
    """
    A MagicMock subclass to mock Context objects.

    Instances of this class will follow the specifications of `discord.ext.commands.Context`
    instances. For more information, see the `MockGuild` docstring.
    """
    spec_set = context_instance

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bot = kwargs.get('bot', MockBot())
        self.guild = kwargs.get('guild', MockGuild())
        self.author = kwargs.get('author', MockMember())
        self.channel = kwargs.get('channel', MockTextChannel())
        self.message = kwargs.get('message', MockMessage())
        self.reply = AsyncCheckRaiseResponse()
        self.send = AsyncCheckRaiseResponse()


attachment_instance = discord.Attachment(data=unittest.mock.MagicMock(id=1), state=unittest.mock.MagicMock())


class MockAttachment(CustomMockMixin, unittest.mock.MagicMock):
    """
    A MagicMock subclass to mock Attachment objects.

    Instances of this class will follow the specifications of `discord.Attachment` instances. For
    more information, see the `MockGuild` docstring.
    """
    spec_set = attachment_instance


class MockMessage(CustomMockMixin, unittest.mock.MagicMock):
    """
    A MagicMock subclass to mock Message objects.

    Instances of this class will follow the specifications of `discord.Message` instances. For more
    information, see the `MockGuild` docstring.
    """
    spec_set = message_instance

    def __init__(self, **kwargs) -> None:
        default_kwargs = {'attachments': []}
        super().__init__(**collections.ChainMap(kwargs, default_kwargs))
        self.author = kwargs.get('author', MockMember())
        self.channel = kwargs.get('channel', MockTextChannel())
        self.reply = AsyncCheckRaiseResponse()


emoji_data = {'require_colons': True, 'managed': True, 'id': 1, 'name': 'hyperlemon'}
emoji_instance = discord.Emoji(guild=MockGuild(), state=unittest.mock.MagicMock(), data=emoji_data)


class MockEmoji(CustomMockMixin, unittest.mock.MagicMock):
    """
    A MagicMock subclass to mock Emoji objects.

    Instances of this class will follow the specifications of `discord.Emoji` instances. For more
    information, see the `MockGuild` docstring.
    """
    spec_set = emoji_instance

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.guild = kwargs.get('guild', MockGuild())


partial_emoji_instance = discord.PartialEmoji(animated=False, name='guido')


class MockPartialEmoji(CustomMockMixin, unittest.mock.MagicMock):
    """
    A MagicMock subclass to mock PartialEmoji objects.

    Instances of this class will follow the specifications of `discord.PartialEmoji` instances. For
    more information, see the `MockGuild` docstring.
    """
    spec_set = partial_emoji_instance


reaction_instance = discord.Reaction(message=MockMessage(), data={'me': True}, emoji=MockEmoji())


class MockReaction(CustomMockMixin, unittest.mock.MagicMock):
    """
    A MagicMock subclass to mock Reaction objects.

    Instances of this class will follow the specifications of `discord.Reaction` instances. For
    more information, see the `MockGuild` docstring.
    """
    spec_set = reaction_instance

    def __init__(self, **kwargs) -> None:
        _users = kwargs.pop("users", [])
        super().__init__(**kwargs)
        self.emoji = kwargs.get('emoji', MockEmoji())
        self.message = kwargs.get('message', MockMessage())

        user_iterator = unittest.mock.AsyncMock()
        user_iterator.__aiter__.return_value = _users
        self.users.return_value = user_iterator

        self.__str__.return_value = str(self.emoji)


webhook_instance = discord.Webhook(data=unittest.mock.MagicMock(), adapter=unittest.mock.MagicMock())


class MockAsyncWebhook(CustomMockMixin, unittest.mock.MagicMock):
    """
    A MagicMock subclass to mock Webhook objects using an AsyncWebhookAdapter.

    Instances of this class will follow the specifications of `discord.Webhook` instances. For
    more information, see the `MockGuild` docstring.
    """
    spec_set = webhook_instance
    additional_spec_asyncs = ("send", "edit", "delete", "execute")
