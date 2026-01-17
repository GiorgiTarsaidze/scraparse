from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urlparse


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify_domain(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc or "unknown"
    host = host.replace(":", "_")
    return re.sub(r"[^a-zA-Z0-9._-]", "_", host)


def snake_case(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_").lower() or "field"


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")
