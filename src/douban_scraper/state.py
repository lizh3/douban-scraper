"""Progress state manager for resumable scraping."""

from __future__ import annotations

import json
import os
from pathlib import Path


class StateManager:
    """Manages a JSON progress file for tracking scraping state.

    Key format: "{type}_{status}" e.g., "movie_done", "book_mark".
    """

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    @property
    def progress_file(self) -> Path:
        return self.output_dir / ".progress.json"

    def load(self) -> dict:
        """Read the progress file. Returns {} if not found."""
        if not self.progress_file.exists():
            return {}
        with open(self.progress_file, "r") as f:
            return json.load(f)

    def save(self, progress: dict) -> None:
        """Write progress dict to file atomically."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = str(self.progress_file) + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, str(self.progress_file))

    def get_offset(self, key: str) -> int:
        """Return progress[key]["start"] if key exists, else 0."""
        progress = self.load()
        entry = progress.get(key)
        if entry is not None:
            return entry.get("start", 0)
        return 0

    def mark_completed(self, key: str) -> None:
        """Load progress, set key["completed"] = True, save."""
        progress = self.load()
        if key in progress:
            progress[key]["completed"] = True
        else:
            progress[key] = {"completed": True}
        self.save(progress)

    def is_completed(self, key: str) -> bool:
        """Return key["completed"] if exists, else False."""
        progress = self.load()
        entry = progress.get(key)
        if entry is not None:
            return entry.get("completed", False)
        return False
