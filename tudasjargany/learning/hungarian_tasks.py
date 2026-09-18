"""Magyar ábécérend-gyakorlás második osztályosoknak."""

from __future__ import annotations

import random
from collections import deque

from .tasks import LearningTask


HUNGARIAN_ALPHABET = (
    "A", "Á", "B", "C", "CS", "D", "DZ", "DZS", "E", "É", "F", "G", "GY",
    "H", "I", "Í", "J", "K", "L", "LY", "M", "N", "NY", "O", "Ó", "Ö", "Ő",
    "P", "Q", "R", "S", "SZ", "T", "TY", "U", "Ú", "Ü", "Ű", "V", "W", "X",
    "Y", "Z", "ZS",
)


class HungarianAlphabetTaskGenerator:
    """Három egymást követő betűből egy hiányzik, ezt kell begépelni."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.recent_prompts: deque[str] = deque(maxlen=12)

    def next_task(self) -> LearningTask:
        for _ in range(100):
            start = self.rng.randrange(len(HUNGARIAN_ALPHABET) - 2)
            letters = HUNGARIAN_ALPHABET[start:start + 3]
            missing_index = self.rng.randrange(3)
            answer = letters[missing_index]
            shown = list(letters)
            shown[missing_index] = "?"
            sequence = "   ".join(shown)
            prompt = f"{sequence}\nMelyik betű hiányzik?"
            if prompt not in self.recent_prompts:
                self.recent_prompts.append(prompt)
                return LearningTask(
                    prompt=prompt,
                    answer=answer,
                    choices=(),
                    explanation=f"A helyes betű: {answer}.",
                    subject="MAGYAR",
                    requires_keyboard_input=True,
                )
        self.recent_prompts.append(prompt)
        return LearningTask(
            prompt=prompt,
            answer=answer,
            choices=(),
            explanation=f"A helyes betű: {answer}.",
            subject="MAGYAR",
            requires_keyboard_input=True,
        )