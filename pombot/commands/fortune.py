import random
from contextlib import contextmanager
from datetime import datetime
from typing import List, Tuple
from xml.etree import ElementTree

from discord.ext.commands import Context

from pombot.config import Config
from pombot.data import Locations
from pombot.lib.messages import send_embed_message


async def do_fortune(ctx: Context) -> str:
    """Show your fortune!"""
    date = datetime.strftime(datetime.today(), "%Y%m%d")

    with _pause_rng("".join((date, ctx.author.discriminator))):
        lucky_numbers = [random.randint(0, 101) for _ in range(5)]

    await send_embed_message(
        ctx,
        title="Fortune",
        icon_url=Config.WIZARD_ICON_URL,
        description=f"Full disclosure: {_Disclaimer()}",
        footer="Your lucky numbers for today are {}".format(", ".join(
            str(n) for n in lucky_numbers)),
    )


@contextmanager
def _pause_rng(seed: object):
    """Save and restore the current state of the PRNG."""
    state = random.getstate()
    random.seed(seed)

    try:
        yield
    finally:
        random.setstate(state)


class _Disclaimer:
    """Random disclaimer getter."""
    _disclaimers: List[Tuple[str, float]] = []

    def __new__(cls) -> str:
        """Return a random disclaimer from the memoized list."""
        if not cls._disclaimers:
            root = ElementTree.parse(Locations.DISCLAIMERS).getroot()
            cls._disclaimers = [(elem.text, float(elem.attrib["probability"]))
                                for elem in root.findall(".//fortune")]

        disclaimer, = random.choices(*zip(*cls._disclaimers))
        return disclaimer
