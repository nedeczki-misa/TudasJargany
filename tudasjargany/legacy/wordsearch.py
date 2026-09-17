"""A szókereső játékmenetének felülettől független része."""

from __future__ import annotations

import random
import unicodedata
from dataclasses import dataclass


DIRECTIONS = (
    (0, 1),    # jobbra
    (1, 0),    # lefelé
    (1, 1),    # átlósan jobbra-le
    (1, -1),   # átlósan balra-le
    (0, -1),   # balra
    (-1, 0),   # felfelé
    (-1, -1),  # átlósan balra-fel
    (-1, 1),   # átlósan jobbra-fel
)

FILLER_LETTERS = "AÁBCDEÉFGHIÍJKLMNOÓÖŐPRSTUÚÜŰVZ"


def normalized(text: str) -> str:
    """Összehasonlítható alak, az ékezeteket megtartva."""
    return unicodedata.normalize("NFC", text).upper().replace(" ", "")


@dataclass(frozen=True)
class PlacedWord:
    word: str
    cells: tuple[tuple[int, int], ...]


class WordSearch:
    """Véletlenszerű, garantáltan megoldható szókereső tábla."""

    def __init__(
        self,
        words: list[str],
        size: int = 11,
        rng: random.Random | None = None,
    ) -> None:
        self.words = [normalized(word) for word in words]
        self.size = size
        self.rng = rng or random.Random()
        if not self.words or max(map(len, self.words)) > size:
            raise ValueError("A szavaknak el kell férniük a táblán.")
        self.grid: list[list[str]] = []
        self.placements: dict[str, PlacedWord] = {}
        self.generate()

    def generate(self) -> None:
        """Új táblát készít; sikertelenség esetén tiszta tábláról újrakezdi."""
        for _ in range(100):
            grid = [["" for _ in range(self.size)] for _ in range(self.size)]
            placements: dict[str, PlacedWord] = {}

            # A hosszabb szavak kerüljenek be először, mert ezeket nehezebb elhelyezni.
            ordered = sorted(self.words, key=len, reverse=True)
            if all(self._place_word(word, grid, placements) for word in ordered):
                for row in range(self.size):
                    for col in range(self.size):
                        if not grid[row][col]:
                            grid[row][col] = self.rng.choice(FILLER_LETTERS)
                self.grid = grid
                self.placements = placements
                return
        raise RuntimeError("Nem sikerült szókeresőt készíteni.")

    def _place_word(
        self,
        word: str,
        grid: list[list[str]],
        placements: dict[str, PlacedWord],
    ) -> bool:
        candidates: list[tuple[tuple[int, int], ...]] = []
        for dr, dc in DIRECTIONS:
            for row in range(self.size):
                for col in range(self.size):
                    cells = tuple(
                        (row + i * dr, col + i * dc) for i in range(len(word))
                    )
                    if not all(
                        0 <= r < self.size and 0 <= c < self.size for r, c in cells
                    ):
                        continue
                    if all(
                        not grid[r][c] or grid[r][c] == letter
                        for (r, c), letter in zip(cells, word)
                    ):
                        candidates.append(cells)

        if not candidates:
            return False

        cells = self.rng.choice(candidates)
        for (row, col), letter in zip(cells, word):
            grid[row][col] = letter
        placements[word] = PlacedWord(word, cells)
        return True

    def word_at(self, cells: list[tuple[int, int]]) -> str | None:
        """Visszaadja a kijelölés szavát, mindkét olvasási irányt elfogadva."""
        chosen = tuple(cells)
        for word, placement in self.placements.items():
            if chosen == placement.cells or chosen == placement.cells[::-1]:
                return word
        return None


def cells_on_line(
    start: tuple[int, int], end: tuple[int, int]
) -> list[tuple[int, int]]:
    """A két cella közötti vízszintes, függőleges vagy átlós cellák."""
    r1, c1 = start
    r2, c2 = end
    row_delta, col_delta = r2 - r1, c2 - c1
    if row_delta == 0 and col_delta == 0:
        return [start]
    if row_delta and col_delta and abs(row_delta) != abs(col_delta):
        return []
    if not (row_delta == 0 or col_delta == 0 or abs(row_delta) == abs(col_delta)):
        return []
    dr = (row_delta > 0) - (row_delta < 0)
    dc = (col_delta > 0) - (col_delta < 0)
    length = max(abs(row_delta), abs(col_delta))
    return [(r1 + i * dr, c1 + i * dc) for i in range(length + 1)]
