"""Kozos feladatmodell es angol szokincs-gyakorlas."""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class LearningTask:
    """Egy kattinthato, tananyaghoz kotott feladat."""

    prompt: str
    answer: str
    choices: tuple[str, ...]
    explanation: str
    subject: str = "MATEK"
    pronunciation: str | None = None
    choices_in_english: bool = False
    requires_keyboard_input: bool = False


class EnglishTaskGenerator:
    """Masodik osztalyos, alap angol-magyar szokincsfeladatokat keszit."""

    VOCABULARY = (
        ("alma", "apple"), ("macska", "cat"), ("kutya", "dog"),
        ("aut\u00f3", "car"), ("h\u00e1z", "house"), ("k\u00f6nyv", "book"),
        ("nap", "sun"), ("v\u00edz", "water"), ("piros", "red"),
        ("k\u00e9k", "blue"), ("z\u00f6ld", "green"), ("s\u00e1rga", "yellow"),
    )

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.recent_prompts: deque[str] = deque(maxlen=12)

    def next_task(self) -> LearningTask:
        for _ in range(100):
            hungarian, english = self.rng.choice(self.VOCABULARY)
            if self.rng.choice((True, False)):
                prompt = f"V\u00e1laszd ki angolul: {hungarian}!"
                answer = english
                candidates = [word for _, word in self.VOCABULARY if word != answer]
                explanation = f"{hungarian.capitalize()} angolul: {english}."
                choices_in_english = True
            else:
                prompt = f"Mit jelent magyarul: {english}?"
                answer = hungarian
                candidates = [word for word, _ in self.VOCABULARY if word != answer]
                explanation = f"{english.capitalize()} magyarul: {hungarian}."
                choices_in_english = False
            if prompt not in self.recent_prompts:
                self.recent_prompts.append(prompt)
                choices = [answer, *self.rng.sample(candidates, 2)]
                self.rng.shuffle(choices)
                return LearningTask(
                    prompt=prompt,
                    answer=answer,
                    choices=tuple(choices),
                    explanation=explanation,
                    subject="ANGOL",
                    pronunciation=english,
                    choices_in_english=choices_in_english,
                )
        # Veges marad a kereses akkor is, ha minden kozelmuli kerdes elfogyott.
        self.recent_prompts.append(prompt)
        choices = [answer, *self.rng.sample(candidates, 2)]
        self.rng.shuffle(choices)
        return LearningTask(prompt, answer, tuple(choices), explanation, "ANGOL", english, choices_in_english)