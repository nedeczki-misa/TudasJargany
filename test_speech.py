import base64
import unittest

from tudasjargany.services.audio import EnglishSpeaker


class EnglishSpeakerTests(unittest.TestCase):
    def test_command_uses_windows_speech_and_keeps_word_as_data(self) -> None:
        speaker = EnglishSpeaker()
        command = speaker._command_for("apple; ignored")
        script = base64.b64decode(command[-1]).decode("utf-16le")
        self.assertIn("System.Speech", script)
        self.assertIn("en-*", script)
        self.assertNotIn("apple; ignored", script)
        self.assertIn("YXBwbGU7IGlnbm9yZWQ=", script)


if __name__ == "__main__":
    unittest.main()