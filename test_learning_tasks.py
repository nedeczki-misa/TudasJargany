import random
import unittest

from learning_tasks import EnglishTaskGenerator
from math_tasks import MathTaskGenerator
from task_manager import TaskManager


class EnglishTaskTests(unittest.TestCase):
    def test_answer_is_always_among_choices(self) -> None:
        generator = EnglishTaskGenerator(random.Random(31))
        for _ in range(30):
            task = generator.next_task()
            self.assertEqual(task.subject, "ANGOL")
            self.assertIn(task.answer, task.choices)
            self.assertEqual(len(task.choices), 3)
            self.assertEqual(len(set(task.choices)), 3)
            self.assertIsNotNone(task.pronunciation)
            if task.choices_in_english:
                self.assertIn(task.pronunciation, task.choices)
            else:
                self.assertIn(task.pronunciation, task.prompt)

    def test_no_immediate_repetition(self) -> None:
        generator = EnglishTaskGenerator(random.Random(7))
        first = generator.next_task()
        second = generator.next_task()
        self.assertNotEqual(first.prompt, second.prompt)


class TaskManagerTests(unittest.TestCase):
    def test_tasks_strictly_alternate_between_math_and_english(self) -> None:
        manager = TaskManager(
            MathTaskGenerator(random.Random(3)),
            EnglishTaskGenerator(random.Random(4)),
        )
        subjects = [manager.next_task().subject for _ in range(8)]
        self.assertEqual(subjects, ["MATEK", "ANGOL"] * 4)


if __name__ == "__main__":
    unittest.main()