"""A főalkalmazásból kiemelt, önálló felelősségű műveletek."""

from __future__ import annotations

import math
import random
import threading
import tkinter as tk
from tudasjargany.app import BRICK_BLUE, BRICK_GREEN, BRICK_RED, BRICK_YELLOW, INK

class GameViewMixin:

    def _draw_road(self) -> None:
            if self._is_unicorn_mode():
                self._draw_unicorn_scene()
                return
            if self._is_helicopter_mode():
                self._draw_flight_scene()
                return
            self.canvas.delete("all")
            width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
            left, right = self._road_edges()
            self.canvas.create_rectangle(0, 0, width, height, fill="#8DD8FF", outline="")
            self.canvas.create_oval(width - 125, 25, width - 55, 95, fill=BRICK_YELLOW, outline="")
            self.canvas.create_rectangle(0, 105, width, height, fill="#69C56B", outline="")
            self._draw_houses(left, right)
            self.canvas.create_polygon(left, 0, right, 0, right, height, left, height, fill="#4C5560", outline="")
            self.canvas.create_line(left, 0, left, height, fill="white", width=7)
            self.canvas.create_line(right, 0, right, height, fill="white", width=7)
            self.canvas.create_rectangle(
                right - 185, 14, right - 14, 52,
                fill="#17324D", outline="white", width=2
            )
            self.canvas.create_text(
                right - 99, 33,
                text=f"SEBESSÉG: {self.speed_level + 1}. FOKOZAT",
                font=("Arial", 10, "bold"), fill="white"
            )

            lane_width = (right - left) / 4
            dash_offset = (self.frame * self.road_speed) % 72
            for divider in (left + lane_width, left + lane_width * 2, left + lane_width * 3):
                y = -72 + dash_offset
                while y < height:
                    self.canvas.create_rectangle(divider - 3, y, divider + 3, y + 38, fill="white", outline="")
                    y += 72

            for item in self.road_items:
                x, y = self._lane_x(float(item.get("lane_position", item["lane"]))), float(item["y"])
                kind = item["kind"]
                if kind == "star":
                    self._draw_star(x, y, 27)
                elif kind == "cone":
                    self._draw_cone(x, y)
                elif kind == "car":
                    self._draw_other_car(x, y)
                elif kind == "motorcycle":
                    self._draw_wild_motorcycle(x, y, float(item.get("lane_direction", 1.0)))
                elif kind == "bus":
                    self._draw_bus(x, y)
                elif kind == "asphalt_paver":
                    self._draw_asphalt_paver(x, y)
                elif kind == "dumper":
                    self._draw_dumper(x, y)
                elif kind == "dirt_pile":
                    self._draw_dirt_pile(x, y)
                else:
                    self._draw_lane_closure(x, y)
            self._draw_driving_car(self._lane_x(self.lane), height - 128)
            if self.message_frames:
                self.canvas.create_text(width / 2, 60, text=self.message, font=("Arial", 22, "bold"), fill="white")

    def _draw_unicorn_scene(self) -> None:
            self.canvas.delete("all")
            width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
            self.canvas.create_rectangle(0, 0, width, height, fill="#BEEBFF", outline="")
            self.canvas.create_rectangle(0, height - 110, width, height, fill="#9BE29B", outline="")
            self._draw_rainbow(width - 300, -90, 260, 220)
            for x in range(55, width, 115):
                self._draw_flower(x, height - 75, "#FF6FAB" if x % 3 else "#FFD43B")
            left, right = self._road_edges()
            lane_width = (right - left) / 4
            for divider in (left + lane_width, left + lane_width * 2, left + lane_width * 3):
                self.canvas.create_line(divider, 82, divider, height - 110, fill="#F6D7FF", width=5, dash=(8, 13))
            for item in self.road_items:
                if item["kind"] == "unicorn_star":
                    self._draw_star(self._lane_x(float(item["lane"])), float(item["y"]), 30)
            self._draw_unicorn(self._lane_x(self.lane), height - 140)
            self.canvas.create_text(width / 2, 45, text=f"⭐  {self.score}", font=("Arial", 26, "bold"), fill="#C75DCE")

    def _draw_flight_scene(self) -> None:
            self.canvas.delete("all")
            width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
            self.canvas.create_rectangle(0, 0, width, height, fill="#88D8FF", outline="")
            self.canvas.create_oval(width - 125, 28, width - 55, 98, fill=BRICK_YELLOW, outline="")
            self.canvas.create_rectangle(0, height - 105, width, height, fill="#83C96A", outline="")
            for cloud_x, cloud_y, scale in ((90, 95, 0.8), (width - 180, 160, 0.65), (width * 0.48, 82, 0.45)):
                self._draw_cloud(cloud_x, cloud_y, scale, "#F5FCFF")
            left, right = self._road_edges()
            lane_width = (right - left) / 4
            for divider in (left + lane_width, left + lane_width * 2, left + lane_width * 3):
                self.canvas.create_line(divider, 80, divider, height - 110, fill="#D8F4FF", width=2, dash=(8, 12))
            self.canvas.create_text(width / 2, 34, text="HELIKOPTERES MENTŐREPÜLÉS", font=("Arial", 15, "bold"), fill="#17324D")
            self.canvas.create_rectangle(right - 185, 48, right - 14, 84, fill="#17324D", outline="white", width=2)
            self.canvas.create_text(right - 99, 66, text=f"REPÜLÉS: {self.speed_level + 1}. SZINT", font=("Arial", 10, "bold"), fill="white")
            for item in self.road_items:
                x = self._lane_x(float(item.get("lane_position", item["lane"])))
                y = float(item["y"])
                kind = item["kind"]
                if kind == "star":
                    self._draw_star(x, y, 27)
                elif kind == "cloud":
                    self._draw_cloud(x, y, 1.0, "#607D8B")
                elif kind == "bird":
                    self._draw_bird(x, y)
                elif kind == "plane":
                    self._draw_plane(x, y)
            self._draw_helicopter(self._lane_x(self.lane), height - 135)
            if self.message_frames:
                self.canvas.create_text(width / 2, 105, text=self.message, font=("Arial", 22, "bold"), fill="white")

    def _draw_houses(self, left: float, right: float) -> None:
            for side_x in (left - 105, right + 105):
                for index in range(5):
                    y = -95 + index * 155 + (self.frame * 2 % 155)
                    x1, x2 = side_x - 55, side_x + 55
                    color = ("#FF8A65", "#7E57C2", "#26A69A", "#FFA726", "#EC6A8C")[index]
                    self.canvas.create_rectangle(x1, y, x2, y + 90, fill=color, outline="#37474F", width=2)
                    self.canvas.create_polygon(x1 - 12, y, x2 + 12, y, side_x, y - 42, fill="#8D4E36", outline="#37474F")
                    self.canvas.create_rectangle(side_x - 13, y + 50, side_x + 13, y + 90, fill="#6D4C41", outline="")

    def _draw_driving_car(self, x: float, y: float) -> None:
            extras = {part.kind for part in self.parts if not part.required and part.placed}
            style = self.car_style.get()
            wheel_edge = 63 if style == "TEREPJÁRÓ" else 55
            self.canvas.create_oval(x - wheel_edge, y - 55, x - wheel_edge + 20, y + 55, fill="#20262A", outline="")
            self.canvas.create_oval(x + wheel_edge - 20, y - 55, x + wheel_edge, y + 55, fill="#20262A", outline="")
            if "hitch" in extras:
                self.canvas.create_rectangle(x - 5, y + 66, x + 5, y + 88, fill="#546E7A", outline="#263238")
                self.canvas.create_oval(x - 10, y + 82, x + 10, y + 101, fill="#90A4AE", outline="#263238", width=2)
            if style == "SPORTAUTÓ":
                self.canvas.create_polygon(
                    x - 32, y - 76, x + 32, y - 76, x + 50, y - 42,
                    x + 47, y + 62, x + 33, y + 72, x - 33, y + 72,
                    x - 47, y + 62, x - 50, y - 42,
                    fill=self.car_color, outline="#4B2630", width=3
                )
                cabin = (x - 32, y - 25, x + 32, y + 22)
            elif style == "TEREPJÁRÓ":
                self.canvas.create_rectangle(x - 56, y - 76, x + 56, y + 76, fill=self.car_color, outline="#263238", width=5)
                self.canvas.create_rectangle(x - 50, y + 55, x + 50, y + 68, fill="#37474F", outline="")
                cabin = (x - 43, y - 30, x + 43, y + 30)
            elif style == "PICKUP":
                self.canvas.create_rectangle(x - 50, y - 72, x + 50, y + 72, fill=self.car_color, outline="#4B2630", width=3)
                self.canvas.create_rectangle(x - 40, y + 24, x + 40, y + 62, fill=self._lighter(self.car_color), outline="#4B2630", width=2)
                cabin = (x - 38, y - 39, x + 38, y + 12)
            else:
                self.canvas.create_rectangle(x - 48, y - 70, x + 48, y + 70, fill=self.car_color, outline="#4B2630", width=3)
                cabin = (x - 38, y - 25, x + 38, y + 30)
            cx1, cy1, cx2, cy2 = cabin
            self.canvas.create_rectangle(cx1, cy1, cx2, cy2, fill=BRICK_BLUE, outline="#0D4775", width=3)
            self.canvas.create_rectangle(cx1 + 9, cy1 + 9, cx2 - 9, cy2 - 9, fill="#BDEBFF", outline="")
            for sx in (-30, 0, 30):
                self.canvas.create_oval(x + sx - 8, y + 47, x + sx + 8, y + 58, fill="#FF7773", outline="#7A1414")
            if "spoiler" in extras:
                self.canvas.create_rectangle(x - 58, y + 44, x + 58, y + 54, fill="#F57C00", outline="#6D3A00", width=2)
                self.canvas.create_rectangle(x - 38, y + 53, x - 29, y + 66, fill="#F57C00", outline="#6D3A00")
                self.canvas.create_rectangle(x + 29, y + 53, x + 38, y + 66, fill="#F57C00", outline="#6D3A00")
            if "siren" in extras:
                self.canvas.create_rectangle(x - 37, y - 38, x, y - 26, fill="#E53935", outline="white")
                self.canvas.create_rectangle(x, y - 38, x + 37, y - 26, fill="#2196F3", outline="white")
            if "taxi" in extras:
                self.canvas.create_rectangle(x - 24, y + 21, x + 24, y + 36, fill=BRICK_YELLOW, outline="#5D4A00", width=2)
                self.canvas.create_text(x, y + 29, text="TAXI", font=("Arial", 7, "bold"), fill=INK)
            self.canvas.create_oval(x - 37, y - 62, x - 18, y - 43, fill=BRICK_YELLOW, outline="#A47A00")
            self.canvas.create_oval(x + 18, y - 62, x + 37, y - 43, fill=BRICK_YELLOW, outline="#A47A00")

    def _draw_star(self, x: float, y: float, radius: float) -> None:
            points = []
            for index in range(10):
                angle = -math.pi / 2 + index * math.pi / 5
                r = radius if index % 2 == 0 else radius * 0.43
                points.extend((x + math.cos(angle) * r, y + math.sin(angle) * r))
            self.canvas.create_polygon(points, fill=BRICK_YELLOW, outline="#E09B00", width=3)

    def _draw_cone(self, x: float, y: float) -> None:
            self.canvas.create_polygon(x, y - 31, x - 25, y + 28, x + 25, y + 28, fill="#FF6D00", outline="#8D3B00", width=3)
            self.canvas.create_rectangle(x - 19, y + 2, x + 19, y + 12, fill="white", outline="")
            self.canvas.create_rectangle(x - 34, y + 27, x + 34, y + 37, fill="#FF6D00", outline="#8D3B00", width=2)

    def _draw_wild_motorcycle(self, x: float, y: float, direction: float) -> None:
            """Szines, enyhen megdolgoztatott motor es sisakos motoros felulnezetben."""
            lean = 11 if direction > 0 else -11
            self.canvas.create_line(x - lean, y - 39, x + lean, y + 44, fill="#20262A", width=10)
            self.canvas.create_oval(x - lean - 12, y - 49, x - lean + 12, y - 25, fill="#1B2026", outline="#101418", width=2)
            self.canvas.create_oval(x + lean - 12, y + 29, x + lean + 12, y + 53, fill="#1B2026", outline="#101418", width=2)
            self.canvas.create_polygon(
                x - 14 + lean, y - 20, x + 15 + lean, y - 10,
                x + 12 + lean, y + 27, x - 12 + lean, y + 30,
                fill="#E53935", outline="#6D1515", width=2,
            )
            self.canvas.create_oval(x - 16 - lean / 3, y - 18, x + 16 - lean / 3, y + 12, fill="#263238", outline="#111820", width=2)
            self.canvas.create_oval(x - 10 - lean / 3, y - 29, x + 10 - lean / 3, y - 9, fill="#FFCE45", outline="#7E5A00", width=2)
            self.canvas.create_line(x - 26 + lean, y + 17, x + 25 + lean, y + 17, fill="#BDEBFF", width=4)
            self.canvas.create_line(x - 38, y + 46, x - 57, y + 64, fill="#F7D24C", width=3)
            self.canvas.create_line(x + 38, y + 46, x + 57, y + 64, fill="#F7D24C", width=3)

    def _draw_rainbow(self, x: float, y: float, width: float, height: float) -> None:
            for index, color in enumerate(("#F45B69", "#FF9F43", "#FFD43B", "#5CCF80", "#4CA6FF", "#A66CFF")):
                inset = index * 12
                self.canvas.create_arc(x + inset, y + inset, x + width - inset, y + height - inset, start=0, extent=180, style="arc", outline=color, width=14)

    def _draw_flower(self, x: float, y: float, color: str) -> None:
            for dx, dy in ((-10, 0), (10, 0), (0, -10), (0, 10)):
                self.canvas.create_oval(x + dx - 8, y + dy - 8, x + dx + 8, y + dy + 8, fill=color, outline="")
            self.canvas.create_oval(x - 7, y - 7, x + 7, y + 7, fill="#FFD43B", outline="#C88A00")
            self.canvas.create_line(x, y + 9, x, y + 35, fill="#3E9D56", width=4)

    def _draw_unicorn(self, x: float, y: float) -> None:
            bob = math.sin(self.frame * 0.16) * 5
            y += bob
            self.canvas.create_line(x - 45, y + 43, x - 52, y + 76, fill="#6F4A8E", width=9)
            self.canvas.create_line(x + 34, y + 43, x + 28, y + 76, fill="#6F4A8E", width=9)
            self.canvas.create_line(x - 58, y + 8, x - 93, y - 12, fill="#FF78B9", width=12, smooth=True)
            self.canvas.create_oval(x - 62, y - 32, x + 48, y + 53, fill="#FFF9FF", outline="#8D5A9F", width=3)
            self.canvas.create_oval(x + 20, y - 70, x + 79, y - 10, fill="#FFF9FF", outline="#8D5A9F", width=3)
            self.canvas.create_polygon(x + 44, y - 68, x + 55, y - 105, x + 65, y - 65, fill="#FFD43B", outline="#C88A00", width=2)
            self.canvas.create_line(x + 14, y - 35, x + 49, y - 72, fill="#A66CFF", width=11, smooth=True)
            self.canvas.create_line(x + 7, y - 27, x + 40, y - 61, fill="#FF78B9", width=8, smooth=True)
            self.canvas.create_oval(x + 57, y - 48, x + 64, y - 41, fill="#263238", outline="")
            self.canvas.create_arc(x + 43, y - 42, x + 62, y - 25, start=200, extent=120, style="arc", outline="#D45A8A", width=2)
            self.canvas.create_polygon(x - 10, y - 24, x - 61, y - 58, x - 35, y + 7, fill="#E8D4FF", outline="#A66CFF", width=2)
            self.canvas.create_oval(x - 22, y - 6, x - 5, y + 11, fill="#FFB8D6", outline="")

    def _draw_helicopter(self, x: float, y: float) -> None:
            rotor_angle = self.frame * 0.45
            rotor_length = 82
            dx = math.cos(rotor_angle) * rotor_length
            dy = math.sin(rotor_angle) * rotor_length * 0.22
            self.canvas.create_line(x - dx, y - 67 - dy, x + dx, y - 67 + dy, fill="#263238", width=5)
            self.canvas.create_line(x, y - 58, x, y - 75, fill="#37474F", width=4)
            self.canvas.create_polygon(x + 35, y - 6, x + 88, y + 10, x + 88, y + 21, x + 31, y + 28, fill=self.car_color, outline="#452060", width=3)
            self.canvas.create_polygon(x + 80, y + 8, x + 112, y - 11, x + 112, y + 32, fill="#FBC02D", outline="#715800", width=2)
            self.canvas.create_oval(x - 54, y - 43, x + 43, y + 42, fill=self.car_color, outline="#452060", width=4)
            self.canvas.create_oval(x - 36, y - 32, x + 19, y + 14, fill="#BDEBFF", outline="#0D4775", width=3)
            self.canvas.create_line(x - 43, y + 49, x + 47, y + 49, fill="#263238", width=5)
            self.canvas.create_line(x - 28, y + 40, x - 43, y + 57, fill="#263238", width=4)
            self.canvas.create_line(x + 24, y + 40, x + 40, y + 57, fill="#263238", width=4)

    def _draw_cloud(self, x: float, y: float, scale: float, color: str) -> None:
            outline = "#455A64" if color != "#F5FCFF" else "#D0EAF5"
            self.canvas.create_oval(x - 48 * scale, y - 4 * scale, x - 3 * scale, y + 31 * scale, fill=color, outline=outline)
            self.canvas.create_oval(x - 25 * scale, y - 27 * scale, x + 28 * scale, y + 31 * scale, fill=color, outline=outline)
            self.canvas.create_oval(x + 6 * scale, y - 12 * scale, x + 52 * scale, y + 31 * scale, fill=color, outline=outline)
            if color != "#F5FCFF":
                for offset in (-22, 0, 22):
                    self.canvas.create_line(x + offset * scale, y + 37 * scale, x + (offset - 5) * scale, y + 51 * scale, fill="#D9F3FC", width=3)

    def _draw_bird(self, x: float, y: float) -> None:
            flap = 8 if self.frame % 10 < 5 else -5
            self.canvas.create_line(x - 37, y + flap, x, y - 8, x + 37, y + flap, fill="#4B2630", width=5, smooth=True)
            self.canvas.create_oval(x - 7, y - 10, x + 8, y + 7, fill="#263238", outline="#111820")

    def _draw_plane(self, x: float, y: float) -> None:
            """Kis utasszállító repülő felülnézetben a légi pályához."""
            self.canvas.create_polygon(
                x, y - 55, x + 17, y - 15, x + 58, y + 8,
                x + 54, y + 21, x + 16, y + 10, x + 10, y + 53,
                x - 10, y + 53, x - 16, y + 10, x - 54, y + 21,
                x - 58, y + 8, x - 17, y - 15,
                fill="#F5F5F5", outline="#315C6A", width=3,
            )
            self.canvas.create_polygon(x - 8, y - 23, x + 8, y - 23, x + 8, y + 4, x - 8, y + 4, fill="#2E86C1", outline="")
            self.canvas.create_line(x - 40, y + 13, x + 40, y + 13, fill="#E53935", width=4)

    def _draw_other_car(self, x: float, y: float) -> None:
            self.canvas.create_oval(x - 45, y - 42, x - 31, y + 43, fill="#1D2529", outline="")
            self.canvas.create_oval(x + 31, y - 42, x + 45, y + 43, fill="#1D2529", outline="")
            self.canvas.create_rectangle(x - 39, y - 55, x + 39, y + 55, fill="#9C4DCC", outline="#452060", width=3)
            self.canvas.create_rectangle(x - 30, y - 18, x + 30, y + 23, fill="#BDEBFF", outline="#0D4775", width=2)
            self.canvas.create_oval(x - 29, y + 37, x - 14, y + 50, fill="#FF5252", outline="")
            self.canvas.create_oval(x + 14, y + 37, x + 29, y + 50, fill="#FF5252", outline="")

    def _draw_bus(self, x: float, y: float) -> None:
            self.canvas.create_rectangle(x - 48, y - 70, x + 48, y + 70, fill="#F4C430", outline="#715800", width=3)
            self.canvas.create_rectangle(x - 36, y - 54, x + 36, y - 17, fill="#A7E4F7", outline="#315C6A", width=2)
            for window_y in (-3, 27):
                self.canvas.create_rectangle(x - 35, y + window_y, x + 35, y + window_y + 18, fill="#D9F3FC", outline="#315C6A")
            self.canvas.create_rectangle(x - 32, y + 54, x - 13, y + 66, fill="#E53935", outline="")
            self.canvas.create_rectangle(x + 13, y + 54, x + 32, y + 66, fill="#E53935", outline="")
            self.canvas.create_text(x, y - 35, text="BUSZ", font=("Arial", 10, "bold"), fill=INK)

    def _draw_asphalt_paver(self, x: float, y: float) -> None:
            """Sárga aszfaltozó gép, amely elfoglal egy teljes sávot."""
            self.canvas.create_rectangle(x - 52, y - 55, x + 52, y + 52, fill="#F4B400", outline="#6D5200", width=3)
            self.canvas.create_rectangle(x - 31, y - 42, x + 31, y - 5, fill="#BDEBFF", outline="#315C6A", width=2)
            self.canvas.create_rectangle(x - 68, y + 25, x + 68, y + 62, fill="#455A64", outline="#263238", width=3)
            for wheel_x in (-38, 38):
                self.canvas.create_oval(x + wheel_x - 13, y + 36, x + wheel_x + 13, y + 62, fill="#20262A", outline="#101418")
            self.canvas.create_text(x, y + 10, text="ASZFALT", font=("Arial", 8, "bold"), fill="#3E2B00")

    def _draw_dumper(self, x: float, y: float) -> None:
            """Narancssárga dömper földdel megrakva."""
            self.canvas.create_rectangle(x - 48, y - 58, x + 48, y + 56, fill="#F57C00", outline="#6D3A00", width=3)
            self.canvas.create_polygon(x - 40, y - 47, x + 40, y - 47, x + 29, y - 4, x - 29, y - 4, fill="#8D5A3B", outline="#5D4037", width=2)
            self.canvas.create_rectangle(x - 32, y + 4, x + 32, y + 41, fill="#BDEBFF", outline="#315C6A", width=2)
            for wheel_x in (-35, 35):
                self.canvas.create_oval(x + wheel_x - 12, y + 38, x + wheel_x + 12, y + 62, fill="#20262A", outline="#101418")
            self.canvas.create_text(x, y + 23, text="DÖMPER", font=("Arial", 8, "bold"), fill="#4B2630")

    def _draw_dirt_pile(self, x: float, y: float) -> None:
            self.canvas.create_oval(x - 52, y - 8, x + 52, y + 34, fill="#8D5A3B", outline="#5D4037", width=3)
            self.canvas.create_oval(x - 30, y - 27, x + 30, y + 26, fill="#A97148", outline="#5D4037", width=2)
            self.canvas.create_text(x, y + 6, text="FÖLD", font=("Arial", 8, "bold"), fill="#FFF3D6")

    def _draw_lane_closure(self, x: float, y: float) -> None:
            self.canvas.create_rectangle(x - 88, y - 30, x + 88, y + 30, fill="#F5F5F5", outline="#5D4037", width=4)
            for stripe_x in range(-78, 80, 40):
                self.canvas.create_polygon(
                    x + stripe_x, y + 27,
                    x + stripe_x + 22, y + 27,
                    x + stripe_x + 50, y - 27,
                    x + stripe_x + 28, y - 27,
                    fill="#E53935", outline=""
                )
            self.canvas.create_rectangle(x - 73, y + 30, x - 58, y + 49, fill="#5D4037", outline="")
            self.canvas.create_rectangle(x + 58, y + 30, x + 73, y + 49, fill="#5D4037", outline="")
            self.canvas.create_text(x, y, text="LEZÁRVA", font=("Arial", 10, "bold"), fill="#17212B")
