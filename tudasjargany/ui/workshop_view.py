"""A főalkalmazásból kiemelt, önálló felelősségű műveletek."""

from __future__ import annotations

import math
import random
import threading
import tkinter as tk
from tudasjargany.app import BRICK_BLUE, BRICK_GREEN, BRICK_RED, BRICK_YELLOW, CAR_COLORS, Part

class WorkshopViewMixin:

    def _car_center(self) -> float:
            width = max(900, self.canvas.winfo_width())
            return min(width - 330, width * 0.47)

    def _draw(self) -> None:
            if self.mode == "build":
                self._draw_workshop()
            elif self.mode == "drive":
                self._draw_road()

    def _draw_workshop(self) -> None:
            self.canvas.delete("all")
            width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
            if self._is_unicorn_mode():
                self._draw_unicorn_workshop()
                return
            if self._is_helicopter_mode():
                self._draw_helicopter_workshop()
                return
            self.canvas.create_rectangle(0, 0, width, height, fill=BG, outline="")
            self.canvas.create_rectangle(0, height - 105, width, height, fill="#D5E5EA", outline="")
            for x in range(0, width, 80):
                self.canvas.create_line(x, height - 105, x - 35, height, fill="#BED1D7")
            self.canvas.create_text(
                self._car_center(), 62, text="AZ AUTÓ HELYE",
                font=("Arial", 17, "bold"), fill="#55738A"
            )

            self._draw_color_picker()

            tray_left = max(565, width - 335)
            self.canvas.create_rectangle(
                tray_left, 25, width - 25, height - 25,
                fill="#FFFFFF", outline="#87BDE1", width=3
            )
            self.canvas.create_rectangle(tray_left, 25, width - 25, 65, fill="#1976D2", outline="")
            self.canvas.create_text(
                (tray_left + width - 25) / 2, 45, text="ALKATRÉSZEK",
                font=("Arial", 14, "bold"), fill="white"
            )
            self.canvas.create_text(
                (tray_left + width - 25) / 2, 76,
                text="KÖTELEZŐ ELEMEK", font=("Arial", 10, "bold"), fill="#1565C0"
            )
            self.canvas.create_line(
                tray_left + 15, 385, width - 40, 385, fill="#B8CDDA", width=2
            )
            self.canvas.create_text(
                (tray_left + width - 25) / 2, 396,
                text="VÁLASZTHATÓ EXTRÁK", font=("Arial", 10, "bold"), fill="#7E57C2"
            )

            for part in self.parts:
                if not part.placed:
                    self._draw_part(part, *self._target(part), ghost=True)
            for part in self.parts:
                if part.placed:
                    self._draw_part(part, *self._target(part))
            for part in self.parts:
                if not part.placed:
                    self._draw_part(part, part.x, part.y)

            required_total = sum(part.required for part in self.parts)
            required_done = sum(part.required and part.placed for part in self.parts)
            extra_total = len(self.parts) - required_total
            extra_done = sum(not part.required and part.placed for part in self.parts)
            self.canvas.create_text(
                self._car_center(), 455,
                text=f"Kötelező: {required_done}/{required_total}    Extrák: {extra_done}/{extra_total}",
                font=("Arial", 14, "bold"),
                fill="#26734D" if required_done == required_total else "#55738A"
            )

    def _draw_unicorn_workshop(self) -> None:
            width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
            self.canvas.create_rectangle(0, 0, width, height, fill="#F9D9F3", outline="")
            self.canvas.create_rectangle(0, height - 125, width, height, fill="#A8E6A3", outline="")
            center_x = width / 2
            self._draw_rainbow(center_x - 170, 70, 340, 175)
            self._draw_unicorn(center_x, height - 190)
            self.canvas.create_text(center_x, 55, text="🦄  KATA  🦄", font=("Arial", 24, "bold"), fill="#8D3BA4")
            for x in range(75, width, 125):
                self._draw_flower(x, height - 86, "#FF6FAB" if x % 2 else "#FFD43B")

    def _draw_helicopter_workshop(self) -> None:
            """Kesz helikoptert mutat, amikor a helikopteres jatek van kivalasztva."""
            width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
            self.canvas.create_rectangle(0, 0, width, height, fill="#CDEFFF", outline="")
            self.canvas.create_rectangle(0, height - 120, width, height, fill="#9AD486", outline="")
            center_x = width * 0.47
            self.canvas.create_oval(center_x - 175, height - 245, center_x + 175, height + 90, fill="#738B95", outline="#455A64", width=4)
            self.canvas.create_oval(center_x - 125, height - 195, center_x + 125, height + 40, fill="#F5F5F5", outline="")
            self._draw_helicopter(center_x, height - 180)
            self.canvas.create_text(center_x, 66, text="HELIKOPTERES MENTŐREPÜLÉS", font=("Arial", 21, "bold"), fill="#1565C0")
            text_width = max(360, min(760, width - 80))
            self.canvas.create_text(center_x, 102, text="Gyűjts csillagokat, és kerüld ki a felhőket, madarakat, repülőket!", font=("Arial", 13, "bold"), fill=INK, width=text_width, justify="center")
            self.canvas.create_text(center_x, height - 36, text="A helikopter indulásra kész - kattints az INDULÁS gombra!", font=("Arial", 14, "bold"), fill="#155A35", width=text_width, justify="center")

    def _draw_color_picker(self) -> None:
            """Nagy, egérrel kattintható színmintákat rajzol a műhelybe."""
            self.canvas.create_rectangle(
                20, 25, 230, 250, fill="white", outline="#87BDE1", width=3
            )
            self.canvas.create_text(
                125, 50, text="AUTÓ SZÍNE – 16 FÉLE", font=("Arial", 12, "bold"), fill=INK
            )
            self.color_boxes = []
            for index, (name, color) in enumerate(CAR_COLORS.items()):
                col, row = index % 4, index // 4
                x1, y1 = 34 + col * 49, 72 + row * 43
                x2, y2 = x1 + 36, y1 + 31
                selected = color == self.car_color
                self.canvas.create_rectangle(
                    x1 - 4, y1 - 4, x2 + 4, y2 + 4,
                    fill="#FFF3A6" if selected else "white",
                    outline="#F2B705" if selected else "#D5E3EA",
                    width=3 if selected else 1,
                )
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="#243746", width=2
                )
                if selected:
                    self.canvas.create_text(
                        (x1 + x2) / 2, (y1 + y2) / 2,
                        text="✓", font=("Arial", 16, "bold"),
                        fill=self._contrast_text(color)
                    )
                self.color_boxes.append((x1 - 5, y1 - 5, x2 + 5, y2 + 5, name, color))

    def _contrast_text(color: str) -> str:
            red, green, blue = (int(color[index:index + 2], 16) for index in (1, 3, 5))
            brightness = red * 0.299 + green * 0.587 + blue * 0.114
            return INK if brightness > 165 else "white"

    def _draw_part(self, part: Part, x: float, y: float, ghost: bool = False) -> None:
            outline = "#90A4AE" if ghost else "#1A2633"
            fill = "" if ghost else part.color
            dash = (7, 5) if ghost else None
            tag = f"part-{part.name}"

            if part.kind == "wheel":
                self.canvas.create_oval(
                    x, y, x + part.width, y + part.height,
                    fill=fill, outline=outline, width=3, dash=dash, tags=tag
                )
                if not ghost:
                    self.canvas.create_oval(
                        x + 17, y + 17, x + part.width - 17, y + part.height - 17,
                        fill="#90A4AE", outline="#ECEFF1", width=3, tags=tag
                    )
                    self.canvas.create_oval(
                        x + 27, y + 27, x + part.width - 27, y + part.height - 27,
                        fill=BRICK_YELLOW, outline="", tags=tag
                    )
            elif part.kind == "spoiler":
                if ghost:
                    self.canvas.create_rectangle(
                        x, y, x + part.width, y + part.height,
                        fill="", outline=outline, width=3, dash=dash, tags=tag
                    )
                else:
                    self.canvas.create_rectangle(
                        x, y + 2, x + part.width, y + 14,
                        fill=fill, outline=outline, width=2, tags=tag
                    )
                    for support_x in (x + 17, x + part.width - 27):
                        self.canvas.create_rectangle(
                            support_x, y + 13, support_x + 10, y + part.height,
                            fill=fill, outline=outline, width=2, tags=tag
                        )
            elif part.kind == "hitch":
                if ghost:
                    self.canvas.create_rectangle(
                        x, y, x + part.width, y + part.height,
                        fill="", outline=outline, width=3, dash=dash, tags=tag
                    )
                else:
                    self.canvas.create_rectangle(
                        x, y + 9, x + part.width - 16, y + 17,
                        fill=fill, outline=outline, width=2, tags=tag
                    )
                    self.canvas.create_oval(
                        x + part.width - 22, y + 3, x + part.width, y + part.height,
                        fill="#90A4AE", outline=outline, width=2, tags=tag
                    )
            elif part.kind == "siren":
                self.canvas.create_rectangle(
                    x, y + 5, x + part.width, y + part.height,
                    fill="" if ghost else "#ECEFF1", outline=outline,
                    width=3, dash=dash, tags=tag
                )
                if not ghost:
                    middle = x + part.width / 2
                    self.canvas.create_rectangle(
                        x + 5, y + 2, middle, y + part.height - 3,
                        fill="#E53935", outline="#7A1414", tags=tag
                    )
                    self.canvas.create_rectangle(
                        middle, y + 2, x + part.width - 5, y + part.height - 3,
                        fill="#1976D2", outline="#0D4775", tags=tag
                    )
            elif part.kind == "taxi":
                self.canvas.create_polygon(
                    x, y + part.height,
                    x + 7, y,
                    x + part.width - 7, y,
                    x + part.width, y + part.height,
                    fill=fill, outline=outline, width=3, dash=dash, tags=tag
                )
                if not ghost:
                    self.canvas.create_text(
                        x + part.width / 2, y + part.height / 2 + 2,
                        text="TAXI", font=("Arial", 8, "bold"), fill=INK, tags=tag
                    )
            elif part.kind == "cabin":
                self._draw_cabin_part(part, x, y, ghost, outline, fill, dash, tag)
            elif part.kind == "brick":
                self._draw_body_part(part, x, y, ghost, outline, fill, dash, tag)
            else:
                self.canvas.create_rectangle(
                    x, y, x + part.width, y + part.height,
                    fill=fill, outline=outline, width=3, dash=dash, tags=tag
                )
                if not ghost:
                    studs = max(1, part.width // 42)
                    gap = part.width / studs
                    for index in range(studs):
                        sx = x + gap * (index + 0.5)
                        self.canvas.create_oval(
                            sx - 10, y - 6, sx + 10, y + 7,
                            fill=self._lighter(part.color), outline="#1A2633", width=1, tags=tag
                        )


            if ghost:
                self.canvas.create_text(
                    x + part.width / 2, y + part.height / 2,
                    text=part.name.replace(" ", "\n", 1),
                    font=("Arial", 9, "bold"), fill="#78909C", justify="center"
                )
            elif not part.placed and part.kind not in ("wheel", "siren", "taxi"):
                label_fill = INK if part.kind == "light" else "white"
                self.canvas.create_text(
                    x + part.width / 2, y + part.height / 2, text=part.name,
                    font=("Arial", 8 if part.kind in ("spoiler", "hitch") else 9, "bold"),
                    fill=label_fill, tags=tag
                )

    def _draw_cabin_part(
            self, part: Part, x: float, y: float, ghost: bool,
            outline: str, fill: str, dash, tag: str
        ) -> None:
            """Formához illő tetőt és osztott ablakokat rajzol oldalnézetben."""
            style = self.car_style.get()
            w, h = part.width, part.height
            if style == "SPORTAUTÓ":
                points = (x + 5, y + h, x + 32, y + 8, x + w - 38, y + 8, x + w, y + h)
            elif style == "TEREPJÁRÓ":
                points = (x, y + h, x + 8, y + 4, x + w - 8, y + 4, x + w, y + h)
            elif style == "PICKUP":
                points = (x, y + h, x + 12, y + 6, x + w - 42, y + 6, x + w, y + h)
            else:
                points = (x, y + h, x + 20, y + 7, x + w - 25, y + 7, x + w, y + h)
            self.canvas.create_polygon(
                points, fill=fill, outline=outline, width=3, dash=dash, tags=tag
            )
            if ghost:
                return

            margin = 15 if style != "SPORTAUTÓ" else 23
            top = y + 15
            bottom = y + h - 11
            left = x + margin
            right = x + w - margin
            pillar = x + w * (0.46 if style == "PICKUP" else 0.51)
            self.canvas.create_polygon(
                left, bottom, left + 10, top, pillar - 5, top, pillar - 5, bottom,
                fill="#BDEBFF", outline="#0D4775", width=2, tags=tag
            )
            self.canvas.create_polygon(
                pillar + 5, top, right - 13, top, right, bottom, pillar + 5, bottom,
                fill="#A8DDF2", outline="#0D4775", width=2, tags=tag
            )
            self.canvas.create_rectangle(
                pillar - 5, top - 1, pillar + 5, bottom + 1,
                fill="#173A59", outline="", tags=tag
            )
            for stud_x in (x + 25, x + w - 25):
                self.canvas.create_oval(
                    stud_x - 9, y - 5, stud_x + 9, y + 7,
                    fill=self._lighter(part.color), outline="#1A2633", tags=tag
                )

    def _draw_body_part(
            self, part: Part, x: float, y: float, ghost: bool,
            outline: str, fill: str, dash, tag: str
        ) -> None:
            """Részletes, a választott autóformához igazodó karosszériát rajzol."""
            style = self.car_style.get()
            w, h = part.width, part.height
            if style == "SPORTAUTÓ":
                points = (x, y + 31, x + 42, y + 10, x + w - 48, y + 10,
                          x + w, y + 35, x + w - 8, y + h, x + 8, y + h)
                self.canvas.create_polygon(
                    points, fill=fill, outline=outline, width=3, dash=dash, tags=tag
                )
            elif style == "PICKUP":
                points = (x, y + 14, x + 108, y + 14, x + 133, y + 2,
                          x + w - 10, y + 2, x + w, y + 29,
                          x + w - 7, y + h, x, y + h)
                self.canvas.create_polygon(
                    points, fill=fill, outline=outline, width=3, dash=dash, tags=tag
                )
                if not ghost:
                    self.canvas.create_rectangle(
                        x + 10, y + 25, x + 102, y + h - 10,
                        fill=self._lighter(part.color), outline=outline, width=2, tags=tag
                    )
                    self.canvas.create_line(
                        x + 108, y + 15, x + 108, y + h - 7,
                        fill=outline, width=3, tags=tag
                    )
            elif style == "VÁROSI AUTÓ":
                points = (x, y + 22, x + 27, y + 8, x + w - 42, y + 8,
                          x + w, y + 27, x + w - 4, y + h, x + 4, y + h)
                self.canvas.create_polygon(
                    points, fill=fill, outline=outline, width=3, dash=dash, tags=tag
                )
            else:
                self.canvas.create_rectangle(
                    x, y, x + w, y + h, fill=fill,
                    outline=outline, width=4, dash=dash, tags=tag
                )
                if not ghost:
                    self.canvas.create_rectangle(
                        x + 8, y + h - 20, x + w - 8, y + h - 7,
                        fill="#37474F", outline="", tags=tag
                    )
            if not ghost:
                door_x = x + (176 if style == "PICKUP" else 151)
                self.canvas.create_line(
                    door_x, y + 17, door_x, y + h - 7,
                    fill="#263238", width=2, tags=tag
                )
                self.canvas.create_rectangle(
                    door_x + 12, y + 29, door_x + 34, y + 34,
                    fill="#ECEFF1", outline="#263238", tags=tag
                )
                self.canvas.create_rectangle(
                    x + w - 12, y + 32, x + w, y + h - 13,
                    fill="#263238", outline="", tags=tag
                )
                for index in range(6):
                    sx = x + w * (index + 0.5) / 6
                    self.canvas.create_oval(
                        sx - 10, y - 6, sx + 10, y + 7,
                        fill=self._lighter(part.color), outline="#1A2633", width=1, tags=tag
                    )

    def _lighter(color: str) -> str:
            """Világosabb árnyalat az építőkocka bütykeihez."""
            if len(color) != 7 or not color.startswith("#"):
                return color
            red, green, blue = (int(color[i:i + 2], 16) for i in (1, 3, 5))
            red = min(255, red + 45)
            green = min(255, green + 45)
            blue = min(255, blue + 45)
            return f"#{red:02X}{green:02X}{blue:02X}"
