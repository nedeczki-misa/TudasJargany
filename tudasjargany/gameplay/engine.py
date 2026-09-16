"""A főalkalmazásból kiemelt, önálló felelősségű műveletek."""

from __future__ import annotations

import math
import random
import threading
import tkinter as tk
from tudasjargany.app import INK
from tudasjargany.core.rules import add_stars, collision_speed_level, road_speed

class GameplayEngineMixin:

    def _road_edges(self) -> tuple[float, float]:
            width = self.canvas_width
            if width <= 1:
                width = self.canvas.winfo_width()
            road_width = min(690, width - 170)
            return (width - road_width) / 2, (width + road_width) / 2

    def _lane_x(self, lane: int) -> float:
            left, right = self._road_edges()
            return left + (right - left) / 4 * (lane + 0.5)

    def _change_lane(self, direction: int) -> None:
            if self.mode == "drive":
                old_lane = self.lane
                self.lane = max(0, min(3, self.lane + direction))
                if old_lane != self.lane:
                    self.message, self.message_frames = "HOPP!", 12

    def _update_drive_status(self) -> None:
            if self._is_unicorn_mode():
                status = (f"⭐  {self.score}", "#C75DCE", 20)
                if status != self.last_drive_status:
                    self.status.configure(
                        text=status[0], font=("Arial", status[2], "bold"), fg=status[1]
                    )
                    self.last_drive_status = status
                return
            hearts = "♥" * self.lives + "♡" * (3 - self.lives)
            vehicle_status = "Magasság: {0}. szint".format(self.speed_level + 1) if self._is_helicopter_mode() else "Sebesség: {0}. fokozat".format(self.speed_level + 1)
            status = (f"★ {self.score}     |     {hearts}     |     {vehicle_status}", INK, 12)
            # A Label ujrakonfiguralasa meretezesi munkat indit a Tk-ben. Pontszam,
            # elet vagy sebesseg valtozasa nelkul nincs mit frissiteni minden kepen.
            if status != self.last_drive_status:
                self.status.configure(
                    text=status[0], font=("Arial", status[2], "bold"), fg=status[1]
                )
                self.last_drive_status = status

    def _add_stars(self, amount: int) -> bool:
        """Hozzáadja a jutalmat, és kezeli a 10 csillagos mérföldköveket."""
        old_score = self.score
        change = add_stars(
            old_score, getattr(self, "speed_level", 0), amount,
            unicorn=self._is_unicorn_mode(),
        )
        self.score = change.score
        if self._is_unicorn_mode():
            self.pending_coloring_challenges += change.coloring_challenges
            if change.coloring_challenges:
                self.message, self.message_frames = "🎨", 45
            self._update_drive_status()
            return bool(change.coloring_challenges)
        crossed = change.speed_level - self.speed_level
        self.pending_bonus_challenges += change.bonus_challenges
        self.pending_life_challenges += change.life_challenges
        self.speed_level = change.speed_level
        self.road_speed = road_speed(self.speed_level)
        if crossed:
            last_milestone = (self.score // 10) * 10
            if last_milestone % 30 == 0:
                self.message = f"{last_milestone} PONT! ÉLETBÓNUSZ-FELADAT!"
            else:
                self.message = f"{last_milestone} PONT! SEBESSÉGVÁLTÁS!"
            self.message_frames = 45
            self.speed_just_increased = True
            self._play_speed_up_sound()
        self._update_drive_status()
        return bool(crossed)

    def _slow_down_after_collision(self, obstacle_kind: str) -> None:
            self._play_collision_sound(obstacle_kind)
            self.speed_just_increased = False
            old_level = self.speed_level
            self.speed_level = collision_speed_level(self.speed_level)
            self.road_speed = road_speed(self.speed_level)
            if self.speed_level < old_level:
                self.message = "ÜTKÖZÉS – EGY SEBESSÉGGEL LASSABB!"
            else:
                self.message = "ÜTKÖZÉS – MARAD AZ ALAPSEBESSÉG!"
            self.message_frames = 45
            self._update_drive_status()

    def _random_road_kind(helicopter: bool = False, unicorn: bool = False) -> str:
            if unicorn:
                return "unicorn_star"
            roll = random.random()
            if helicopter:
                if roll < 0.58:
                    return "star"
                if roll < 0.80:
                    return "cloud"
                if roll < 0.92:
                    return "bird"
                return "plane"
            if roll < 0.50:
                return "star"
            if roll < 0.65:
                return "cone"
            if roll < 0.76:
                return "motorcycle"
            if roll < 0.86:
                return "car"
            if roll < 0.93:
                return "bus"
            if roll < 0.96:
                return "asphalt_paver"
            if roll < 0.98:
                return "dumper"
            return "closure"

    def _dumper_dirt_pile(lane: int) -> dict[str, float | int | str]:
            """A dömper után egy földkupac marad ugyanabban a sávban."""
            return {"kind": "dirt_pile", "lane": lane, "y": -150.0}

    def _move_wild_motorcycle(item: dict[str, float | int | str]) -> None:
            """A motoros sávok közt cikázik, de nem hagyhatja el az utat."""
            lane_position = float(item.get("lane_position", item["lane"]))
            direction = float(item.get("lane_direction", 1.0))
            if random.random() < 0.075:
                direction *= -1
            lane_position += direction * 0.095
            if lane_position <= 0:
                lane_position, direction = 0.0, 1.0
            elif lane_position >= 3:
                lane_position, direction = 3.0, -1.0
            item["lane_position"] = lane_position
            item["lane_direction"] = direction
            item["lane"] = int(round(lane_position))

    def _drive_tick(self) -> None:
            if self.mode != "drive" or self.math_active or self.coloring_active:
                return
            self.frame += 1
            spawn_interval = 32 if self._is_unicorn_mode() else 48
            if self.frame % spawn_interval == 0:
                occupied = {int(item["lane"]) for item in self.road_items if float(item["y"]) < 120}
                free_lanes = [lane for lane in range(4) if lane not in occupied] or [0, 1, 2, 3]
                kind = self._random_road_kind(self._is_helicopter_mode(), self._is_unicorn_mode())
                lane = random.choice(free_lanes)
                item: dict[str, float | int | str] = {"kind": kind, "lane": lane, "y": -45.0}
                if kind == "motorcycle":
                    item["lane_position"] = float(lane)
                    item["lane_direction"] = random.choice((-1.0, 1.0))
                self.road_items.append(item)
                if kind == "dumper":
                    self.road_items.append(self._dumper_dirt_pile(lane))

            height = self.canvas_height if self.canvas_height > 1 else self.canvas.winfo_height()
            car_y = height - 128
            survivors = []
            hit_obstacle: str | None = None
            for item in self.road_items:
                item["y"] = float(item["y"]) + self.road_speed
                if item["kind"] == "motorcycle":
                    self._move_wild_motorcycle(item)
                collision_distance = 72 if item["kind"] in ("closure", "asphalt_paver", "dumper") else 54
                if (
                    hit_obstacle is None
                    and abs(float(item.get("lane_position", item["lane"])) - self.lane) < 0.43
                    and abs(float(item["y"]) - car_y) < collision_distance
                ):
                    if item["kind"] in ("star", "unicorn_star"):
                        self._play_sound_effect("star_pickup")
                        sped_up = self._add_stars(1)
                        if not sped_up:
                            self.message, self.message_frames = "+1 CSILLAG!", 25
                        else:
                            # A gyorsulási üzenetet itt rögtön megjelenítjük.
                            self.speed_just_increased = False
                    else:
                        hit_obstacle = str(item["kind"])
                        self._slow_down_after_collision(hit_obstacle)
                    continue
                if float(item["y"]) < height + 60:
                    survivors.append(item)
            self.road_items = survivors
            if self.message_frames:
                self.message_frames -= 1

            self._update_drive_status()
            self._draw_road()
            if self._is_unicorn_mode() and self.pending_coloring_challenges:
                self._start_coloring_challenge(delay=180)
            elif hit_obstacle:
                obstacle_names = {
                    "cone": "A bója megállított.",
                    "car": "Összekoccantál egy másik autóval.",
                    "motorcycle": "Egy vadmotoros eléd cikázott!",
                    "bus": "Túl közel kerültél a buszhoz.",
                    "asphalt_paver": "Az aszfaltozó gép elállta az utat!",
                    "dumper": "A dömper útjába kerültél!",
                    "dirt_pile": "A földkupacba hajtottál!",
                    "closure": "Behajtottál a lezárt sávba!",
                    "cloud": "Egy viharfelhőbe repültél!",
                    "bird": "Egy madár eléd repült!",
                    "plane": "Egy repülő keresztezte az utadat!",
                }
                task_count = 3 if hit_obstacle == "closure" else 1
                self._begin_learning_challenge(
                    count=task_count,
                    reward=0,
                    title="3 FELADATOS ÚTJAVÍTÁS" if task_count == 3 else "TUDÁS-SZERVIZ",
                    reason=obstacle_names[hit_obstacle],
                    is_collision=True,
                    delay=250,
                )
            elif self.pending_life_challenges:
                self._start_pending_life(delay=180)
            elif self.pending_bonus_challenges:
                self._start_pending_bonus(delay=180)
            elif self.lives <= 0:
                self.after(250, self._game_over)
            else:
                self.animation_job = self.after(32, self._drive_tick)
