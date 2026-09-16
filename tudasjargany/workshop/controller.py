"""A főalkalmazásból kiemelt, önálló felelősségű műveletek."""

from __future__ import annotations

import math
import random
import threading
import tkinter as tk
from tudasjargany.app import BASE_ROAD_SPEED, BRICK_BLUE, BRICK_GREEN, BRICK_RED, BRICK_YELLOW, Part
from tudasjargany.core.state import GameMode

class WorkshopControllerMixin:

    def _make_parts() -> list[Part]:
            return [
                Part("AUTÓ ALAPJA", "brick", BRICK_RED, 285, 78, 90, -142, 292),
                Part("KÉK TETŐ", "cabin", BRICK_BLUE, 145, 76, 178, -55, 216),
                Part("SÁRGA LÁMPA", "light", BRICK_YELLOW, 38, 28, 268, 143, 316, -1),
                Part("ZÖLD LÖKHÁRÍTÓ", "bumper", BRICK_GREEN, 50, 25, 268, -192, 338, 1),
                Part("BAL KERÉK", "wheel", "#263238", 67, 67, 307, -102, 344, -1),
                Part("JOBB KERÉK", "wheel", "#263238", 67, 67, 307, 72, 344, 1),
                Part("LÉGTERELŐ", "spoiler", "#F57C00", 82, 25, 410, -162, 267, -1, False),
                Part("VONÓHOROG", "hitch", "#546E7A", 58, 25, 410, -247, 350, 1, False),
                Part("SZIRÉNA", "siren", "#1976D2", 62, 27, 451, -53, 186, -1, False),
                Part("TAXIJEL", "taxi", BRICK_YELLOW, 58, 29, 451, 31, 184, 1, False),
            ]

    def _target(self, part: Part) -> tuple[float, float]:
            horizontal_adjustment = 0
            # A pickup kabinja és tetőextrái előrébb kerülnek, így nem lógnak a platóra.
            if self.car_style.get() == "PICKUP" and part.kind in ("cabin", "siren", "taxi"):
                horizontal_adjustment = 50
            return self._car_center() + part.target_dx + horizontal_adjustment, part.target_y

    def _tray_x(self, part: Part) -> float:
            tray_left = max(565, self.canvas.winfo_width() - 335)
            if part.tray_col < 0:
                return tray_left + 47
            if part.tray_col > 0:
                return tray_left + 263 - part.width
            return tray_left + (310 - part.width) / 2

    def _mouse_down(self, event) -> None:
            if self.mode == "build" and self._is_special_game_mode():
                return
            if self.mode == "drive":
                road_left, road_right = self._road_edges()
                if road_left < event.x < road_right:
                    lane_width = (road_right - road_left) / 4
                    self.lane = max(0, min(3, int((event.x - road_left) // lane_width)))
                return
            if self.auto_assembling:
                return
            for x1, y1, x2, y2, name, color in self.color_boxes:
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    self.car_color = color
                    next(part for part in self.parts if part.kind == "brick").color = color
                    self.status.configure(text=f"Az autó új színe: {name.lower()}!", fg=color)
                    self._draw_workshop()
                    return
            for part in reversed(self.parts):
                if not part.placed and part.x <= event.x <= part.x + part.width and part.y <= event.y <= part.y + part.height:
                    self.dragged = part
                    self.drag_offset = (event.x - part.x, event.y - part.y)
                    self.status.configure(text=f"Vidd a helyére: {part.name}", fg="#1565C0")
                    break

    def _mouse_drag(self, event) -> None:
            if self.mode == "build" and not self._is_special_game_mode() and self.dragged:
                wanted_x = event.x - self.drag_offset[0]
                wanted_y = event.y - self.drag_offset[1]
                self.dragged.x = max(
                    5, min(wanted_x, self.canvas.winfo_width() - self.dragged.width - 5)
                )
                self.dragged.y = max(
                    8, min(wanted_y, self.canvas.winfo_height() - self.dragged.height - 8)
                )
                self._draw_workshop()

    def _mouse_up(self, _event) -> None:
            if self.mode != "build" or self._is_special_game_mode() or not self.dragged:
                return
            part = self.dragged
            tx, ty = self._target(part)
            distance = math.hypot(part.x - tx, part.y - ty)
            if distance < 85:
                part.x, part.y, part.placed = tx, ty, True
                self.bell()
                remaining_required = sum(
                    item.required and not item.placed for item in self.parts
                )
                if remaining_required:
                    kind_text = "Extra felszerelve!" if not part.required else "Katt! A helyén van."
                    self.status.configure(
                        text=f"{kind_text} Még {remaining_required} kötelező elem hiányzik.",
                        fg="#238636",
                    )
                else:
                    self.status.configure(
                        text="Minden kötelező elem kész! Extrákat még felszerelhetsz.",
                        fg="#238636",
                    )
                    self.start_button.configure(state="normal", bg=BRICK_GREEN, activebackground="#55C16B", fg="white")
                    self.auto_button.configure(state="disabled")
            else:
                part.x, part.y = self._tray_x(part), part.tray_y
                self.status.configure(text="Majdnem! Keresd az elem szaggatott körvonalát.", fg="#D14B3E")
            self.dragged = None
            self._draw_workshop()

    def _auto_assemble(self) -> None:
            """Egymás után a helyükre pattintja a hiányzó alkatrészeket."""
            if self.mode != "build" or self.auto_assembling:
                return
            remaining = [part for part in self.parts if part.required and not part.placed]
            if not remaining:
                return
            self.assembly_run += 1
            run = self.assembly_run
            self.auto_assembling = True
            self.dragged = None
            self.auto_button.configure(state="disabled")
            self.status.configure(text="Az autószerelő robot munkához lát...", fg="#7E57C2")
            self._auto_place_next(remaining, 0, run)

    def _auto_place_next(self, parts: list[Part], index: int, run: int) -> None:
            if run != self.assembly_run or self.mode != "build":
                return
            if index >= len(parts):
                self.auto_assembling = False
                self.status.configure(
                    text="A kötelező elemek készen vannak! Válassz extrát, vagy indulj!",
                    fg="#238636",
                )
                self.start_button.configure(
                    state="normal", bg=BRICK_GREEN, activebackground="#55C16B", fg="white"
                )
                self._draw_workshop()
                self.bell()
                return
            part = parts[index]
            part.x, part.y = self._target(part)
            part.placed = True
            self.status.configure(
                text=f"Katt! A helyére került: {part.name}  ({index + 1}/{len(parts)})",
                fg="#7E57C2",
            )
            self._draw_workshop()
            self.after(280, lambda: self._auto_place_next(parts, index + 1, run))

    def _start_driving(self) -> None:
            if not self._is_special_game_mode() and not all(part.placed for part in self.parts if part.required):
                return
            self._stop_siren()
            self.game_state.mode = (
                GameMode.UNICORN if self._is_unicorn_mode()
                else GameMode.HELICOPTER if self._is_helicopter_mode()
                else GameMode.CAR
            )
            self.mode = "drive"
            self.lane, self.frame, self.score, self.lives = 1, 0, 0, 3
            self.speed_level, self.road_speed = 0, BASE_ROAD_SPEED
            self.speed_just_increased = False
            self.last_drive_status = None
            self.pending_bonus_challenges = 0
            self.pending_life_challenges = 0
            self.road_items = []
            self.message, self.message_frames = "RAJT!", 45
            self.math_active = False
            if self._is_unicorn_mode():
                self.header_text.configure(text="🦄  Kata unikornisa  🦄")
            elif self._is_helicopter_mode():
                self.header_text.configure(text="Repülj csillagokat gyűjteni, és kerüld ki a felhőket, madarakat, repülőket!")
            else:
                self.header_text.configure(text="Gyűjts csillagokat, kerüld ki az akadályokat!")
            self._show_drive_controls()
            if not self._is_special_game_mode():
                self._play_sound_effect("engine_start")
                self.after(950, self._start_siren_loop)
            self._update_drive_status()
            self.focus_set()
            self._drive_tick()
