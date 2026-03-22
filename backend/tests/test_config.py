from config import Settings


def test_settings_debug_is_disabled_by_default() -> None:
    assert Settings().debug is False
