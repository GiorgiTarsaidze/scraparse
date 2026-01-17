from __future__ import annotations

from dataclasses import dataclass, field
import time

from scraparse.core.errors import LimitExceededError


@dataclass(frozen=True)
class Limits:
    # Discovery
    max_pages: int = 25
    max_depth: int = 2
    max_consecutive_failures: int = 5
    same_domain_only: bool = True

    # Fetching
    timeout_connect_s: float = 5
    timeout_read_s: float = 15
    timeout_total_s: float = 30
    retries: int = 2
    backoff_base_s: float = 0.5
    backoff_max_s: float = 5.0
    jitter_s: float = 0.25
    rate_limit_rps: float = 1.0

    # Size + runtime
    max_response_bytes: int = 2_000_000
    max_total_bytes: int = 15_000_000
    max_runtime_s: int = 180

    # LLM payload limits
    max_html_chars_for_llm: int = 120_000

    def with_overrides(self, overrides: dict[str, object]) -> "Limits":
        values = {**self.__dict__}
        for key, value in overrides.items():
            if value is None:
                continue
            if key not in values:
                continue
            values[key] = value
        return Limits(**values)

    def to_dict(self) -> dict[str, object]:
        return dict(self.__dict__)


@dataclass
class LimitTracker:
    limits: Limits
    start_time_s: float = field(default_factory=time.time)
    pages_fetched: int = 0
    total_bytes: int = 0
    consecutive_failures: int = 0
    current_page_bytes: int = 0

    def check_runtime(self) -> None:
        elapsed = time.time() - self.start_time_s
        if elapsed > self.limits.max_runtime_s:
            raise LimitExceededError(
                "max_runtime_s",
                "Max runtime exceeded",
                {"elapsed_s": round(elapsed, 2)},
                self.limits.max_runtime_s,
            )

    def start_page(self) -> None:
        if self.pages_fetched >= self.limits.max_pages:
            raise LimitExceededError(
                "max_pages",
                "Max pages exceeded",
                {"pages_fetched": self.pages_fetched},
                self.limits.max_pages,
            )
        self.current_page_bytes = 0

    def add_bytes(self, count: int) -> None:
        self.current_page_bytes += count
        self.total_bytes += count
        if self.current_page_bytes > self.limits.max_response_bytes:
            raise LimitExceededError(
                "max_response_bytes",
                "Max response bytes exceeded",
                {"response_bytes": self.current_page_bytes},
                self.limits.max_response_bytes,
            )
        if self.total_bytes > self.limits.max_total_bytes:
            raise LimitExceededError(
                "max_total_bytes",
                "Max total bytes exceeded",
                {"total_bytes": self.total_bytes},
                self.limits.max_total_bytes,
            )

    def finish_page(self) -> None:
        self.pages_fetched += 1
        self.consecutive_failures = 0

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        if self.consecutive_failures > self.limits.max_consecutive_failures:
            raise LimitExceededError(
                "max_consecutive_failures",
                "Max consecutive failures exceeded",
                {"consecutive_failures": self.consecutive_failures},
                self.limits.max_consecutive_failures,
            )
