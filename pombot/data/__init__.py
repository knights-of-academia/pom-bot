from pathlib import Path
import logging

THIS_DIR = Path(__file__).parent
POM_WARS_DATA_DIR = THIS_DIR / "pom_wars"

_log = logging.getLogger(__name__)
_log.info("Collecting initial commands data")


class Locations:
    WEAK_ATTACKS_DIR = POM_WARS_DATA_DIR / "weak_attacks"
    NORMAL_ATTACKS_DIR = POM_WARS_DATA_DIR / "normal_attacks"
    STRONG_ATTACKS_DIR = POM_WARS_DATA_DIR / "strong_attacks"
    SPECIAL_ATTACKS_DIR = POM_WARS_DATA_DIR / "special_attacks"

# Check sanity to discover errors in folder structure during developement.
for attr in vars(Locations):
    name, *_ = attr.split("__")

    if name and hasattr(Locations, name):
        location = getattr(Locations, name)
        assert location.exists()

        if name.endswith("DIR"):
            assert location.is_dir()

        if location.name.endswith("attacks"):
            for item in location.iterdir():
                if not item.is_dir():
                    continue

                attack_dir = item
                expected_items = {"message.txt", "meta.json"}
                actual_items = {item.name for item in attack_dir.iterdir()}

                # NOTE: Other items are allowed to exist.
                missing_items = expected_items - actual_items

                if missing_items:
                    items = ", ".join(missing_items)
                    raise RuntimeError(f"Missing {items} in {item}")
