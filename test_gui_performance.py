"""A gyakori GUI-frissitesek optimalizalasainak tesztjei."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from main import TudasJarganyGame


class GuiPerformanceTests(unittest.TestCase):
    def test_unchanged_drive_status_does_not_reconfigure_label(self) -> None:
        game = SimpleNamespace(
            score=4,
            lives=3,
            speed_level=1,
            last_drive_status=None,
            status=Mock(),
            _is_unicorn_mode=lambda: False,
            _is_helicopter_mode=lambda: False,
        )

        TudasJarganyGame._update_drive_status(game)
        TudasJarganyGame._update_drive_status(game)

        game.status.configure.assert_called_once()

    def test_changed_drive_status_reconfigures_label(self) -> None:
        game = SimpleNamespace(
            score=4,
            lives=3,
            speed_level=1,
            last_drive_status=None,
            status=Mock(),
            _is_unicorn_mode=lambda: False,
            _is_helicopter_mode=lambda: False,
        )

        TudasJarganyGame._update_drive_status(game)
        game.score += 1
        TudasJarganyGame._update_drive_status(game)

        self.assertEqual(game.status.configure.call_count, 2)


if __name__ == "__main__":
    unittest.main()
