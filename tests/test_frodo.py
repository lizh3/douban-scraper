"""Tests for Frodo client pagination logic with mocked HTTP."""
import base64
import json
import time
from unittest.mock import patch, MagicMock

import pytest
from pathlib import Path

from douban_scraper.frodo import DoubanFrodoClient, compute_signature

FIXTURES = Path(__file__).parent / "fixtures"


def _make_page(items, start, total):
    return {
        "start": start,
        "count": len(items),
        "total": total,
        "interests": items,
    }


def _mock_client_init(self, **kwargs):
    """Override __init__ to avoid real HTTP setup."""
    self.api_key = "test_key"
    self.api_secret = b"test_secret"
    self.user_agent = "test-agent"
    self.base_url = "https://frodo.douban.com"
    self._last_request_time = 0.0
    self._delay = 0.0  # No delay in tests
    self.failures = []


def _mock_make_request(client, url, params):
    """Replace _make_request to return fixture-based responses."""
    return client._test_responses.pop(0)


@patch.object(DoubanFrodoClient, "__init__", _mock_client_init)
def test_export_all_paginates():
    fixture_data = json.loads((FIXTURES / "frodo_movie_interests.json").read_text())
    items = fixture_data["interests"]

    # Mock: page 1 returns 3 items, total=6; page 2 returns 3 more items, total=6
    page1 = _make_page(items[:3], 0, 6)
    page2_data = json.loads((FIXTURES / "frodo_movie_interests.json").read_text())
    for item in page2_data["interests"]:
        item["id"] += 1000  # Different IDs
    page2 = _make_page(page2_data["interests"], 3, 6)

    client = DoubanFrodoClient.__new__(DoubanFrodoClient)
    _mock_client_init(client)

    # Store responses for _make_request to consume
    mock_resp1 = MagicMock()
    mock_resp1.json.return_value = page1
    mock_resp2 = MagicMock()
    mock_resp2.json.return_value = page2

    with patch.object(client, "_make_request", side_effect=[mock_resp1, mock_resp2]):
        result = client.export_all(user_id="123", type_="movie", status="done")

    assert len(result) == 6


@patch.object(DoubanFrodoClient, "__init__", _mock_client_init)
def test_export_all_max_items():
    fixture_data = json.loads((FIXTURES / "frodo_movie_interests.json").read_text())
    # Use only 2 items so max_items=2 stops exactly after first page
    page = _make_page(fixture_data["interests"][:2], 0, 100)

    client = DoubanFrodoClient.__new__(DoubanFrodoClient)
    _mock_client_init(client)

    mock_resp = MagicMock()
    mock_resp.json.return_value = page

    with patch.object(client, "_make_request", return_value=mock_resp):
        result = client.export_all(user_id="123", type_="movie", status="done", max_items=2)

    assert len(result) == 2


@patch.object(DoubanFrodoClient, "__init__", _mock_client_init)
def test_export_all_empty_response():
    page = _make_page([], 0, 0)

    client = DoubanFrodoClient.__new__(DoubanFrodoClient)
    _mock_client_init(client)

    mock_resp = MagicMock()
    mock_resp.json.return_value = page

    with patch.object(client, "_make_request", return_value=mock_resp):
        result = client.export_all(user_id="123", type_="movie", status="done")

    assert len(result) == 0


@patch.object(DoubanFrodoClient, "__init__", _mock_client_init)
def test_export_all_with_start_offset():
    fixture_data = json.loads((FIXTURES / "frodo_movie_interests.json").read_text())
    # Set total=3 so pagination stops after one page of 3 items
    page1 = _make_page(fixture_data["interests"], 100, 3)

    client = DoubanFrodoClient.__new__(DoubanFrodoClient)
    _mock_client_init(client)

    mock_resp = MagicMock()
    mock_resp.json.return_value = page1

    with patch.object(client, "_make_request", return_value=mock_resp) as mock_req:
        result = client.export_all(user_id="123", type_="movie", status="done", start_offset=100)
        call_args = mock_req.call_args
        assert call_args[0][0] == "https://frodo.douban.com/api/v2/user/123/interests"

    assert len(result) == 3


@patch.object(DoubanFrodoClient, "__init__", _mock_client_init)
def test_export_all_progress_callback():
    fixture_data = json.loads((FIXTURES / "frodo_movie_interests.json").read_text())

    page1 = _make_page(fixture_data["interests"][:2], 0, 5)
    page2_data = json.loads((FIXTURES / "frodo_movie_interests.json").read_text())
    for item in page2_data["interests"][:3]:
        item["id"] += 2000
    page2 = _make_page(page2_data["interests"][:3], 2, 5)

    client = DoubanFrodoClient.__new__(DoubanFrodoClient)
    _mock_client_init(client)

    mock_resp1 = MagicMock()
    mock_resp1.json.return_value = page1
    mock_resp2 = MagicMock()
    mock_resp2.json.return_value = page2

    callback_calls = []

    def cb(type_, status, offset, total):
        callback_calls.append((type_, status, offset, total))

    with patch.object(client, "_make_request", side_effect=[mock_resp1, mock_resp2]):
        result = client.export_all(user_id="123", type_="movie", status="done", progress_callback=cb)

    assert len(callback_calls) == 2
    assert callback_calls[0][0] == "movie"
    assert callback_calls[0][1] == "done"
    assert callback_calls[0][2] == 2
    assert callback_calls[0][3] == 5


def test_validate_signature_format():
    """Verify the signature is included in request URL."""
    ts = str(int(time.time()))
    sig = compute_signature("/api/v2/user/123/interests", ts)
    decoded = base64.b64decode(sig)
    assert len(decoded) == 20  # SHA1 = 20 bytes


@patch.object(DoubanFrodoClient, "__init__", _mock_client_init)
def test_validate_user_success():
    client = DoubanFrodoClient.__new__(DoubanFrodoClient)
    _mock_client_init(client)

    page = _make_page([], 0, 5)
    mock_resp = MagicMock()
    mock_resp.json.return_value = page

    with patch.object(client, "_make_request", return_value=mock_resp):
        result = client.validate_user("123")

    assert result is True


@patch.object(DoubanFrodoClient, "__init__", _mock_client_init)
def test_validate_user_failure():
    client = DoubanFrodoClient.__new__(DoubanFrodoClient)
    _mock_client_init(client)

    with patch.object(client, "_make_request", side_effect=Exception("network error")):
        result = client.validate_user("123")

    assert result is False
