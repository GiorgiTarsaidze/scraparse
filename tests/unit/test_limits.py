import pytest

from scraparse.core.errors import LimitExceededError
from scraparse.core.limits import LimitTracker, Limits


def test_max_response_bytes_exceeded() -> None:
    limits = Limits(max_response_bytes=5, max_total_bytes=100)
    tracker = LimitTracker(limits)
    tracker.start_page()
    with pytest.raises(LimitExceededError):
        tracker.add_bytes(6)


def test_max_total_bytes_exceeded() -> None:
    limits = Limits(max_response_bytes=100, max_total_bytes=5)
    tracker = LimitTracker(limits)
    tracker.start_page()
    with pytest.raises(LimitExceededError):
        tracker.add_bytes(6)


def test_max_pages_exceeded() -> None:
    limits = Limits(max_pages=1)
    tracker = LimitTracker(limits)
    tracker.start_page()
    tracker.finish_page()
    with pytest.raises(LimitExceededError):
        tracker.start_page()
