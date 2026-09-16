"""A főalkalmazásból kiemelt, önálló felelősségű műveletek."""

from __future__ import annotations

import math
import random
import threading
import tkinter as tk
from pathlib import Path

from .speech import EnglishSpeaker

try:
    import winsound
except ImportError:
    winsound = None

SOUND_DIR = Path(__file__).parents[2] / "assets" / "sounds"
SOUND_FILES = {
    "engine_start": SOUND_DIR / "engine_start.wav",
    "speed_up": SOUND_DIR / "speed_up.wav",
    "brake_screech": SOUND_DIR / "brake_screech.wav",
    "collision_light": SOUND_DIR / "collision_light.wav",
    "collision_heavy": SOUND_DIR / "collision_heavy.wav",
    "bonus_success": SOUND_DIR / "bonus_success.wav",
    "horn": SOUND_DIR / "horn.wav",
    "siren_loop": SOUND_DIR / "siren_loop.wav",
    "star_pickup": SOUND_DIR / "star_pickup_retro.wav",
}

class AudioServiceMixin:

    def _play_tones(self, tones: tuple[tuple[int, int], ...]) -> None:
            """Tartalek hangjelzes, ha egy hangfajl nem erheto el."""
            if winsound is None:
                self.bell()
                return

            def play() -> None:
                try:
                    for frequency, duration in tones:
                        winsound.Beep(frequency, duration)
                except RuntimeError:
                    winsound.MessageBeep()

            threading.Thread(target=play, daemon=True).start()

    def _play_sound_effect(self, name: str) -> None:
            sound_file = SOUND_FILES[name]
            if winsound is not None and sound_file.is_file():
                restart_siren = self.siren_running
                self.siren_running = False
                winsound.PlaySound(str(sound_file), winsound.SND_FILENAME | winsound.SND_ASYNC)
                if restart_siren:
                    self.after(900, self._start_siren_loop)
                return
            fallback = {
                "speed_up": ((523, 70), (659, 70), (784, 120)),
                "collision_light": ((330, 100), (220, 180)),
                "collision_heavy": ((280, 130), (180, 210)),
                "bonus_success": ((659, 80), (784, 140)),
            }
            self._play_tones(fallback.get(name, ((523, 100),)))

    def _play_collision_sound(self, obstacle_kind: str) -> None:
            if obstacle_kind in ("cloud", "bird", "plane"):
                self._play_sound_effect("collision_light")
                return
            self._play_sound_effect("brake_screech")
            impact = "collision_light" if obstacle_kind == "cone" else "collision_heavy"
            self.after(170, lambda: self._play_sound_effect(impact))

    def _play_speed_up_sound(self) -> None:
            self._play_sound_effect("speed_up")

    def _honk(self) -> None:
            if self.mode == "drive" and not self.math_active and not self._is_helicopter_mode():
                self._play_sound_effect("horn")

    def _start_siren_loop(self) -> None:
            has_siren = any(part.kind == "siren" and part.placed for part in self.parts)
            sound_file = SOUND_FILES["siren_loop"]
            if self.mode == "drive" and not self._is_helicopter_mode() and not self.math_active and has_siren and winsound is not None and sound_file.is_file():
                winsound.PlaySound(str(sound_file), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
                self.siren_running = True

    def _stop_siren(self) -> None:
            if self.siren_running and winsound is not None:
                winsound.PlaySound(None, 0)
            self.siren_running = False

    def _speak_english_word(self, word: str | None) -> None:
            if word:
                self.english_speaker.speak(word)
