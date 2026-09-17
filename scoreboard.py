"""Helyi TOP 10 ranglista a TudasJargany játékhoz."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RESULTS_FILE = Path(__file__).with_name("eredmenyek.json")
TOP_LIMIT = 10


def _clean_name(value: object) -> str:
    name = " ".join(str(value or "").split())
    return name[:18] or "Névtelen"


def _nonnegative_int(value: object) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _clean_result(result: dict[str, Any]) -> dict[str, Any]:
    stats = result.get("stats", {})
    if not isinstance(stats, dict):
        stats = {}
    return {
        "name": _clean_name(result.get("name")),
        "stars": _nonnegative_int(result.get("stars", 0)),
        "when": str(result.get("when", ""))[:24],
        "mode": str(result.get("mode", ""))[:30],
        "stats": {
            "duration_seconds": _nonnegative_int(stats.get("duration_seconds", 0)),
            "tasks_shown": _nonnegative_int(stats.get("tasks_shown", 0)),
            "tasks_correct": _nonnegative_int(stats.get("tasks_correct", 0)),
            "tasks_wrong": _nonnegative_int(stats.get("tasks_wrong", 0)),
            "tasks_timed_out": _nonnegative_int(stats.get("tasks_timed_out", 0)),
            "lives": _nonnegative_int(stats.get("lives", 0)),
            "top_speed": _nonnegative_int(stats.get("top_speed", 0)),
        },
    }


def _sort_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        results,
        key=lambda result: (
            int(result["stars"]),
            int(result["stats"]["tasks_correct"]),
            result["when"],
        ),
        reverse=True,
    )[:TOP_LIMIT]


def load_top_scores(path: Path = RESULTS_FILE) -> list[dict[str, Any]]:
    """Betölti a használható, legfeljebb tíz helyi eredményt."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(raw, list):
        return []
    valid = [_clean_result(item) for item in raw if isinstance(item, dict)]
    return _sort_results(valid)


def save_result(result: dict[str, Any], path: Path = RESULTS_FILE) -> list[dict[str, Any]]:
    """Elment egy eredményt, majd visszaadja az új TOP 10 listát."""
    scores = _sort_results([*load_top_scores(path), _clean_result(result)])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(scores, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(path)
    return scores
