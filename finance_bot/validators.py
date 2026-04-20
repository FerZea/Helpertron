from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def is_allowed_chat(chat_id: int, allowed_chat_id: int) -> bool:
    return chat_id == allowed_chat_id


def normalize_keyword(keyword: str) -> str:
    return keyword.strip().lower()


def normalize_category(category: str) -> str:
    return category.strip().lower()


def build_timestamps(message_date: int, timezone_name: str) -> tuple[datetime, datetime]:
    utc_dt = datetime.fromtimestamp(message_date, tz=timezone.utc)
    local_dt = utc_dt.astimezone(ZoneInfo(timezone_name))
    return utc_dt, local_dt
