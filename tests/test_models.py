"""Tests for Pydantic models using live fixtures."""
import json

import pytest
from pathlib import Path

from douban_scraper.models import FrodoInterestsResponse, FrodoInterest, FrodoSubject

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_movie_interests():
    data = json.loads((FIXTURES / "frodo_movie_interests.json").read_text())
    resp = FrodoInterestsResponse.model_validate(data)
    assert resp.start == 0
    assert resp.count == 3
    assert resp.total == 551
    assert len(resp.interests) == 3
    first = resp.interests[0]
    assert first.comment is not None
    assert first.subject is not None
    assert first.subject.title is not None
    assert first.rating is not None
    assert first.rating["value"] > 0


def test_parse_book_interests():
    data = json.loads((FIXTURES / "frodo_book_interests.json").read_text())
    resp = FrodoInterestsResponse.model_validate(data)
    assert resp.count == len(resp.interests)
    assert resp.total == 70
    for interest in resp.interests:
        assert interest.subject is not None


def test_parse_music_interests_empty():
    data = json.loads((FIXTURES / "frodo_music_interests.json").read_text())
    resp = FrodoInterestsResponse.model_validate(data)
    assert resp.total == 0
    assert len(resp.interests) == 0


def test_unicode_in_comment():
    data = json.loads((FIXTURES / "frodo_movie_interests.json").read_text())
    resp = FrodoInterestsResponse.model_validate(data)
    first_comment = resp.interests[0].comment
    assert first_comment is not None
    # Should contain Chinese characters
    assert any("\u4e00" <= c <= "\u9fff" for c in first_comment)


def test_subject_fields():
    data = json.loads((FIXTURES / "frodo_movie_interests.json").read_text())
    resp = FrodoInterestsResponse.model_validate(data)
    subject = resp.interests[0].subject
    assert isinstance(subject, FrodoSubject)
    assert subject.id == "37134598"
    assert subject.title == "相反的你和我"
    assert subject.type == "tv"
    assert subject.url.startswith("https://")


def test_interest_fields():
    data = json.loads((FIXTURES / "frodo_movie_interests.json").read_text())
    resp = FrodoInterestsResponse.model_validate(data)
    interest = resp.interests[1]
    assert interest.status == "done"
    assert interest.create_time is not None
    assert isinstance(interest.tags, list)


def test_model_extra_fields_allowed():
    """Extra fields in JSON should not cause validation errors."""
    data = json.loads((FIXTURES / "frodo_movie_interests.json").read_text())
    resp = FrodoInterestsResponse.model_validate(data)
    # The fixture has extra fields like "filters" — model should accept them
    assert resp.interests is not None
