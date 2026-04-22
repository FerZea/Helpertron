from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml


@dataclass(slots=True)
class Settings:
    telegram_bot_token: str
    allowed_chat_id: int
    google_sheets_id: str
    google_service_account_file: Path
    timezone: str
    default_currency: str
    sheets_worksheet: str
    sheets_dashboard_worksheet: str
    openrouter_api_key: str | None
    openrouter_model: str
    openrouter_timeout_seconds: float
    openrouter_base_url: str
    openrouter_site_url: str | None
    openrouter_app_name: str
    categories_file: Path
    rules_file: Path


def load_settings(base_path: Path | None = None) -> Settings:
    root = base_path or Path.cwd()
    config_dir = root / "config"

    telegram_bot_token = _required_env("TELEGRAM_BOT_TOKEN")
    allowed_chat_id = int(_required_env("ALLOWED_CHAT_ID"))
    google_sheets_id = _required_env("GOOGLE_SHEETS_ID")
    service_account_path = Path(_required_env("GOOGLE_SERVICE_ACCOUNT_FILE"))

    if not service_account_path.is_absolute():
        service_account_path = root / service_account_path

    timezone_name = os.getenv("TIMEZONE", "UTC")
    _validate_timezone(timezone_name)

    default_currency = os.getenv("DEFAULT_CURRENCY", "MXN").strip().upper()
    sheets_worksheet = os.getenv("SHEETS_WORKSHEET", "expenses").strip() or "expenses"
    sheets_dashboard_worksheet = os.getenv("SHEETS_DASHBOARD_WORKSHEET", "dashboard").strip() or "dashboard"

    openrouter_api_key = _load_optional_secret(
        root,
        secret_env_key="OPENROUTER_API_KEY",
        file_env_key="OPENROUTER_API_KEY_FILE",
    )
    openrouter_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip() or "openai/gpt-4o-mini"
    openrouter_timeout_seconds = float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "15"))
    if openrouter_timeout_seconds <= 0:
        raise ValueError("OPENROUTER_TIMEOUT_SECONDS debe ser mayor a 0")
    openrouter_base_url = (
        os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions").strip()
        or "https://openrouter.ai/api/v1/chat/completions"
    )
    openrouter_site_url = os.getenv("OPENROUTER_SITE_URL", "").strip() or None
    openrouter_app_name = os.getenv("OPENROUTER_APP_NAME", "financebot").strip() or "financebot"

    return Settings(
        telegram_bot_token=telegram_bot_token,
        allowed_chat_id=allowed_chat_id,
        google_sheets_id=google_sheets_id,
        google_service_account_file=service_account_path,
        timezone=timezone_name,
        default_currency=default_currency,
        sheets_worksheet=sheets_worksheet,
        sheets_dashboard_worksheet=sheets_dashboard_worksheet,
        openrouter_api_key=openrouter_api_key,
        openrouter_model=openrouter_model,
        openrouter_timeout_seconds=openrouter_timeout_seconds,
        openrouter_base_url=openrouter_base_url,
        openrouter_site_url=openrouter_site_url,
        openrouter_app_name=openrouter_app_name,
        categories_file=config_dir / "categories.yml",
        rules_file=config_dir / "rules.yml",
    )


def load_categories(path: Path) -> list[str]:
    data = _read_yaml(path)
    categories = data.get("categories", [])
    if not isinstance(categories, list):
        raise ValueError(f"Formato invalido de categorias en {path}")

    normalized = [str(item).strip().lower() for item in categories if str(item).strip()]
    if "otros" not in normalized:
        normalized.append("otros")
    return sorted(set(normalized))


def load_rules(path: Path) -> dict[str, str]:
    data = _read_yaml(path)
    rules = data.get("rules", {})
    if not isinstance(rules, dict):
        raise ValueError(f"Formato invalido de reglas en {path}")

    normalized: dict[str, str] = {}
    for keyword, category in rules.items():
        keyword_normalized = str(keyword).strip().lower()
        category_normalized = str(category).strip().lower()
        if not keyword_normalized or not category_normalized:
            continue
        normalized[keyword_normalized] = category_normalized
    return normalized


def save_rules(path: Path, rules: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered_rules = dict(sorted(rules.items(), key=lambda item: item[0]))
    payload = {"rules": ordered_rules}
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")


def _required_env(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        raise ValueError(f"No se encontro la variable obligatoria: {key}")
    return value


def _load_optional_secret(root: Path, secret_env_key: str, file_env_key: str) -> str | None:
    secret_value = os.getenv(secret_env_key, "").strip()
    if secret_value:
        return secret_value

    secret_file = os.getenv(file_env_key, "").strip()
    if not secret_file:
        return None

    secret_path = Path(secret_file)
    if not secret_path.is_absolute():
        secret_path = root / secret_path

    if not secret_path.exists():
        raise ValueError(f"No existe el archivo de secreto: {secret_path}")

    file_secret = secret_path.read_text(encoding="utf-8").strip()
    if not file_secret:
        raise ValueError(f"El archivo de secreto esta vacio: {secret_path}")

    return file_secret


def _validate_timezone(timezone_name: str) -> None:
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as error:
        raise ValueError(f"Zona horaria invalida: {timezone_name}") from error


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Contenido invalido en {path}")
    return data
