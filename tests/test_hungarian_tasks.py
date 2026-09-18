import random
import unittest

from tudasjargany.learning.hungarian_tasks import HUNGARIAN_ALPHABET, HungarianAlphabetTaskGenerator
from tudasjargany.learning.manager import TaskManager


class HungarianAlphabetTaskTests(unittest.TestCase):
    def test_missing_letter_is_one_of_three_consecutive_hungarian_letters(self) -> None:
        generator = HungarianAlphabetTaskGenerator(random.Random(42))
        for _ in range(150):
            task = generator.next_task()
            shown = task.prompt.splitlines()[0].split()
            self.assertEqual(task.subject, "MAGYAR")
            self.assertTrue(task.requires_keyboard_input)
            self.assertEqual(task.choices, ())
            self.assertEqual(len(shown), 3)
            self.assertEqual(shown.count("?"), 1)
            missing_index = shown.index("?")
            for start in range(len(HUNGARIAN_ALPHABET) - 2):
                expected = list(HUNGARIAN_ALPHABET[start:start + 3])
                expected[missing_index] = "?"
                if expected == shown:
                    self.assertEqual(task.answer, HUNGARIAN_ALPHABET[start + missing_index])
                    break
            else:
                self.fail(f"Nem egymást követő ábécébetűk: {shown}")

    def test_no_immediate_prompt_repetition(self) -> None:
        generator = HungarianAlphabetTaskGenerator(random.Random(9))
        prompts = [generator.next_task().prompt for _ in range(60)]
        self.assertTrue(all(first != second for first, second in zip(prompts, prompts[1:])))

    def test_task_manager_can_select_hungarian_only(self) -> None:
        manager = TaskManager(enabled_subjects=("MAGYAR",))
        self.assertEqual([manager.next_task().subject for _ in range(5)], ["MAGYAR"] * 5)


if __name__ == "__main__":
    unittest.main()