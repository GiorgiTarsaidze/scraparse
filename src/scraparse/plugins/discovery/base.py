from __future__ import annotations

from typing import Protocol

from scraparse.core.limits import Limits, LimitTracker
from scraparse.core.models import FetchResult
from scraparse.plugins.fetchers.base import Fetcher


class DiscoveryPlugin(Protocol):
    def discover(
        self,
        start_url: str,
        fetcher: Fetcher,
        tracker: LimitTracker,
        limits: Limits,
        next_selector: str | None = None,
        detail_selector: str | None = None,
    ) -> list[FetchResult]:
        ...
