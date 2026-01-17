from __future__ import annotations

import random
import time
from urllib.parse import urlparse

import httpx

from scraparse.core.errors import FetchError
from scraparse.core.limits import Limits, LimitTracker
from scraparse.core.models import FetchResult

ALLOWED_CONTENT_TYPES = {"text/html", "application/xhtml+xml"}


class HttpxFetcher:
    def __init__(self, limits: Limits, transport: httpx.BaseTransport | None = None) -> None:
        self.limits = limits
        self.client = httpx.Client(
            timeout=httpx.Timeout(
                timeout=limits.timeout_total_s,
                connect=limits.timeout_connect_s,
                read=limits.timeout_read_s,
            ),
            follow_redirects=True,
            transport=transport,
        )
        self._last_request_time: dict[str, float] = {}

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "HttpxFetcher":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.close()

    def _rate_limit(self, url: str) -> None:
        host = urlparse(url).netloc
        if not host or self.limits.rate_limit_rps <= 0:
            return
        min_interval = 1.0 / self.limits.rate_limit_rps
        last_time = self._last_request_time.get(host)
        if last_time is None:
            return
        elapsed = time.time() - last_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    def fetch(self, url: str, tracker: LimitTracker) -> FetchResult:
        last_error: Exception | None = None
        for attempt in range(self.limits.retries + 1):
            tracker.check_runtime()
            tracker.start_page()
            self._rate_limit(url)
            try:
                with self.client.stream("GET", url) as response:
                    status = response.status_code
                    if status >= 400:
                        raise FetchError(f"HTTP {status} for {url}")
                    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
                    if content_type not in ALLOWED_CONTENT_TYPES:
                        raise FetchError(f"Disallowed content-type: {content_type or 'missing'}")
                    chunks: list[bytes] = []
                    for chunk in response.iter_bytes():
                        if not chunk:
                            continue
                        tracker.add_bytes(len(chunk))
                        chunks.append(chunk)
                    tracker.finish_page()
                    self._last_request_time[urlparse(url).netloc] = time.time()
                    content_bytes = b"".join(chunks)
                    encoding = response.encoding or "utf-8"
                    content_text = content_bytes.decode(encoding, errors="replace")
                    return FetchResult(
                        url=url,
                        content_bytes=content_bytes,
                        content_text=content_text,
                        status_code=status,
                        content_type=content_type,
                    )
            except FetchError as exc:
                last_error = exc
                tracker.record_failure()
            except httpx.RequestError as exc:
                last_error = exc
                tracker.record_failure()
            if attempt < self.limits.retries:
                backoff = min(self.limits.backoff_base_s * (2**attempt), self.limits.backoff_max_s)
                jitter = random.random() * self.limits.jitter_s
                time.sleep(backoff + jitter)
        raise FetchError(f"Failed to fetch {url}: {last_error}")
