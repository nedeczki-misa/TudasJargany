"""A kulonbozo tantargyi feladatforrasok valtasat kezeli."""

from __future__ import annotations

from learning_tasks import EnglishTaskGenerator, LearningTask
from math_tasks import MathTaskGenerator


class TaskManager:
    """Felvaltva ad matek- es angolfeladatot; uj targy itt bovitheto."""

    SUBJECTS = ("MATEK", "ANGOL")

    def __init__(
        self,
        math_generator: MathTaskGenerator | None = None,
        english_generator: EnglishTaskGenerator | None = None,
    ) -> None:
        self.generators = {
            "MATEK": math_generator or MathTaskGenerator(),
            "ANGOL": english_generator or EnglishTaskGenerator(),
        }
        self.next_subject_index = 0

    def next_task(self) -> LearningTask:
        subject = self.SUBJECTS[self.next_subject_index]
        self.next_subject_index = (self.next_subject_index + 1) % len(self.SUBJECTS)
        return self.generators[subject].next_task()