"""A játék Tkintertől független, módosítható állapota."""

from dataclasses import dataclass
from enum import Enum


class GameMode(str, Enum):
    """A választható játékmódok Python 3.9-cel is használható azonosítói.

    A ``StrEnum`` csak Python 3.11-ben jelent meg. A ``str`` és ``Enum``
    együttes öröklése ugyanazt a szöveges összehasonlíthatóságot biztosítja
    a játék által támogatott régebbi Python-verziókon is.
    """

    CAR = "car"
    HELICOPTER = "helicopter"
    UNICORN = "unicorn"

    def __str__(self) -> str:
        """A ``StrEnum`` viselkedéséhez hasonlóan az értéket adja vissza."""
        return self.value


@dataclass
class GameState:
    """A menet közben változó, felülettől független értékek."""

    score: int = 0
    lives: int = 3
    speed_level: int = 0
    mode: GameMode = GameMode.CAR

    def reset(self, mode: GameMode | None = None) -> None:
        """Új menet alapértékeire állítja az állapotot."""
        self.score = 0
        self.lives = 3
        self.speed_level = 0
        if mode is not None:
            self.mode = mode
