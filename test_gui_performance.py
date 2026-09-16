"""A gyakori GUI-frissitesek optimalizalasainak tesztjei."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from tudasjargany.app import TudasJarganyGame


class GuiPerformanceTests(unittest.TestCase):
    def test_compact_layout_shortens_controls_and_wraps_status(self) -> None:
        header_text = Mock()
        header_text.winfo_manager.return_value = "pack"
        game = SimpleNamespace(
            layout_job="pending",
            winfo_width=lambda: 900,
            header_text=header_text,
            auto_button=Mock(),
            settings_button=Mock(),
            back_button=Mock(),
            start_button=Mock(),
            status=Mock(),
        )

        TudasJarganyGame._apply_responsive_layout(game)

        header_text.pack_forget.assert_called_once()
        game.auto_button.configure.assert_called_once_with(
            text="✨  ÖSSZERAKÁS", padx=10
        )
        self.assertGreater(
            game.status.configure.call_args.kwargs["wraplength"], 0
        )

    def test_wide_layout_restores_header_subtitle(self) -> None:
        header_text = Mock()
        header_text.winfo_manager.return_value = ""
        game = SimpleNamespace(
            layout_job=None,
            winfo_width=lambda: 1200,
            header_text=header_text,
            auto_button=Mock(),
            settings_button=Mock(),
            back_button=Mock(),
            start_button=Mock(),
            status=Mock(),
        )

        TudasJarganyGame._apply_responsive_layout(game)

        header_text.pack.assert_called_once_with(side="left", padx=(22, 0))
        game.auto_button.configure.assert_called_once_with(
            text="✨  KÖTELEZŐK ÖSSZERAKÁSA", padx=18
        )

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
