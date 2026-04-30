"""Tests for rate limiting and error handling."""
import time

import pytest

from douban_scraper.ratelimit import RetryDecision, handle_api_error, RateLimiter, RetryConfig


def test_handle_api_error_rate_limit():
    decision = handle_api_error(1080)
    assert decision == RetryDecision.RETRY


def test_handle_api_error_invalid_sig():
    decision = handle_api_error(996)
    assert decision == RetryDecision.FATAL


def test_handle_api_error_server_error_500():
    decision = handle_api_error(500)
    assert decision == RetryDecision.RETRY


def test_handle_api_error_server_error_503():
    decision = handle_api_error(503)
    assert decision == RetryDecision.RETRY


def test_handle_api_error_server_error_599():
    decision = handle_api_error(599)
    assert decision == RetryDecision.RETRY


def test_handle_api_error_unknown():
    decision = handle_api_error(9999)
    assert decision == RetryDecision.FATAL


def test_handle_api_error_invalid_user():
    decision = handle_api_error(1000)
    assert decision == RetryDecision.FATAL


def test_rate_limiter_delay():
    rl = RateLimiter(delay=0.05)
    start = time.monotonic()
    rl.wait()
    rl.wait()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.04  # Should have waited at least ~delay


def test_rate_limiter_first_call_no_wait():
    rl = RateLimiter(delay=10.0)
    start = time.monotonic()
    rl.wait()
    elapsed = time.monotonic() - start
    assert elapsed < 1.0  # First call should not sleep


def test_retry_config_defaults():
    config = RetryConfig()
    assert config.max_retries == 3
    assert config.backoff_base == 5.0


def test_retry_decision_enum_values():
    assert RetryDecision.RETRY.value == "retry"
    assert RetryDecision.FATAL.value == "fatal"
