import unittest
from unittest.mock import patch

from main import COLORING_ANIMALS, TudasJarganyGame


class UnicornModeTests(unittest.TestCase):
    def test_unicorn_mode_spawns_stars_and_dragons(self) -> None:
        with patch("main.random.random", return_value=0.40):
            self.assertEqual(
                TudasJarganyGame._random_road_kind(unicorn=True),
                "unicorn_star",
            )
        with patch("main.random.random", return_value=0.99):
            self.assertEqual(
                TudasJarganyGame._random_road_kind(unicorn=True),
                "unicorn_dragon",
            )
    def test_other_modes_keep_existing_spawns(self) -> None:
        with patch("main.random.random", return_value=0.70):
            self.assertEqual(TudasJarganyGame._random_road_kind(), "motorcycle")
            self.assertEqual(TudasJarganyGame._random_road_kind(helicopter=True), "cloud")

    def test_tenth_star_queues_coloring_without_math_or_speed(self) -> None:
        class UnicornScore:
            score = 9
            pending_coloring_challenges = 0
            message = ""
            message_frames = 0

            @staticmethod
            def _is_unicorn_mode() -> bool:
                return True

            @staticmethod
            def _update_drive_status() -> None:
                pass

        game = UnicornScore()
        self.assertTrue(TudasJarganyGame._add_stars(game, 1))
        self.assertEqual(game.score, 10)
        self.assertEqual(game.pending_coloring_challenges, 1)

    def test_twenty_coloring_animals_do_not_repeat_immediately(self) -> None:
        self.assertEqual(len(COLORING_ANIMALS), 20)
        self.assertEqual(len(set(COLORING_ANIMALS)), 20)

        class AnimalPicker:
            last_coloring_animal = None

        picker = AnimalPicker()
        with patch("main.random.choice", side_effect=lambda choices: choices[0]):
            first = TudasJarganyGame._next_coloring_animal(picker)
            second = TudasJarganyGame._next_coloring_animal(picker)
        self.assertNotEqual(first, second)
if __name__ == "__main__":
    unittest.main()