from __future__ import annotations

from typing import Protocol

from scraparse.core.limits import LimitTracker
from scraparse.core.models import FetchResult


class Fetcher(Protocol):
    def fetch(self, url: str, tracker: LimitTracker) -> FetchResult:
        ...
