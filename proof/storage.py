"""Persistent atomic JSON storage for Anonnix.

All data files stored in DATA_DIR (env ANONNIX_DATA_DIR, default: /tmp/anonnix/).
Atomic writes via tmp+rename. Thread-safe via threading.Lock.
All operations (read+write) happen under lock to prevent TOCTOU races.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any

log = logging.getLogger(__name__)

DATA_DIR = os.environ.get("ANONNIX_DATA_DIR", "/data")


class JsonStore:
    """Thread-safe JSON file storage with atomic writes.

    All public methods acquire lock before any read/write to prevent
    race conditions between concurrent threads/coroutines.
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self._path = os.path.join(DATA_DIR, f"{name}.json")
        self._data: dict[str, Any] = {}
        self._loaded = False
        self._load_succeeded = False  # guard: refuse writes if load never succeeded
        self._lock = threading.Lock()

    def _ensure_dir(self) -> None:
        os.makedirs(DATA_DIR, exist_ok=True)

    def _load_unlocked(self) -> None:
        """Load from disk. Must be called WITH lock held."""
        if self._loaded:
            return
        try:
            if os.path.exists(self._path):
                with open(self._path) as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    self._data = raw
                elif isinstance(raw, list):
                    self._data = {"_list": raw}
            self._loaded = True
            self._load_succeeded = True
        except Exception:
            log.exception("Failed to load %s, will retry", self._path)

    def _save_unlocked(self) -> None:
        """Save to disk atomically. Must be called WITH lock held."""
        if not self._load_succeeded and os.path.exists(self._path):
            log.error("Refusing to write %s: load never succeeded (data corruption guard)", self._path)
            return
        try:
            self._ensure_dir()
            tmp = self._path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(self._data, f, separators=(",", ":"))
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self._path)
        except Exception:
            log.exception("Failed to save %s", self._path)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            self._load_unlocked()
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._load_unlocked()
            self._data[key] = value
            self._save_unlocked()

    def pop(self, key: str, default: Any = None) -> Any:
        with self._lock:
            self._load_unlocked()
            val = self._data.pop(key, default)
            self._save_unlocked()
            return val

    def keys(self) -> list[str]:
        with self._lock:
            self._load_unlocked()
            return list(self._data.keys())

    def items(self) -> list[tuple[str, Any]]:
        with self._lock:
            self._load_unlocked()
            return list(self._data.items())

    def update(self, data: dict) -> None:
        with self._lock:
            self._load_unlocked()
            self._data.update(data)
            self._save_unlocked()

    def cleanup(self, predicate) -> int:
        """Remove entries where predicate(key, value) is True."""
        with self._lock:
            self._load_unlocked()
            to_remove = [k for k, v in self._data.items() if predicate(k, v)]
            for k in to_remove:
                del self._data[k]
            if to_remove:
                self._save_unlocked()
            return len(to_remove)

    def get_list(self) -> list:
        with self._lock:
            self._load_unlocked()
            return list(self._data.get("_list", []))  # return copy

    def append_list(self, item: Any) -> None:
        with self._lock:
            self._load_unlocked()
            lst = self._data.setdefault("_list", [])
            lst.append(item)
            self._save_unlocked()

    @property
    def count(self) -> int:
        with self._lock:
            self._load_unlocked()
            return len(self._data)
