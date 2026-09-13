"""TudasJargany autóépítő és könnyű utcai vezetős játék gyerekeknek."""

from __future__ import annotations

import math
import random
import tkinter as tk
from dataclasses import dataclass

from math_tasks import MathTask, MathTaskGenerator


BG = "#EAF7FF"
INK = "#183153"
BRICK_RED = "#E53935"
BRICK_BLUE = "#1976D2"
BRICK_YELLOW = "#FFD43B"
BRICK_GREEN = "#35A853"
BASE_ROAD_SPEED = 6.5
SPEED_STEP = 1.6

CAR_COLORS = {
    "PIROS": BRICK_RED,
    "KÉK": "#1565C0",
    "ZÖLD": "#2EAD58",
    "NARANCS": "#F57C00",
    "RÓZSASZÍN": "#EC407A",
    "LILA": "#7E57C2",
    "SÁRGA": "#FBC02D",
    "TÜRKIZ": "#00A6A6",
    "VILÁGOSKÉK": "#29B6F6",
    "LIME": "#7CB342",
    "BORDÓ": "#8E244D",
    "SÖTÉTKÉK": "#263B80",
    "FEHÉR": "#F5F5F5",
    "FEKETE": "#263238",
    "EZÜST": "#90A4AE",
    "BARNA": "#795548",
}

CAR_STYLES = ("VÁROSI AUTÓ", "SPORTAUTÓ", "TEREPJÁRÓ", "PICKUP")


@dataclass
class Part:
    name: str
    kind: str
    color: str
    width: int
    height: int
    tray_y: int
    target_dx: int
    target_y: int
    tray_col: int = 0
    required: bool = True
    x: float = 0
    y: float = 0
    placed: bool = False


class TudasJarganyGame(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("TudasJargany")
        self.geometry("1050x740")
        self.minsize(900, 650)
        self.configure(bg=BG)

        self.mode = "build"
        self.dragged: Part | None = None
        self.drag_offset = (0.0, 0.0)
        self.animation_job: str | None = None
        self.assembly_run = 0
        self.auto_assembling = False
        self.car_color = BRICK_RED
        self.car_style = tk.StringVar(value=CAR_STYLES[0])
        self.color_boxes: list[tuple[float, float, float, float, str, str]] = []
        self.parts = self._make_parts()

        self.lane = 1
        self.road_items: list[dict[str, float | int | str]] = []
        self.frame = 0
        self.score = 0
        self.lives = 3
        self.speed_level = 0
        self.road_speed = BASE_ROAD_SPEED
        self.pending_bonus_challenges = 0
        self.message = ""
        self.message_frames = 0
        self.math_tasks = MathTaskGenerator()
        self.math_active = False
        self.math_popup: tk.Toplevel | None = None
        self.current_math_task: MathTask | None = None
        self.challenge_tasks_left = 0
        self.challenge_reward = 0
        self.challenge_title = "MATEK-SZERVIZ"
        self.challenge_reason = "Az akadály megállított. Rakd ki a hiányzó részt!"
        self.challenge_is_collision = False
        self.task_timer_job: str | None = None
        self.task_seconds_left = 60
        self.task_resolved = False
        self.speed_just_increased = False

        self._build_window()
        self.after(80, self._reset_build)

    @staticmethod
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

    def _build_window(self) -> None:
        header = tk.Frame(self, bg="#1565C0", padx=20, pady=12)
        header.pack(fill="x")
        tk.Label(
            header, text="TudasJargany", font=("Arial", 23, "bold"),
            bg="#1565C0", fg="white"
        ).pack(side="left")
        self.header_text = tk.Label(
            header, text="Építsd meg, aztán irány az utca!",
            font=("Arial", 13), bg="#1565C0", fg="#D8ECFF"
        )
        self.header_text.pack(side="left", padx=(22, 0))
        style_box = tk.Frame(header, bg="#1565C0")
        style_box.pack(side="right")
        tk.Label(
            style_box, text="AUTÓFORMA:", font=("Arial", 10, "bold"),
            bg="#1565C0", fg="white"
        ).pack(side="left", padx=(0, 7))
        style_menu = tk.OptionMenu(
            style_box, self.car_style, *CAR_STYLES,
            command=lambda _value: self._draw()
        )
        style_menu.configure(
            font=("Arial", 10, "bold"), bg=BRICK_YELLOW, fg=INK,
            activebackground="#FFE47A", relief="flat", width=13,
            highlightthickness=0, cursor="hand2"
        )
        style_menu["menu"].configure(font=("Arial", 10))
        style_menu.pack(side="left")

        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0, cursor="hand2")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._canvas_resized)
        self.canvas.bind("<Button-1>", self._mouse_down)
        self.canvas.bind("<B1-Motion>", self._mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._mouse_up)

        self.controls = tk.Frame(self, bg="white", padx=18, pady=11, height=74)
        self.controls.pack(fill="x")
        self.controls.pack_propagate(False)

        self.left_button = self._button("◀  BALRA", lambda: self._change_lane(-1), BRICK_YELLOW)
        self.right_button = self._button("JOBBRA  ▶", lambda: self._change_lane(1), BRICK_YELLOW)
        self.back_button = self._button("↻  ELÖLRŐL", self._reset_build, "#E1F0F8", size=11)
        self.back_button.pack(side="left")
        self.auto_button = self._button(
            "✨  KÖTELEZŐK ÖSSZERAKÁSA", self._auto_assemble, "#7E57C2", size=10
        )
        self.auto_button.configure(fg="white", activebackground="#9675D1", activeforeground="white")
        self.auto_button.pack(side="left", padx=(9, 0))

        self.status = tk.Label(
            self.controls, text="Húzd a építőkockákat a szaggatott helyükre!",
            font=("Arial", 12, "bold"), bg="white", fg=INK
        )
        self.status.pack(side="left", expand=True, padx=14)

        self.start_button = self._button("INDULÁS!  ➜", self._start_driving, "#B9C8D0", size=13)
        self.start_button.configure(state="disabled", disabledforeground="#EEF3F5")
        self.start_button.pack(side="right")

        self.bind("<Left>", lambda _event: self._change_lane(-1))
        self.bind("<Right>", lambda _event: self._change_lane(1))
        self.bind("<a>", lambda _event: self._change_lane(-1))
        self.bind("<d>", lambda _event: self._change_lane(1))

    def _button(self, text: str, command, color: str, size: int = 12) -> tk.Button:
        return tk.Button(
            self.controls, text=text, command=command, font=("Arial", size, "bold"),
            bg=color, fg=INK if color != BRICK_GREEN else "white", relief="flat",
            padx=18, pady=8, cursor="hand2"
        )

    def _car_center(self) -> float:
        width = max(900, self.canvas.winfo_width())
        return min(width - 330, width * 0.47)

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

    def _canvas_resized(self, _event=None) -> None:
        if self.mode == "build":
            height = max(1, self.canvas.winfo_height())
            for part in self.parts:
                if not part.placed and part is not self.dragged:
                    part.x = self._tray_x(part)
                    part.y = min(part.tray_y, height - part.height - 10)
        self._draw()

    def _reset_build(self) -> None:
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        self.mode = "build"
        self._cancel_math_timer()
        self.assembly_run += 1
        self.auto_assembling = False
        if self.math_popup and self.math_popup.winfo_exists():
            self.math_popup.destroy()
        self.math_popup = None
        self.math_active = False
        self.task_resolved = False
        self.dragged = None
        self.road_items.clear()
        for part in self.parts:
            part.placed = False
            part.x = self._tray_x(part)
            part.y = part.tray_y
        self.header_text.configure(text="Építsd meg, aztán irány az utca!")
        self.status.configure(text="Húzd a építőkockákat a szaggatott helyükre!", fg=INK)
        self.start_button.configure(state="disabled", bg="#B9C8D0")
        self.auto_button.configure(state="normal")
        self._show_build_controls()
        self._draw()

    def _show_build_controls(self) -> None:
        for widget in (self.left_button, self.right_button, self.back_button, self.auto_button, self.start_button, self.status):
            widget.pack_forget()
        self.back_button.configure(text="↻  ELÖLRŐL", command=self._reset_build)
        self.back_button.pack(side="left")
        self.auto_button.pack(side="left", padx=(9, 0))
        self.status.pack(side="left", expand=True, padx=14)
        self.start_button.pack(side="right")

    def _show_drive_controls(self) -> None:
        for widget in (self.left_button, self.right_button, self.back_button, self.auto_button, self.start_button, self.status):
            widget.pack_forget()
        self.back_button.configure(text="🔧  MŰHELY", command=self._reset_build)
        self.back_button.pack(side="left", padx=(0, 10))
        self.left_button.pack(side="left")
        self.status.pack(side="left", expand=True, padx=10)
        self.right_button.pack(side="right")

    def _draw(self) -> None:
        if self.mode == "build":
            self._draw_workshop()
        elif self.mode == "drive":
            self._draw_road()

    def _draw_workshop(self) -> None:
        self.canvas.delete("all")
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
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

    @staticmethod
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
    @staticmethod
    def _lighter(color: str) -> str:
        """Világosabb árnyalat az építőkocka bütykeihez."""
        if len(color) != 7 or not color.startswith("#"):
            return color
        red, green, blue = (int(color[i:i + 2], 16) for i in (1, 3, 5))
        red = min(255, red + 45)
        green = min(255, green + 45)
        blue = min(255, blue + 45)
        return f"#{red:02X}{green:02X}{blue:02X}"

    def _mouse_down(self, event) -> None:
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
        if self.mode == "build" and self.dragged:
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
        if self.mode != "build" or not self.dragged:
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
        if not all(part.placed for part in self.parts if part.required):
            return
        self.mode = "drive"
        self.lane, self.frame, self.score, self.lives = 1, 0, 0, 3
        self.speed_level, self.road_speed = 0, BASE_ROAD_SPEED
        self.speed_just_increased = False
        self.pending_bonus_challenges = 0
        self.road_items = []
        self.message, self.message_frames = "RAJT!", 45
        self.math_active = False
        self.header_text.configure(text="Gyűjts csillagokat, kerüld ki az akadályokat!")
        self._show_drive_controls()
        self._update_drive_status()
        self.focus_set()
        self._drive_tick()

    def _road_edges(self) -> tuple[float, float]:
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
        hearts = "♥" * self.lives + "♡" * (3 - self.lives)
        self.status.configure(
            text=f"★ {self.score}     |     {hearts}     |     Sebesség: {self.speed_level + 1}. fokozat"
        )

    def _add_stars(self, amount: int) -> bool:
        """Hozzáadja a jutalmat, és kezeli a 10 csillagos mérföldköveket."""
        old_score = self.score
        self.score += amount
        sped_up = False
        first_milestone = (old_score // 10 + 1) * 10
        for milestone in range(first_milestone, self.score + 1, 10):
            self.pending_bonus_challenges += 1
            self.speed_level += 1
            self.road_speed = BASE_ROAD_SPEED + self.speed_level * SPEED_STEP
            self.message = f"{milestone} CSILLAG! SEBESSÉGVÁLTÁS!"
            self.message_frames = 45
            sped_up = True
            self.speed_just_increased = True
        self._update_drive_status()
        return sped_up

    def _slow_down_after_collision(self) -> None:
        self.speed_just_increased = False
        if self.speed_level > 0:
            self.speed_level -= 1
            self.road_speed = BASE_ROAD_SPEED + self.speed_level * SPEED_STEP
            self.message = "ÜTKÖZÉS – EGY SEBESSÉGGEL LASSABB!"
        else:
            self.message = "ÜTKÖZÉS – MARAD AZ ALAPSEBESSÉG!"
        self.message_frames = 45
        self._update_drive_status()

    @staticmethod
    def _random_road_kind() -> str:
        roll = random.random()
        if roll < 0.52:
            return "star"
        if roll < 0.68:
            return "cone"
        if roll < 0.82:
            return "car"
        if roll < 0.92:
            return "bus"
        return "closure"

    def _drive_tick(self) -> None:
        if self.mode != "drive" or self.math_active:
            return
        self.frame += 1
        if self.frame % 48 == 0:
            occupied = {int(item["lane"]) for item in self.road_items if float(item["y"]) < 120}
            free_lanes = [lane for lane in range(4) if lane not in occupied] or [0, 1, 2, 3]
            self.road_items.append({
                "kind": self._random_road_kind(),
                "lane": random.choice(free_lanes), "y": -45.0,
            })

        car_y = self.canvas.winfo_height() - 128
        survivors = []
        hit_obstacle: str | None = None
        for item in self.road_items:
            item["y"] = float(item["y"]) + self.road_speed
            collision_distance = 72 if item["kind"] == "closure" else 54
            if (
                hit_obstacle is None
                and int(item["lane"]) == self.lane
                and abs(float(item["y"]) - car_y) < collision_distance
            ):
                if item["kind"] == "star":
                    sped_up = self._add_stars(1)
                    if not sped_up:
                        self.message, self.message_frames = "+1 CSILLAG!", 25
                    else:
                        # A gyorsulási üzenetet itt rögtön megjelenítjük.
                        self.speed_just_increased = False
                    self.bell()
                else:
                    hit_obstacle = str(item["kind"])
                    self._slow_down_after_collision()
                continue
            if float(item["y"]) < self.canvas.winfo_height() + 60:
                survivors.append(item)
        self.road_items = survivors
        if self.message_frames:
            self.message_frames -= 1

        self._update_drive_status()
        self._draw_road()
        if hit_obstacle:
            obstacle_names = {
                "cone": "A bója megállított.",
                "car": "Összekoccantál egy másik autóval.",
                "bus": "Túl közel kerültél a buszhoz.",
                "closure": "Behajtottál a lezárt sávba!",
            }
            task_count = 3 if hit_obstacle == "closure" else 1
            self._begin_math_challenge(
                count=task_count,
                reward=0,
                title="3 FELADATOS ÚTJAVÍTÁS" if task_count == 3 else "MATEK-SZERVIZ",
                reason=obstacle_names[hit_obstacle],
                is_collision=True,
                delay=250,
            )
        elif self.pending_bonus_challenges:
            self._start_pending_bonus(delay=180)
        elif self.lives <= 0:
            self.after(250, self._game_over)
        else:
            self.animation_job = self.after(32, self._drive_tick)

    def _begin_math_challenge(
        self,
        count: int,
        reward: int,
        title: str,
        reason: str,
        is_collision: bool,
        delay: int = 0,
    ) -> None:
        self.math_active = True
        self.animation_job = None
        self.challenge_tasks_left = count
        self.challenge_reward = reward
        self.challenge_title = title
        self.challenge_reason = reason
        self.challenge_is_collision = is_collision
        self.after(delay, self._show_math_task)

    def _start_pending_bonus(self, delay: int = 0) -> None:
        if self.pending_bonus_challenges <= 0:
            return
        self.pending_bonus_challenges -= 1
        self._begin_math_challenge(
            count=1,
            reward=2,
            title="10 CSILLAGOS BÓNUSZ!",
            reason="Elértél egy újabb 10 csillagos mérföldkövet!",
            is_collision=False,
            delay=delay,
        )

    def _show_math_task(self) -> None:
        """Megállítja a vezetést, és kattintható matekfeladatot mutat."""
        if self.mode != "drive" or not self.math_active:
            return
        self._cancel_math_timer()
        self.task_seconds_left = 60
        self.task_resolved = False
        task = self.math_tasks.next_task()
        self.current_math_task = task
        popup = tk.Toplevel(self)
        self.math_popup = popup
        popup.title(self.challenge_title.title())
        popup.geometry("510x430")
        popup.resizable(False, False)
        popup.configure(bg="#FFF7D1")
        popup.transient(self)
        popup.grab_set()
        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - popup.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - popup.winfo_height()) // 2
        popup.geometry(f"+{x}+{y}")

        tk.Label(
            popup, text=f"🔧  {self.challenge_title}",
            font=("Arial", 21, "bold"), bg="#FFF7D1", fg="#1565C0"
        ).pack(pady=(24, 5))
        progress_text = ""
        if self.challenge_tasks_left > 1 or self.challenge_title.startswith("3"):
            solved = 3 - self.challenge_tasks_left
            progress_text = f"  ({solved + 1}/3. feladat)"
        tk.Label(
            popup,
            text=f"{self.challenge_reason}{progress_text}\nRakd ki a hiányzó részt!",
            font=("Arial", 12), bg="#FFF7D1", fg=INK
        ).pack(pady=(0, 8))
        timer_label = tk.Label(
            popup, text="⏱  60 másodperc",
            font=("Arial", 14, "bold"), bg="#FFF7D1", fg="#26734D"
        )
        timer_label.pack(pady=(0, 8))
        tk.Label(
            popup, text=task.prompt,
            font=("Arial", 32, "bold"), bg="white", fg=INK,
            padx=30, pady=15, relief="solid", borderwidth=2
        ).pack()

        answers = tk.Frame(popup, bg="#FFF7D1")
        answers.pack(pady=20)
        feedback = tk.Label(
            popup, text="Kattints a helyes válaszra!",
            font=("Arial", 12, "bold"), bg="#FFF7D1", fg="#526D7A"
        )
        feedback.pack()
        buttons: list[tk.Button] = []
        for choice in task.choices:
            button = tk.Button(
                answers, text=choice, font=("Arial", 20, "bold"),
                bg="#4FA3F7", fg="white", activebackground="#75B8F8",
                activeforeground="white", relief="flat", width=4, pady=8,
                cursor="hand2"
            )
            button.configure(
                command=lambda value=choice, widget=button: self._check_math_answer(
                    value, widget, buttons, feedback, task, popup
                )
            )
            button.pack(side="left", padx=8)
            buttons.append(button)
        popup.protocol(
            "WM_DELETE_WINDOW",
            lambda: feedback.configure(text="Előbb válassz egy választ!", fg="#D14B3E")
        )
        self.task_timer_job = self.after(
            1000,
            lambda: self._tick_math_timer(popup, timer_label, buttons, feedback),
        )

    def _check_math_answer(
        self,
        choice: str,
        clicked: tk.Button,
        buttons: list[tk.Button],
        feedback: tk.Label,
        task: MathTask,
        popup: tk.Toplevel,
    ) -> None:
        if self.task_resolved:
            return
        if choice == task.answer:
            self.task_resolved = True
            self._cancel_math_timer()
            for button in buttons:
                button.configure(state="disabled")
            clicked.configure(bg=BRICK_GREEN, disabledforeground="white")
            if self.challenge_reward:
                self._add_stars(self.challenge_reward)
                reward_note = f"  +{self.challenge_reward} csillag!"
            else:
                reward_note = "  Nem vesztettél életet!"
            feedback.configure(
                text=f"Ügyes vagy!  {task.explanation}{reward_note}", fg="#238636"
            )
            self.bell()
            self.after(1000, lambda: self._finish_math_task(popup, success=True))
        else:
            clicked.configure(bg="#E55245")
            if self.challenge_is_collision:
                self._lose_life()
                feedback.configure(
                    text="Ez most nem jó: −1 élet. Próbáld meg újra!",
                    fg="#D14B3E",
                )
                if self.lives <= 0:
                    self.task_resolved = True
                    self._cancel_math_timer()
                    for button in buttons:
                        button.configure(state="disabled")
                    feedback.configure(text="Elfogytak az életek.", fg="#D14B3E")
                    self.after(900, lambda: self._finish_math_task(popup, success=False))
                    return
            else:
                feedback.configure(
                    text="Ez most nem jó. Próbáld meg még egyszer!", fg="#D14B3E"
                )
            self.after(
                550,
                lambda: clicked.configure(bg="#4FA3F7") if clicked.winfo_exists() else None
            )

    def _lose_life(self) -> None:
        self.lives = max(0, self.lives - 1)
        self._update_drive_status()

    def _cancel_math_timer(self) -> None:
        if self.task_timer_job:
            try:
                self.after_cancel(self.task_timer_job)
            except tk.TclError:
                pass
            self.task_timer_job = None

    def _tick_math_timer(
        self,
        popup: tk.Toplevel,
        timer_label: tk.Label,
        buttons: list[tk.Button],
        feedback: tk.Label,
    ) -> None:
        if self.task_resolved or not popup.winfo_exists():
            return
        self.task_seconds_left -= 1
        timer_label.configure(
            text=f"⏱  {self.task_seconds_left} másodperc",
            fg="#D14B3E" if self.task_seconds_left <= 10 else "#26734D",
        )
        if self.task_seconds_left > 0:
            self.task_timer_job = self.after(
                1000,
                lambda: self._tick_math_timer(popup, timer_label, buttons, feedback),
            )
            return

        self.task_resolved = True
        self.task_timer_job = None
        for button in buttons:
            button.configure(state="disabled")
        if self.challenge_is_collision:
            self._lose_life()
            feedback.configure(text="Lejárt az idő: −1 élet.", fg="#D14B3E")
        else:
            feedback.configure(text="Lejárt az idő, most nem jár bónuszcsillag.", fg="#D14B3E")
        self.after(1300, lambda: self._finish_math_task(popup, success=False))

    def _finish_math_task(self, popup: tk.Toplevel, success: bool) -> None:
        self._cancel_math_timer()
        if popup.winfo_exists():
            popup.grab_release()
            popup.destroy()
        self.math_popup = None
        if self.mode != "drive":
            return
        self.challenge_tasks_left -= 1
        if self.challenge_tasks_left > 0 and self.lives > 0:
            self.after(250, self._show_math_task)
            return

        self.math_active = False
        if self.speed_just_increased:
            reward_text = "10 CSILLAG! GYORSABB FOKOZAT!"
            self.speed_just_increased = False
        elif self.challenge_is_collision:
            reward_text = "HELYES! MEHETSZ TOVÁBB!" if success else "INDULÁS TOVÁBB!"
        else:
            reward_text = "+2 ★ BÓNUSZ!" if success else "A BÓNUSZ MOST NEM JÁRT"
        self.message, self.message_frames = reward_text, 40
        if self.lives <= 0:
            self.after(350, self._game_over)
        elif self.pending_bonus_challenges:
            self._start_pending_bonus(delay=250)
        else:
            self._drive_tick()

    def _draw_road(self) -> None:
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
            x, y = self._lane_x(int(item["lane"])), float(item["y"])
            kind = item["kind"]
            if kind == "star":
                self._draw_star(x, y, 27)
            elif kind == "cone":
                self._draw_cone(x, y)
            elif kind == "car":
                self._draw_other_car(x, y)
            elif kind == "bus":
                self._draw_bus(x, y)
            else:
                self._draw_lane_closure(x, y)
        self._draw_driving_car(self._lane_x(self.lane), height - 128)
        if self.message_frames:
            self.canvas.create_text(width / 2, 60, text=self.message, font=("Arial", 22, "bold"), fill="white")

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

    def _game_over(self) -> None:
        if self.mode != "drive":
            return
        self.mode = "stopped"
        popup = tk.Toplevel(self)
        popup.title("Menet vége")
        popup.geometry("440x285")
        popup.resizable(False, False)
        popup.configure(bg="#FFF5CC")
        popup.transient(self)
        popup.grab_set()
        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - popup.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - popup.winfo_height()) // 2
        popup.geometry(f"+{x}+{y}")
        tk.Label(popup, text="SZÉP VEZETÉS!", font=("Arial", 24, "bold"), bg="#FFF5CC", fg="#1565C0").pack(pady=(28, 8))
        tk.Label(popup, text=f"Összegyűjtöttél {self.score} csillagot! ★", font=("Arial", 15, "bold"), bg="#FFF5CC", fg=INK).pack(pady=8)
        tk.Button(
            popup, text="VEZETEK MÉG!", command=lambda: (popup.destroy(), self._start_driving()),
            font=("Arial", 12, "bold"), bg=BRICK_GREEN, fg="white", relief="flat", padx=20, pady=9, cursor="hand2"
        ).pack(pady=6)
        tk.Button(
            popup, text="VISSZA A MŰHELYBE", command=lambda: (popup.destroy(), self._reset_build()),
            font=("Arial", 10, "bold"), bg="#E1F0F8", fg=INK, relief="flat", padx=18, pady=7, cursor="hand2"
        ).pack(pady=3)


if __name__ == "__main__":
    TudasJarganyGame().mainloop()
