import random
from contextlib import contextmanager
from datetime import datetime
from typing import List, Tuple
from xml.etree import ElementTree

from discord.ext.commands import Context

from pombot.config import IconUrls
from pombot.data import Locations
from pombot.lib.messages import send_embed_message


async def do_fortune(ctx: Context) -> str:
    """Show your fortune!"""
    date = datetime.strftime(datetime.today(), "%Y%m%d")

    with _pause_rng("".join((date, ctx.author.discriminator))):
        lucky_numbers = [random.randint(0, 101) for _ in range(5)]

    disclaimer = _Disclaimer()

    await send_embed_message(
        ctx,
        title="Fortune",
        thumbnail=IconUrls.WIZARD,
        description=f"{disclaimer.type}: {disclaimer.content}",
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
    POSSIBLE_TYPES = (
        "Information",
        "WARNING",
        "Full Disclosure",
        "Disclaimer",
        "NOTICE",
        "Terms and Conditions",
        "ACHTUNG",
        "AVISO",
    )

    _disclaimers: List[Tuple[str, float]] = []

    def __init__(self) -> str:
        """Return a random disclaimer from the memoized list."""
        if not self._disclaimers:
            root = ElementTree.parse(Locations.DISCLAIMERS).getroot()
            self._disclaimers = [(elem.text, float(elem.attrib["probability"]))
                                for elem in root.findall(".//fortune")]

        self.content, = random.choices(*zip(*self._disclaimers))
        self.type = random.choice(self.POSSIBLE_TYPES)
