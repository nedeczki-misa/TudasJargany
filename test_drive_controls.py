import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from main import BASE_ROAD_SPEED, SPEED_STEP, TudasJarganyGame


class DriveControlsTests(unittest.TestCase):
    def _game(self) -> SimpleNamespace:
        return SimpleNamespace(
            mode="drive",
            math_active=False,
            coloring_active=False,
            speed_level=0,
            highest_speed_level=0,
            road_speed=BASE_ROAD_SPEED,
            speed_just_increased=False,
            message="",
            message_frames=0,
            last_drive_status=None,
            drive_paused=False,
            animation_job="drive-tick",
            after_cancel=Mock(),
            _play_speed_up_sound=Mock(),
            _update_drive_status=Mock(),
            _draw_road=Mock(),
            _drive_tick=Mock(),
        )

    def test_slowing_down_to_zero_stops_the_road(self) -> None:
        game = self._game()

        TudasJarganyGame._change_drive_speed(game, -1)

        self.assertEqual(game.speed_level, -1)
        self.assertEqual(game.road_speed, 0)
        self.assertIn("MEGÁLLTÁL", game.message)

    def test_accelerating_from_zero_restarts_at_base_speed(self) -> None:
        game = self._game()
        game.speed_level = -1
        game.road_speed = 0

        TudasJarganyGame._change_drive_speed(game, 1)

        self.assertEqual(game.speed_level, 0)
        self.assertEqual(game.road_speed, BASE_ROAD_SPEED)
        game._play_speed_up_sound.assert_called_once()

    def test_acceleration_increases_one_speed_level(self) -> None:
        game = self._game()

        TudasJarganyGame._change_drive_speed(game, 1)

        self.assertEqual(game.speed_level, 1)
        self.assertEqual(game.road_speed, BASE_ROAD_SPEED + SPEED_STEP)

    def test_space_pause_stops_and_resumes_the_animation(self) -> None:
        game = self._game()

        TudasJarganyGame._toggle_drive_pause(game)
        self.assertTrue(game.drive_paused)
        game.after_cancel.assert_called_once_with("drive-tick")

        TudasJarganyGame._toggle_drive_pause(game)
        self.assertFalse(game.drive_paused)
        game._drive_tick.assert_called_once()


if __name__ == "__main__":
    unittest.main()