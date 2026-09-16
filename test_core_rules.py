import unittest

from tudasjargany.core.rules import add_stars, collision_speed_level, restore_life, road_speed
from tudasjargany.core.state import GameMode, GameState


class GameStateTests(unittest.TestCase):
    def test_game_mode_is_compatible_with_plain_strings(self):
        self.assertEqual(GameMode.CAR, "car")
        self.assertEqual(str(GameMode.HELICOPTER), "helicopter")

    def test_reset_preserves_or_changes_mode(self):
        state = GameState(score=31, lives=1, speed_level=3, mode=GameMode.HELICOPTER)
        state.reset()
        self.assertEqual((state.score, state.lives, state.speed_level), (0, 3, 0))
        self.assertEqual(state.mode, GameMode.HELICOPTER)
        state.reset(GameMode.UNICORN)
        self.assertEqual(state.mode, GameMode.UNICORN)


class RuleTests(unittest.TestCase):
    def test_crossed_milestones_queue_the_right_tasks(self):
        change = add_stars(9, 0, 22)
        self.assertEqual(change.score, 31)
        self.assertEqual(change.speed_level, 3)
        self.assertEqual(change.bonus_challenges, 2)
        self.assertEqual(change.life_challenges, 1)
        self.assertEqual(road_speed(change.speed_level), 11.3)

    def test_unicorn_queues_only_coloring(self):
        change = add_stars(9, 0, 12, unicorn=True)
        self.assertEqual(change.coloring_challenges, 2)
        self.assertEqual(change.speed_level, 0)

    def test_life_and_collision_limits(self):
        self.assertEqual(collision_speed_level(0), 0)
        self.assertEqual(collision_speed_level(2), 1)
        self.assertEqual(restore_life(3), 3)


if __name__ == "__main__":
    unittest.main()
