"""A játék Tkintertől független, módosítható állapota."""

from dataclasses import dataclass
from enum import StrEnum


class GameMode(StrEnum):
    """A választható játékmódok belső azonosítói."""

    CAR = "car"
    HELICOPTER = "helicopter"
    UNICORN = "unicorn"


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
