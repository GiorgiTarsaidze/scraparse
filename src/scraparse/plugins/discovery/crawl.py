from __future__ import annotations

from collections import deque
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup

from scraparse.core.errors import LimitExceededError
from scraparse.core.limits import Limits, LimitTracker
from scraparse.core.models import FetchResult
from scraparse.plugins.fetchers.base import Fetcher


class CrawlDiscovery:
    def discover(
        self,
        start_url: str,
        fetcher: Fetcher,
        tracker: LimitTracker,
        limits: Limits,
        next_selector: str | None = None,
        detail_selector: str | None = None,
    ) -> list[FetchResult]:
        start_netloc = urlparse(start_url).netloc
        queue: deque[tuple[str, int]] = deque([(start_url, 0)])
        visited: set[str] = set()
        results: list[FetchResult] = []

        while queue:
            url, depth = queue.popleft()
            normalized = self._normalize_url(url)
            if normalized in visited:
                continue
            if depth > limits.max_depth:
                continue
            if len(results) >= limits.max_pages:
                raise LimitExceededError(
                    "max_pages",
                    "Max pages exceeded",
                    {"pages_fetched": len(results)},
                    limits.max_pages,
                )
            visited.add(normalized)
            tracker.check_runtime()
            result = fetcher.fetch(normalized, tracker)
            results.append(result)
            soup = BeautifulSoup(result.content_text, "html.parser")
            for link in soup.find_all("a", href=True):
                href = str(link["href"]).strip()
                if not href:
                    continue
                next_url = self._normalize_url(urljoin(normalized, href))
                if not next_url:
                    continue
                if limits.same_domain_only and urlparse(next_url).netloc != start_netloc:
                    continue
                if next_url in visited:
                    continue
                queue.append((next_url, depth + 1))
        return results

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not url:
            return ""
        cleaned, _ = urldefrag(url.strip())
        return cleaned
