import unittest
from unittest.mock import patch

from tudasjargany.app import TudasJarganyGame


class HelicopterModeTests(unittest.TestCase):
    def test_helicopter_mode_spawns_stars_clouds_birds_and_planes(self) -> None:
        with patch("tudasjargany.app.random.random", return_value=0.20):
            self.assertEqual(TudasJarganyGame._random_road_kind(True), "star")
        with patch("tudasjargany.app.random.random", return_value=0.70):
            self.assertEqual(TudasJarganyGame._random_road_kind(True), "cloud")
        with patch("tudasjargany.app.random.random", return_value=0.90):
            self.assertEqual(TudasJarganyGame._random_road_kind(True), "bird")
        with patch("tudasjargany.app.random.random", return_value=0.95):
            self.assertEqual(TudasJarganyGame._random_road_kind(True), "plane")

    def test_car_mode_keeps_road_obstacles(self) -> None:
        with patch("tudasjargany.app.random.random", return_value=0.70):
            self.assertEqual(TudasJarganyGame._random_road_kind(), "motorcycle")


if __name__ == "__main__":
    unittest.main()
