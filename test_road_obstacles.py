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

    def test_car_mode_includes_roadwork_vehicles(self) -> None:
        with patch("main.random.random", return_value=0.94):
            self.assertEqual(TudasJarganyGame._random_road_kind(), "asphalt_paver")
        with patch("main.random.random", return_value=0.97):
            self.assertEqual(TudasJarganyGame._random_road_kind(), "dumper")

    def test_dumper_leaves_a_dirt_pile_in_its_lane(self) -> None:
        dirt_pile = TudasJarganyGame._dumper_dirt_pile(3)
        self.assertEqual(dirt_pile["kind"], "dirt_pile")
        self.assertEqual(dirt_pile["lane"], 3)
        self.assertLess(float(dirt_pile["y"]), -45.0)

    def test_dumper_occupies_two_neighboring_lanes(self) -> None:
        dumper = {"kind": "dumper", "lane": 1, "lane_span": 2, "lane_position": 1.5, "y": 0.0}
        self.assertEqual(TudasJarganyGame._road_item_lanes(dumper), (1, 2))
        self.assertFalse(TudasJarganyGame._road_item_hits_lane(dumper, 0))
        self.assertTrue(TudasJarganyGame._road_item_hits_lane(dumper, 1))
        self.assertTrue(TudasJarganyGame._road_item_hits_lane(dumper, 2))
        self.assertFalse(TudasJarganyGame._road_item_hits_lane(dumper, 3))

if __name__ == "__main__":
    unittest.main()
