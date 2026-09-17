import random
import unittest

from tudasjargany.legacy.wordsearch import WordSearch, cells_on_line


class LineTests(unittest.TestCase):
    def test_horizontal(self):
        self.assertEqual(cells_on_line((2, 1), (2, 4)), [(2, 1), (2, 2), (2, 3), (2, 4)])

    def test_reverse_diagonal(self):
        self.assertEqual(cells_on_line((3, 3), (1, 1)), [(3, 3), (2, 2), (1, 1)])

    def test_invalid_line(self):
        self.assertEqual(cells_on_line((0, 0), (2, 3)), [])


class GenerationTests(unittest.TestCase):
    def test_every_word_is_present_and_selectable_both_ways(self):
        words = ["AUTÓ", "BUSZ", "VONAT", "HAJÓ", "BICIKLI", "MOTOR", "TAXI", "REPÜLŐ"]
        game = WordSearch(words, size=11, rng=random.Random(42))
        for word in words:
            placement = game.placements[word]
            letters = "".join(game.grid[r][c] for r, c in placement.cells)
            self.assertEqual(letters, word)
            self.assertEqual(game.word_at(list(placement.cells)), word)
            self.assertEqual(game.word_at(list(reversed(placement.cells))), word)


if __name__ == "__main__":
    unittest.main()
