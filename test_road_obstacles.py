import unittest
from unittest.mock import patch

from main import TudasJarganyGame


class WildMotorcycleTests(unittest.TestCase):
    def test_motorcycle_is_generated_as_road_item(self) -> None:
        with patch("main.random.random", return_value=0.70):
            self.assertEqual(TudasJarganyGame._random_road_kind(), "motorcycle")

    def test_motorcycle_zigzags_inside_four_lanes(self) -> None:
        item = {"kind": "motorcycle", "lane": 1, "lane_position": 1.0, "lane_direction": 1.0, "y": 0.0}
        positions = []
        for _ in range(80):
            TudasJarganyGame._move_wild_motorcycle(item)
            positions.append(float(item["lane_position"]))
            self.assertGreaterEqual(float(item["lane_position"]), 0.0)
            self.assertLessEqual(float(item["lane_position"]), 3.0)
            self.assertIn(int(item["lane"]), range(4))
        self.assertGreater(len({round(position, 2) for position in positions}), 8)


if __name__ == "__main__":
    unittest.main()