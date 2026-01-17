import httpx
import pytest

from scraparse.core.errors import LimitExceededError
from scraparse.core.limits import LimitTracker, Limits
from scraparse.plugins.fetchers.httpx_fetcher import HttpxFetcher


def test_fetcher_returns_html() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"<html></html>",
        )

    transport = httpx.MockTransport(handler)
    limits = Limits()
    fetcher = HttpxFetcher(limits, transport=transport)
    tracker = LimitTracker(limits)
    result = fetcher.fetch("https://example.com", tracker)
    assert "<html" in result.content_text
    fetcher.close()


def test_fetcher_respects_max_response_bytes() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"abcdef",
        )

    transport = httpx.MockTransport(handler)
    limits = Limits(max_response_bytes=3)
    fetcher = HttpxFetcher(limits, transport=transport)
    tracker = LimitTracker(limits)
    with pytest.raises(LimitExceededError):
        fetcher.fetch("https://example.com", tracker)
    fetcher.close()
