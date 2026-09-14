"""Változatos, 30-as számkörbe tartozó matematikai feladatok."""

from __future__ import annotations

import random
from learning_tasks import LearningTask
from collections import deque


MAX_NUMBER = 30

# Visszafele kompatibilis nev a korabbi tesztekhez es hivasokhoz.
MathTask = LearningTask


class MathTaskGenerator:
    """Összeadásos és kivonásos feladatokat készít ismétlés nélkül."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.recent_prompts: deque[str] = deque(maxlen=12)

    def next_task(self) -> MathTask:
        for _ in range(100):
            task_type = self.rng.choice(("result", "left", "right", "operator"))
            task = getattr(self, f"_{task_type}")()
            if task.prompt not in self.recent_prompts:
                self.recent_prompts.append(task.prompt)
                return task
        # Gyakorlatilag nem érhető el, de véges marad a keresés.
        self.recent_prompts.append(task.prompt)
        return task

    def _result(self) -> MathTask:
        operation = self.rng.choice(("+", "−"))
        if operation == "+":
            left = self.rng.randint(0, MAX_NUMBER - 1)
            right = self.rng.randint(1, MAX_NUMBER - left)
            result = left + right
        else:
            left = self.rng.randint(1, MAX_NUMBER)
            right = self.rng.randint(0, left)
            result = left - right
        prompt = f"{left} {operation} {right} = ?"
        return self._number_task(prompt, result, f"{left} {operation} {right} = {result}")

    def _left(self) -> MathTask:
        operation = self.rng.choice(("+", "−"))
        if operation == "+":
            answer = self.rng.randint(0, MAX_NUMBER - 1)
            right = self.rng.randint(1, MAX_NUMBER - answer)
            result = answer + right
        else:
            right = self.rng.randint(0, MAX_NUMBER - 1)
            result = self.rng.randint(0, MAX_NUMBER - right)
            answer = result + right
        prompt = f"? {operation} {right} = {result}"
        return self._number_task(prompt, answer, f"{answer} {operation} {right} = {result}")

    def _right(self) -> MathTask:
        operation = self.rng.choice(("+", "−"))
        if operation == "+":
            left = self.rng.randint(0, MAX_NUMBER - 1)
            answer = self.rng.randint(1, MAX_NUMBER - left)
            result = left + answer
        else:
            left = self.rng.randint(1, MAX_NUMBER)
            answer = self.rng.randint(0, left)
            result = left - answer
        prompt = f"{left} {operation} ? = {result}"
        return self._number_task(prompt, answer, f"{left} {operation} {answer} = {result}")

    def _operator(self) -> MathTask:
        operation = self.rng.choice(("+", "−"))
        right = self.rng.randint(1, 15)
        if operation == "+":
            left = self.rng.randint(0, MAX_NUMBER - right)
            result = left + right
        else:
            left = self.rng.randint(right, MAX_NUMBER)
            result = left - right
        choices = ["+", "−"]
        self.rng.shuffle(choices)
        return MathTask(
            prompt=f"{left}  ?  {right} = {result}",
            answer=operation,
            choices=tuple(choices),
            explanation=f"A hiányzó jel: {operation}",
        )

    def _number_task(self, prompt: str, answer: int, explanation: str) -> MathTask:
        candidates = {answer}
        offsets = [-3, -2, -1, 1, 2, 3]
        self.rng.shuffle(offsets)
        for offset in offsets:
            candidate = answer + offset
            if 0 <= candidate <= MAX_NUMBER:
                candidates.add(candidate)
            if len(candidates) == 3:
                break
        while len(candidates) < 3:
            candidates.add(self.rng.randint(0, MAX_NUMBER))
        choices = [str(number) for number in candidates]
        self.rng.shuffle(choices)
        return MathTask(prompt, str(answer), tuple(choices), explanation)
