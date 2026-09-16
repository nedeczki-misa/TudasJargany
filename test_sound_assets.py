import unittest

from tudasjargany.app import SOUND_FILES


class SoundAssetTests(unittest.TestCase):
    def test_every_referenced_sound_file_is_present(self) -> None:
        expected = {
            "engine_start", "speed_up", "brake_screech", "collision_light",
            "collision_heavy", "bonus_success", "horn", "siren_loop", "star_pickup",
        }
        self.assertEqual(set(SOUND_FILES), expected)
        for sound_file in SOUND_FILES.values():
            self.assertTrue(sound_file.is_file(), sound_file)
            self.assertEqual(sound_file.suffix.lower(), ".wav")


if __name__ == "__main__":
    unittest.main()