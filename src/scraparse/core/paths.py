from __future__ import annotations

from importlib import resources
from pathlib import Path


def templates_dir() -> Path:
    return Path(resources.files("scraparse") / "templates")
