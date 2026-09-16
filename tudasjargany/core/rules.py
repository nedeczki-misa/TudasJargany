"""Pontozási, mérföldkő- és ütközési szabályok Tkinter nélkül."""

from dataclasses import dataclass

BASE_ROAD_SPEED = 6.5
SPEED_STEP = 1.6
MAX_LIVES = 3


@dataclass(frozen=True)
class ScoreChange:
    """Egy pontváltozás összes következménye."""

    score: int
    speed_level: int
    bonus_challenges: int = 0
    life_challenges: int = 0
    coloring_challenges: int = 0

    @property
    def sped_up(self) -> bool:
        return self.speed_level > 0


def road_speed(speed_level: int) -> float:
    return BASE_ROAD_SPEED + max(0, speed_level) * SPEED_STEP


def add_stars(score: int, speed_level: int, amount: int, *, unicorn: bool = False) -> ScoreChange:
    """Kiszámítja a csillagok és az átlépett tízes mérföldkövek hatását."""
    if amount < 0:
        raise ValueError("A csillagok száma nem lehet negatív.")
    new_score = score + amount
    milestones = range((score // 10 + 1) * 10, new_score + 1, 10)
    if unicorn:
        return ScoreChange(new_score, speed_level, coloring_challenges=len(tuple(milestones)))

    milestone_values = tuple(milestones)
    return ScoreChange(
        new_score,
        speed_level + len(milestone_values),
        bonus_challenges=sum(value % 30 != 0 for value in milestone_values),
        life_challenges=sum(value % 30 == 0 for value in milestone_values),
    )


def collision_speed_level(speed_level: int) -> int:
    """Ütközéskor pontosan egy fokozattal lassít, de nulla alá nem megy."""
    return max(0, speed_level - 1)


def lose_life(lives: int) -> int:
    return max(0, lives - 1)


def restore_life(lives: int) -> int:
    return min(MAX_LIVES, lives + 1)
