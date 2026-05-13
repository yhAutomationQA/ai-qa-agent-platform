from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def format_dt(dt: datetime | None, fmt: str = "%Y-%m-%dT%H:%M:%SZ") -> str | None:
    if dt is None:
        return None
    return dt.strftime(fmt)


def parse_dt(value: str, fmt: str = "%Y-%m-%dT%H:%M:%SZ") -> datetime | None:
    try:
        return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None
