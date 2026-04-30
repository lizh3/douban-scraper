"""Integration smoke tests — hit the live Douban API.

Run with: pytest tests/test_integration.py -v -m integration --timeout=120
"""

import json
import os
import subprocess

import pytest

from douban_scraper.frodo import API_KEY, DEFAULT_USER_AGENT, HMAC_SECRET, DoubanFrodoClient

pytestmark = pytest.mark.integration

USER_ID = os.environ.get("DOUBAN_TEST_USER_ID", "1000001")


@pytest.fixture
def frodo_client():
    return DoubanFrodoClient(
        api_key=API_KEY,
        api_secret=HMAC_SECRET,
        user_agent=DEFAULT_USER_AGENT,
    )


def test_validate_user(frodo_client):
    """A valid user should be accepted."""
    assert frodo_client.validate_user(USER_ID) is True


def test_validate_invalid_user(frodo_client):
    """User '999999999999' should be invalid."""
    assert frodo_client.validate_user("999999999999") is False


def test_export_movies_smoke(frodo_client):
    """Export first page of movies, verify structure of first 5."""
    items = frodo_client.export_all(
        user_id=USER_ID,
        type_="movie",
        status="done",
        max_items=5,
    )
    assert len(items) >= 5
    for item in items[:5]:
        assert "subject" in item
        assert "title" in item["subject"]
        if "rating" in item:
            assert "value" in item["rating"]


def test_export_books_smoke(frodo_client):
    """Export first 3 books, verify structure."""
    items = frodo_client.export_all(
        user_id=USER_ID,
        type_="book",
        status="done",
        max_items=3,
    )
    assert len(items) >= 1
    for item in items:
        assert "subject" in item


def test_unicode_in_output(frodo_client):
    """Verify Chinese characters survive the round-trip."""
    items = frodo_client.export_all(
        user_id=USER_ID,
        type_="movie",
        status="done",
        max_items=1,
    )
    assert len(items) >= 1
    json_str = json.dumps(items, ensure_ascii=False)
    assert any("\u4e00" <= c <= "\u9fff" for c in json_str)
    parsed = json.loads(json_str)
    assert parsed == items


def test_full_cli_export(tmp_path):
    """Run the full CLI export for movies with max_items=3."""
    result = subprocess.run(
        [
            ".venv/bin/douban-scraper",
            "export",
            "--user",
            USER_ID,
            "--types",
            "movie",
            "--status",
            "done",
            "--max-items",
            "3",
            "--output",
            str(tmp_path),
            "--force",
        ],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        timeout=60,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    movies_file = tmp_path / "movies.json"
    assert movies_file.exists()

    data = json.loads(movies_file.read_text())
    assert len(data) == 3
    for item in data:
        assert "subject" in item


def test_resumability(frodo_client, tmp_path):
    """State manager tracks offset and export_all accepts start_offset."""
    from douban_scraper.state import StateManager

    items1 = frodo_client.export_all(
        user_id=USER_ID,
        type_="movie",
        status="done",
        max_items=3,
    )
    assert len(items1) > 0

    sm = StateManager(tmp_path)
    state = sm.load()
    key = "movie_done"
    state[key] = {"start": len(items1), "completed": False}
    sm.save(state)

    assert sm.get_offset(key) == len(items1)

    items2 = frodo_client.export_all(
        user_id=USER_ID,
        type_="movie",
        status="done",
        max_items=3,
        start_offset=sm.get_offset(key),
    )
    assert len(items2) > 0

    ids1 = {i["subject"]["id"] for i in items1}
    ids2 = {i["subject"]["id"] for i in items2}
    overlap = ids1.intersection(ids2)
    assert len(overlap) < len(ids1), (
        f"Near-total overlap ({len(overlap)}/{len(ids1)}): offset not applied"
    )
