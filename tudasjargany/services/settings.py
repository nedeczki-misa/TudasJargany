"""Helyi, következő indításkor is megmaradó játékbeállítások."""

from __future__ import annotations

import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parents[2] / "beallitasok.json"
DEFAULT_SUBJECTS = ("MATEK",)


def load_enabled_subjects(
    available_subjects: tuple[str, ...],
    path: Path = SETTINGS_FILE,
) -> tuple[str, ...]:
    """Betölti a korábban kijelölt tantárgyakat, hibás fájlnál alapértéket ad."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_SUBJECTS
    subjects = raw.get("enabled_subjects") if isinstance(raw, dict) else None
    if not isinstance(subjects, list):
        return DEFAULT_SUBJECTS
    selected = tuple(subject for subject in available_subjects if subject in subjects)
    return selected or DEFAULT_SUBJECTS


def save_enabled_subjects(
    subjects: tuple[str, ...],
    path: Path = SETTINGS_FILE,
) -> None:
    """Biztonságosan elmenti a kijelölt tantárgyakat a következő indításhoz."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps({"enabled_subjects": list(subjects)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(path)