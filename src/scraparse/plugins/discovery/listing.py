from __future__ import annotations

from urllib.parse import urljoin, urldefrag, urlparse

from bs4 import BeautifulSoup

from scraparse.core.errors import LimitExceededError
from scraparse.core.limits import Limits, LimitTracker
from scraparse.core.models import FetchResult
from scraparse.plugins.fetchers.base import Fetcher


class ListingDiscovery:
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

        if len(results) >= limits.max_pages:
            raise LimitExceededError(
                "max_pages",
                "Max pages exceeded",
                {"pages_fetched": len(results)},
                limits.max_pages,
            )
        start_normalized = self._normalize_url(start_url)
        result = fetcher.fetch(start_normalized, tracker)
        results.append(result)
        visited.add(start_normalized)

        soup = BeautifulSoup(result.content_text, "html.parser")
        links = self._collect_detail_links(soup, start_normalized, limits, detail_selector)
        for link in links:
            normalized = self._normalize_url(link)
            if not normalized or normalized in visited:
                continue
            if len(results) >= limits.max_pages:
                raise LimitExceededError(
                    "max_pages",
                    "Max pages exceeded",
                    {"pages_fetched": len(results)},
                    limits.max_pages,
                )
            fetched = fetcher.fetch(normalized, tracker)
            results.append(fetched)
            visited.add(normalized)
        return results

    def _collect_detail_links(
        self,
        soup: BeautifulSoup,
        base_url: str,
        limits: Limits,
        detail_selector: str | None,
    ) -> list[str]:
        links: list[str] = []
        seen: set[str] = set()
        base_parts = urlparse(base_url)
        base_path = base_parts.path.rstrip("/")

        if detail_selector:
            nodes = soup.select(detail_selector)
            for node in nodes:
                href = node.get("href") if hasattr(node, "get") else None
                if not href and hasattr(node, "find"):
                    anchor = node.find("a", href=True)
                    href = anchor.get("href") if anchor else None
                if not href:
                    continue
                resolved = self._normalize_url(urljoin(base_url, str(href)))
                if self._allow_link(resolved, base_parts.netloc, base_path, limits):
                    if resolved not in seen:
                        seen.add(resolved)
                        links.append(resolved)
            return links

        for anchor in soup.find_all("a", href=True):
            text = anchor.get_text(strip=True).lower()
            if text in {"next", "prev", "previous", "older", "newer", "more"}:
                continue
            href = str(anchor.get("href"))
            if href.startswith("#") or href.lower().startswith("javascript:"):
                continue
            resolved = self._normalize_url(urljoin(base_url, href))
            if self._allow_link(resolved, base_parts.netloc, base_path, limits):
                if resolved not in seen:
                    seen.add(resolved)
                    links.append(resolved)
        return links

    def _allow_link(self, url: str, base_netloc: str, base_path: str, limits: Limits) -> bool:
        if not url:
            return False
        parts = urlparse(url)
        if limits.same_domain_only and parts.netloc != base_netloc:
            return False
        if base_path:
            if parts.path.rstrip("/") == base_path:
                return False
            if not parts.path.startswith(base_path + "/"):
                return False
        return True

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not url:
            return ""
        cleaned, _ = urldefrag(url.strip())
        return cleaned
