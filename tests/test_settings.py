import tempfile
import unittest
from pathlib import Path

from tudasjargany.services.settings import DEFAULT_SUBJECTS, load_enabled_subjects, save_enabled_subjects


class SettingsTests(unittest.TestCase):
    AVAILABLE = ("MATEK", "ANGOL", "MAGYAR")

    def test_missing_or_bad_settings_use_math_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "beallitasok.json"
            self.assertEqual(load_enabled_subjects(self.AVAILABLE, path), DEFAULT_SUBJECTS)
            path.write_text("not json", encoding="utf-8")
            self.assertEqual(load_enabled_subjects(self.AVAILABLE, path), DEFAULT_SUBJECTS)

    def test_saved_subjects_are_loaded_in_available_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "beallitasok.json"
            save_enabled_subjects(("MAGYAR", "MATEK"), path)
            self.assertEqual(load_enabled_subjects(self.AVAILABLE, path), ("MATEK", "MAGYAR"))

    def test_unknown_or_empty_subjects_fall_back_to_math(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "beallitasok.json"
            path.write_text('{"enabled_subjects": ["NINCS"]}', encoding="utf-8")
            self.assertEqual(load_enabled_subjects(self.AVAILABLE, path), DEFAULT_SUBJECTS)


if __name__ == "__main__":
    unittest.main()