import logging
from pathlib import Path

THIS_DIR = Path(__file__).parent
POM_WARS_DATA_DIR = THIS_DIR / "pom_wars"

_log = logging.getLogger(__name__)


class Limits:
    """Character limits imposed by the Discord API."""
    MAX_CHARACTERS_PER_MESSAGE = 2000
    MAX_CHARACTERS_PER_EMBED = 6000

    MAX_EMBED_TITLE       = 256
    MAX_EMBED_DESCRIPTION = 2048
    MAX_NUM_EMBED_FIELDS  = 25
    MAX_EMBED_FIELD_NAME  = 256
    MAX_EMBED_FIELD_VALUE = 1024
    MAX_EMBED_FOOTER_TEXT = 2048
    MAX_EMBED_AUTHOR_NAME = 256


class Locations:
    """Path-like locations of data for the bot."""
    DISCLAIMERS = THIS_DIR / "disclaimers.xml"
    SCOREBOARD_BODY = POM_WARS_DATA_DIR / "scoreboard.txt"

    MESSAGE = "message.txt"
    META = "meta.json"

    NORMAL_ATTACKS_DIR = POM_WARS_DATA_DIR / "normal_attacks"
    HEAVY_ATTACKS_DIR = POM_WARS_DATA_DIR / "heavy_attacks"
    DEFENDS_DIR = POM_WARS_DATA_DIR / "defends"
    BRIBES_DIR = POM_WARS_DATA_DIR / "bribes"


# Check sanity to discover errors in folder structure during developement.
def _check_is_actions_dir(path: Path) -> True:
    log_name = (path.name if not path.name.startswith("~")
            else "/".join(path.parts[-2:]))
    _log.info("Loading actions directory: %s", log_name)

    for item in path.iterdir():
        if not item.is_dir():
            continue

        if item.name.startswith("~"):
            _check_is_actions_dir(item)
            continue

        attack_dir = item
        expected_items = {Locations.MESSAGE, Locations.META}
        actual_items = {item.name for item in attack_dir.iterdir()}

        # NOTE: Other items in the directory are allowed to exist.
        if missing_items := expected_items - actual_items:
            raise RuntimeError(
                f"Missing {', '.join(missing_items)} in {item}")


for attr in vars(Locations):
    name, *_ = attr.split("__")

    if (not name or not hasattr(Locations, name)
            or not name.casefold().endswith("dir")):
        continue

    location: Path = getattr(Locations, name).resolve()

    if not location.is_dir():
        raise RuntimeError(f"Variable named '{location}' is not a directory")

    _check_is_actions_dir(location)
