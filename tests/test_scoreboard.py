import json
import tempfile
import unittest
from pathlib import Path

from tudasjargany.services.scoreboard import load_top_scores, save_result


class ScoreboardTests(unittest.TestCase):
    def test_keeps_only_the_top_ten_scores(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "eredmenyek.json"
            for stars in range(12):
                save_result(
                    {
                        "name": f"Játékos {stars}",
                        "stars": stars,
                        "when": f"2026.09.17. 10:{stars:02}",
                        "stats": {"tasks_correct": stars},
                    },
                    path,
                )

            scores = load_top_scores(path)

        self.assertEqual(len(scores), 10)
        self.assertEqual(scores[0]["stars"], 11)
        self.assertEqual(scores[-1]["stars"], 2)

    def test_saves_stats_and_sanitises_the_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "eredmenyek.json"
            scores = save_result(
                {
                    "name": "  Kolos   ",
                    "stars": 18,
                    "when": "2026.09.17. 12:30",
                    "stats": {
                        "duration_seconds": 95,
                        "tasks_shown": 6,
                        "tasks_correct": 5,
                        "tasks_wrong": 1,
                        "tasks_timed_out": 0,
                        "lives": 2,
                        "top_speed": 4,
                    },
                },
                path,
            )
            stored = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(scores[0]["name"], "Kolos")
        self.assertEqual(scores[0]["stats"]["tasks_correct"], 5)
        self.assertEqual(stored, scores)

    def test_bad_or_missing_file_means_empty_scoreboard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "eredmenyek.json"
            path.write_text("ez nem json", encoding="utf-8")

            self.assertEqual(load_top_scores(path), [])

    def test_bad_numeric_values_are_made_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "eredmenyek.json"
            path.write_text(
                json.dumps([{"name": "Kolos", "stars": "sok", "stats": {"tasks_correct": None}}]),
                encoding="utf-8",
            )

            scores = load_top_scores(path)

        self.assertEqual(scores[0]["stars"], 0)
        self.assertEqual(scores[0]["stats"]["tasks_correct"], 0)

if __name__ == "__main__":
    unittest.main()
