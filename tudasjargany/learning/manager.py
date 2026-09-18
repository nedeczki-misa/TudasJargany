"""A kulonbozo tantargyi feladatforrasok valtasat kezeli."""

from __future__ import annotations

from .tasks import EnglishTaskGenerator, LearningTask
from .math_tasks import MathTaskGenerator
from .hungarian_tasks import HungarianAlphabetTaskGenerator


class TaskManager:
    """Felvaltva ad matek- es angolfeladatot; uj targy itt bovitheto."""

    AVAILABLE_SUBJECTS = ("MATEK", "ANGOL", "MAGYAR")

    def __init__(
        self,
        math_generator: MathTaskGenerator | None = None,
        english_generator: EnglishTaskGenerator | None = None,
        enabled_subjects: tuple[str, ...] = ("MATEK",),
        hungarian_generator: HungarianAlphabetTaskGenerator | None = None,
    ) -> None:
        self.generators = {
            "MATEK": math_generator or MathTaskGenerator(),
            "ANGOL": english_generator or EnglishTaskGenerator(),
            "MAGYAR": hungarian_generator or HungarianAlphabetTaskGenerator(),
        }
        self.enabled_subjects: tuple[str, ...] = ()
        self.next_subject_index = 0
        self.set_enabled_subjects(enabled_subjects)

    def set_enabled_subjects(self, subjects: tuple[str, ...]) -> None:
        selected = tuple(subject for subject in self.AVAILABLE_SUBJECTS if subject in subjects)
        if not selected:
            raise ValueError("Legalább egy tantárgyat ki kell választani.")
        self.enabled_subjects = selected
        self.next_subject_index = 0

    def next_task(self) -> LearningTask:
        subject = self.enabled_subjects[self.next_subject_index]
        self.next_subject_index = (self.next_subject_index + 1) % len(self.enabled_subjects)
        return self.generators[subject].next_task()