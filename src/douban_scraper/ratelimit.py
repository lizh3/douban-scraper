"""Shared rate limiting and error handling for douban_scraper."""

import time
from dataclasses import dataclass
from enum import Enum


class RetryDecision(Enum):
    """Decision on whether to retry or fail."""

    RETRY = "retry"
    FATAL = "fatal"


@dataclass
class RetryConfig:
    """Configuration for retry behavior with exponential backoff."""

    max_retries: int = 3
    backoff_base: float = 5.0


class RateLimiter:
    """Enforces a minimum delay between successive calls."""

    def __init__(self, delay: float = 1.5) -> None:
        self.delay = delay
        self._last_call: float | None = None

    def wait(self) -> None:
        now = time.monotonic()
        if self._last_call is not None:
            elapsed = now - self._last_call
            remaining = max(0, self.delay - elapsed)
            if remaining > 0:
                time.sleep(remaining)
        self._last_call = time.monotonic()


def handle_api_error(code: int) -> RetryDecision:
    """Classify an API error code as retryable or fatal."""
    # 1080 = rate limit -> retryable
    if code == 1080:
        return RetryDecision.RETRY
    # 5xx server errors -> retryable
    if 500 <= code < 600:
        return RetryDecision.RETRY
    # 996 = invalid signature -> fatal
    # 1000 = invalid user -> fatal
    return RetryDecision.FATAL
