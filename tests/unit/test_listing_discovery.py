from scraparse.core.limits import LimitTracker, Limits
from scraparse.core.models import FetchResult
from scraparse.plugins.discovery.listing import ListingDiscovery
from scraparse.plugins.fetchers.base import Fetcher


class FakeFetcher(Fetcher):
    def __init__(self) -> None:
        self.calls: list[str] = []

    def fetch(self, url: str, tracker: LimitTracker) -> FetchResult:  # type: ignore[override]
        tracker.start_page()
        tracker.add_bytes(10)
        tracker.finish_page()
        self.calls.append(url)
        if url.endswith("/list"):
            html = (
                "<html><body>"
                "<a href='/list/product/1'>Item 1</a>"
                "<a href='/list/product/2'>Item 2</a>"
                "<a href='/other'>Other</a>"
                "</body></html>"
            )
        else:
            html = "<html></html>"
        return FetchResult(
            url=url,
            content_bytes=html.encode("utf-8"),
            content_text=html,
            status_code=200,
            content_type="text/html",
        )


def test_listing_discovery_fetches_detail_links() -> None:
    limits = Limits(max_pages=3)
    tracker = LimitTracker(limits)
    fetcher = FakeFetcher()
    discovery = ListingDiscovery()
    results = discovery.discover(
        start_url="https://example.com/list",
        fetcher=fetcher,
        tracker=tracker,
        limits=limits,
    )
    assert len(results) == 3
    assert fetcher.calls[0].endswith("/list")
    assert fetcher.calls[1].endswith("/list/product/1")
    assert fetcher.calls[2].endswith("/list/product/2")
