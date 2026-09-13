import random
import re
import unittest

from math_tasks import MathTaskGenerator


class MathTaskTests(unittest.TestCase):
    def test_answer_is_always_among_choices(self):
        generator = MathTaskGenerator(random.Random(12))
        for _ in range(200):
            task = generator.next_task()
            self.assertIn(task.answer, task.choices)

    def test_no_immediate_repetition(self):
        generator = MathTaskGenerator(random.Random(8))
        prompts = [generator.next_task().prompt for _ in range(100)]
        self.assertTrue(all(first != second for first, second in zip(prompts, prompts[1:])))

    def test_numbers_stay_in_thirty_range(self):
        generator = MathTaskGenerator(random.Random(20))
        saw_number_over_twenty = False
        for _ in range(300):
            task = generator.next_task()
            prompt_numbers = [int(value) for value in re.findall(r"\d+", task.prompt)]
            self.assertTrue(all(0 <= value <= 30 for value in prompt_numbers))
            saw_number_over_twenty |= any(value > 20 for value in prompt_numbers)
            for choice in task.choices:
                if choice not in ("+", "−"):
                    self.assertGreaterEqual(int(choice), 0)
                    self.assertLessEqual(int(choice), 30)
        self.assertTrue(saw_number_over_twenty)


if __name__ == "__main__":
    unittest.main()
