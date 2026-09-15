import unittest
from unittest.mock import patch

from main import TudasJarganyGame


class HelicopterModeTests(unittest.TestCase):
    def test_helicopter_mode_spawns_stars_clouds_and_birds(self) -> None:
        with patch("main.random.random", return_value=0.20):
            self.assertEqual(TudasJarganyGame._random_road_kind(True), "star")
        with patch("main.random.random", return_value=0.70):
            self.assertEqual(TudasJarganyGame._random_road_kind(True), "cloud")
        with patch("main.random.random", return_value=0.90):
            self.assertEqual(TudasJarganyGame._random_road_kind(True), "bird")

    def test_car_mode_keeps_road_obstacles(self) -> None:
        with patch("main.random.random", return_value=0.70):
            self.assertEqual(TudasJarganyGame._random_road_kind(), "motorcycle")


if __name__ == "__main__":
    unittest.main()