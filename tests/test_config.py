from pombot.config import Config, Secrets


def test_loading_config_gives_no_errors():
    """Test Config attributes that are specified in the .env file."""
    assert Config.ERRORS_CHANNEL_NAME is not None
    assert Config.POM_CHANNEL_NAMES is not None


def test_all_secrets_exist_in_env():
    """Test Secrets attributes that must be specified in the .env file."""
    for attr in vars(Secrets):
        name, *_ = attr.split("__")

        if not name:
            continue

        assert hasattr(Secrets, name), f"{name} must be specified in .env"
        assert getattr(Secrets, name), f"{name} must not be blank in .env"


# NOTE: Debug attributes are tested defensively insteand of in a unit test
# because the __debug__ symbol will change with optimization levels. The test
# will always pass and some options might still be set (eg. clearing all MySQL
# tables).
