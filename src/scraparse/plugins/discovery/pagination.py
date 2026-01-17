from __future__ import annotations

from urllib.parse import urljoin, urldefrag, urlparse

from bs4 import BeautifulSoup

from scraparse.core.errors import LimitExceededError
from scraparse.core.limits import Limits, LimitTracker
from scraparse.core.models import FetchResult
from scraparse.plugins.fetchers.base import Fetcher


class PaginationDiscovery:
    def discover(
        self,
        start_url: str,
        fetcher: Fetcher,
        tracker: LimitTracker,
        limits: Limits,
        next_selector: str | None = None,
        detail_selector: str | None = None,
    ) -> list[FetchResult]:
        results: list[FetchResult] = []
        visited: set[str] = set()
        start_netloc = urlparse(start_url).netloc
        current_url = start_url

        while current_url:
            normalized = self._normalize_url(current_url)
            if normalized in visited:
                break
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
            next_url = self._find_next_url(soup, normalized, next_selector)
            if next_url and limits.same_domain_only:
                next_netloc = urlparse(next_url).netloc
                if next_netloc != start_netloc:
                    next_url = None
            current_url = next_url
        return results

    def _find_next_url(self, soup: BeautifulSoup, base_url: str, selector: str | None) -> str | None:
        if selector:
            node = soup.select_one(selector)
            if node and node.get("href"):
                return self._normalize_url(urljoin(base_url, str(node.get("href"))))
        link_tag = soup.find("link", rel=lambda value: value and "next" in value)
        if link_tag and link_tag.get("href"):
            return self._normalize_url(urljoin(base_url, str(link_tag.get("href"))))
        for anchor in soup.find_all("a", href=True):
            text = anchor.get_text(strip=True).lower()
            if text in {"next", "next page", "older", "more"}:
                return self._normalize_url(urljoin(base_url, str(anchor.get("href"))))
        return None

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not url:
            return ""
        cleaned, _ = urldefrag(url.strip())
        return cleaned
