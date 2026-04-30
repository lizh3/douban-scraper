"""Tests for StateManager."""
import json

import pytest
from pathlib import Path

from douban_scraper.state import StateManager


def test_load_empty(tmp_path):
    sm = StateManager(tmp_path)
    state = sm.load()
    assert state == {}


def test_save_and_load(tmp_path):
    sm = StateManager(tmp_path)
    state = {"movie_done": {"start": 50, "completed": False}}
    sm.save(state)
    loaded = sm.load()
    assert loaded == state


def test_get_offset(tmp_path):
    sm = StateManager(tmp_path)
    sm.save({"movie_done": {"start": 100, "completed": False}})
    assert sm.get_offset("movie_done") == 100


def test_get_offset_missing(tmp_path):
    sm = StateManager(tmp_path)
    assert sm.get_offset("nonexistent") == 0


def test_get_offset_no_start_key(tmp_path):
    sm = StateManager(tmp_path)
    sm.save({"movie_done": {"completed": True}})
    assert sm.get_offset("movie_done") == 0


def test_mark_completed(tmp_path):
    sm = StateManager(tmp_path)
    sm.mark_completed("movie_done")
    state = sm.load()
    assert state["movie_done"]["completed"] is True


def test_mark_completed_existing_entry(tmp_path):
    sm = StateManager(tmp_path)
    sm.save({"movie_done": {"start": 50, "completed": False}})
    sm.mark_completed("movie_done")
    state = sm.load()
    assert state["movie_done"]["completed"] is True
    assert state["movie_done"]["start"] == 50


def test_is_completed(tmp_path):
    sm = StateManager(tmp_path)
    assert not sm.is_completed("movie_done")
    sm.mark_completed("movie_done")
    assert sm.is_completed("movie_done")


def test_is_completed_missing_key(tmp_path):
    sm = StateManager(tmp_path)
    assert sm.is_completed("nonexistent") is False


def test_atomic_write(tmp_path):
    """State file should be valid JSON after save."""
    sm = StateManager(tmp_path)
    sm.save({"test": {"start": 5, "completed": False}})
    state_file = tmp_path / ".progress.json"
    assert state_file.exists()
    data = json.loads(state_file.read_text())
    assert data["test"]["start"] == 5


def test_progress_file_path(tmp_path):
    sm = StateManager(tmp_path)
    assert sm.progress_file == tmp_path / ".progress.json"


def test_creates_output_dir(tmp_path):
    nested = tmp_path / "a" / "b" / "c"
    sm = StateManager(nested)
    sm.save({"key": {"start": 0, "completed": False}})
    assert nested.exists()
    assert (nested / ".progress.json").exists()
