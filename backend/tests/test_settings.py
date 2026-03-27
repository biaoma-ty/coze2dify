from config import Settings


def test_settings_debug_defaults_to_false(monkeypatch) -> None:
    monkeypatch.delenv("COZE2DIFY_DEBUG", raising=False)

    settings = Settings(_env_file=None)

    assert settings.debug is False


def test_settings_debug_can_be_enabled_with_env_var(monkeypatch) -> None:
    monkeypatch.setenv("COZE2DIFY_DEBUG", "true")

    settings = Settings(_env_file=None)

    assert settings.debug is True
