from finance_bot.config import load_settings


def test_load_settings_reads_openrouter_key_from_file(tmp_path, monkeypatch) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "categories.yml").write_text("categories:\n  - otros\n", encoding="utf-8")
    (config_dir / "rules.yml").write_text("rules: {}\n", encoding="utf-8")

    credentials_dir = tmp_path / "credentials"
    credentials_dir.mkdir(parents=True)
    (credentials_dir / "google-service-account.json").write_text("{}", encoding="utf-8")

    secret_file = tmp_path / "secrets" / "openrouter_key.txt"
    secret_file.parent.mkdir(parents=True)
    secret_file.write_text("sk-or-test\n", encoding="utf-8")

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123")
    monkeypatch.setenv("GOOGLE_SHEETS_ID", "sheet-id")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/google-service-account.json")
    monkeypatch.setenv("OPENROUTER_API_KEY_FILE", "secrets/openrouter_key.txt")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    settings = load_settings(base_path=tmp_path)

    assert settings.openrouter_api_key == "sk-or-test"


def test_load_settings_prefers_direct_openrouter_key_over_file(tmp_path, monkeypatch) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "categories.yml").write_text("categories:\n  - otros\n", encoding="utf-8")
    (config_dir / "rules.yml").write_text("rules: {}\n", encoding="utf-8")

    credentials_dir = tmp_path / "credentials"
    credentials_dir.mkdir(parents=True)
    (credentials_dir / "google-service-account.json").write_text("{}", encoding="utf-8")

    secret_file = tmp_path / "secrets" / "openrouter_key.txt"
    secret_file.parent.mkdir(parents=True)
    secret_file.write_text("sk-or-file\n", encoding="utf-8")

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123")
    monkeypatch.setenv("GOOGLE_SHEETS_ID", "sheet-id")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/google-service-account.json")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-direct")
    monkeypatch.setenv("OPENROUTER_API_KEY_FILE", "secrets/openrouter_key.txt")

    settings = load_settings(base_path=tmp_path)

    assert settings.openrouter_api_key == "sk-or-direct"


def test_load_settings_without_openrouter_key_is_allowed(tmp_path, monkeypatch) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "categories.yml").write_text("categories:\n  - otros\n", encoding="utf-8")
    (config_dir / "rules.yml").write_text("rules: {}\n", encoding="utf-8")

    credentials_dir = tmp_path / "credentials"
    credentials_dir.mkdir(parents=True)
    (credentials_dir / "google-service-account.json").write_text("{}", encoding="utf-8")

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123")
    monkeypatch.setenv("GOOGLE_SHEETS_ID", "sheet-id")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/google-service-account.json")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY_FILE", raising=False)

    settings = load_settings(base_path=tmp_path)

    assert settings.openrouter_api_key is None
