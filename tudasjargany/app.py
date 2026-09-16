"""TudasJargany autóépítő és könnyű utcai vezetős játék gyerekeknek."""

from __future__ import annotations

import math
import random
import threading
from pathlib import Path
import tkinter as tk
from dataclasses import dataclass

try:
    import winsound
except ImportError:  # Nem Windows rendszeren a Tk csengője lesz a tartalék.
    winsound = None

from .learning_tasks import LearningTask
from .task_manager import TaskManager
from .services.audio import EnglishSpeaker


BG = "#EAF7FF"
INK = "#183153"
BRICK_RED = "#E53935"
BRICK_BLUE = "#1976D2"
BRICK_YELLOW = "#FFD43B"
BRICK_GREEN = "#35A853"
BASE_ROAD_SPEED = 6.5
SPEED_STEP = 1.6
TASK_TIME_LIMIT = 30
from tudasjargany.services.audio import AudioServiceMixin, SOUND_FILES

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
GAME_MODES = ("AUTÓS JÁTÉK", "HELIKOPTERES JÁTÉK", "KATA UNIKORNISA")
COLORING_ANIMALS = (
    "cica", "kutya", "nyuszi", "medve", "oroszlan", "elefant", "zsiraf", "zebra",
    "lo", "tehen", "malac", "roka", "pingvin", "teknos", "hal", "madar",
    "pillango", "bagoly", "majom", "beka",
)
COLORING_PAINT_TAGS = tuple(f"paint-{index}" for index in range(5))

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


from tudasjargany.gameplay.engine import GameplayEngineMixin
from tudasjargany.workshop.controller import WorkshopControllerMixin
from tudasjargany.ui.workshop_view import WorkshopViewMixin
from tudasjargany.ui.game_view import GameViewMixin
from tudasjargany.ui.task_dialog import TaskDialogMixin
from tudasjargany.core.state import GameState


class TudasJarganyGame(TaskDialogMixin, GameViewMixin, WorkshopViewMixin, WorkshopControllerMixin, GameplayEngineMixin, AudioServiceMixin, tk.Tk):
    def _state(self) -> GameState:
        if not hasattr(self, "game_state"):
            self.game_state = GameState()
        return self.game_state

    score = property(lambda self: self._state().score, lambda self, value: setattr(self._state(), "score", value))
    lives = property(lambda self: self._state().lives, lambda self, value: setattr(self._state(), "lives", value))
    speed_level = property(
        lambda self: self._state().speed_level,
        lambda self, value: setattr(self._state(), "speed_level", value),
    )

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
        self.resize_job: str | None = None
        self.layout_job: str | None = None
        self.canvas_width = 1
        self.canvas_height = 1
        self.last_drive_status: tuple[str, str, int] | None = None
        self.assembly_run = 0
        self.auto_assembling = False
        self.car_color = BRICK_RED
        self.car_style = tk.StringVar(value=CAR_STYLES[0])
        self.game_mode = tk.StringVar(value=GAME_MODES[0])
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
        self.pending_life_challenges = 0
        self.pending_coloring_challenges = 0
        self.coloring_active = False
        self.coloring_popup: tk.Toplevel | None = None
        self.last_coloring_animal: str | None = None
        self.message = ""
        self.message_frames = 0
        self.task_manager = TaskManager()
        self.subject_vars = {
            "MATEK": tk.BooleanVar(value=True),
            "ANGOL": tk.BooleanVar(value=False),
        }
        self.settings_popup: tk.Toplevel | None = None
        self.english_speaker = EnglishSpeaker()
        self.math_active = False
        self.math_popup: tk.Toplevel | None = None
        self.current_task: LearningTask | None = None
        # A korabbi nev megmarad, hogy a regi tesztek es kiegeszitok mukodjenek.
        self.current_math_task: LearningTask | None = None
        self.challenge_tasks_left = 0
        self.challenge_reward = 0
        self.challenge_title = "TUDÁS-SZERVIZ"
        self.challenge_reason = "Az akadály megállított. Válaszd ki a helyes választ!"
        self.challenge_is_collision = False
        self.challenge_life_reward = False
        self.challenge_life_granted = False
        self.task_timer_job: str | None = None
        self.task_seconds_left = TASK_TIME_LIMIT
        self.task_resolved = False
        self.speed_just_increased = False
        self.siren_running = False

        self._build_window()
        self.bind("<Configure>", self._window_resized, add="+")
        self.after(80, self._reset_build)


    def _build_window(self) -> None:
        header = tk.Frame(self, bg="#1565C0", padx=20, pady=12)
        header.pack(fill="x")
        self.title_label = tk.Label(
            header, text="TudasJargany", font=("Arial", 23, "bold"),
            bg="#1565C0", fg="white"
        )
        self.title_label.pack(side="left")
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

        game_box = tk.Frame(header, bg="#1565C0")
        game_box.pack(side="right", padx=(0, 16))
        tk.Label(
            game_box, text="JÁTÉK:", font=("Arial", 10, "bold"),
            bg="#1565C0", fg="white"
        ).pack(side="left", padx=(0, 7))
        game_menu = tk.OptionMenu(
            game_box, self.game_mode, *GAME_MODES,
            command=lambda _value: self._change_game_mode()
        )
        game_menu.configure(
            font=("Arial", 10, "bold"), bg="#78D2E8", fg=INK,
            activebackground="#A3E7F5", relief="flat", width=18,
            highlightthickness=0, cursor="hand2"
        )
        game_menu["menu"].configure(font=("Arial", 10))
        game_menu.pack(side="left")

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
        self.horn_button = self._button("📣  DUDÁLJ", self._honk, "#E1F0F8", size=10)
        self.back_button = self._button("↻  ELÖLRŐL", self._reset_build, "#E1F0F8", size=11)
        self.back_button.pack(side="left")
        self.auto_button = self._button(
            "✨  KÖTELEZŐK ÖSSZERAKÁSA", self._auto_assemble, "#7E57C2", size=10
        )
        self.auto_button.configure(fg="white", activebackground="#9675D1", activeforeground="white")
        self.auto_button.pack(side="left", padx=(9, 0))
        self.settings_button = self._button(
            "⚙  FELADATOK", self._show_task_settings, "#E1F0F8", size=10
        )
        self.settings_button.pack(side="left", padx=(9, 0))

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

    def _window_resized(self, event=None) -> None:
        """A feliratokat es gombokat az aktualis ablakszelesseghez igazitja."""
        if event is not None and event.widget is not self:
            return
        if self.layout_job is not None:
            self.after_cancel(self.layout_job)
        self.layout_job = self.after_idle(self._apply_responsive_layout)

    def _apply_responsive_layout(self) -> None:
        self.layout_job = None
        width = max(900, self.winfo_width())
        compact = width < 1080

        # Kis ablaknal a hosszu alcim helyet ad a valasztoknak. Maga a cim es
        # minden vezerlo tovabbra is lathato marad.
        if compact:
            self.header_text.pack_forget()
        elif not self.header_text.winfo_manager():
            self.header_text.pack(side="left", padx=(22, 0))

        self.auto_button.configure(
            text="✨  ÖSSZERAKÁS" if compact else "✨  KÖTELEZŐK ÖSSZERAKÁSA",
            padx=10 if compact else 18,
        )
        self.settings_button.configure(padx=10 if compact else 18)
        self.back_button.configure(padx=10 if compact else 18)
        self.start_button.configure(padx=12 if compact else 18)
        self.status.configure(
            font=("Arial", 10 if compact else 12, "bold"),
            wraplength=max(120, width - (610 if compact else 690)),
        )

    def _button(self, text: str, command, color: str, size: int = 12) -> tk.Button:
        return tk.Button(
            self.controls, text=text, command=command, font=("Arial", size, "bold"),
            bg=color, fg=INK if color != BRICK_GREEN else "white", relief="flat",
            padx=18, pady=8, cursor="hand2"
        )




    def _canvas_resized(self, event=None) -> None:
        """Elmenti az uj meretet, es egyetlen rajzolassa vonja ossze az esemenyeket."""
        self.canvas_width = max(
            1, int(event.width if event is not None else self.canvas.winfo_width())
        )
        self.canvas_height = max(
            1, int(event.height if event is not None else self.canvas.winfo_height())
        )
        if self.mode == "build":
            height = self.canvas_height
            for part in self.parts:
                if not part.placed and part is not self.dragged:
                    part.x = self._tray_x(part)
                    part.y = min(part.tray_y, height - part.height - 10)
        # Ablakatmeretezes kozben sok Configure esemeny erkezik egyszerre. A
        # korabbi kod mindegyiknel ujrarajzolta a teljes vasznat, ami akadozott.
        if self.resize_job is not None:
            self.after_cancel(self.resize_job)
        self.resize_job = self.after_idle(self._finish_canvas_resize)

    def _finish_canvas_resize(self) -> None:
        self.resize_job = None
        self._draw()

    def _reset_build(self) -> None:
        self._stop_siren()
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
        if self.coloring_popup and self.coloring_popup.winfo_exists():
            self.coloring_popup.destroy()
        self.coloring_popup = None
        self.coloring_active = False
        self.pending_coloring_challenges = 0
        if self.settings_popup and self.settings_popup.winfo_exists():
            self.settings_popup.destroy()
        self.settings_popup = None
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
        if self._is_special_game_mode():
            self._change_game_mode()
        else:
            self._show_build_controls()
            self._draw()

    def _is_helicopter_mode(self) -> bool:
        return self.game_mode.get() == "HELIKOPTERES JÁTÉK"

    def _is_unicorn_mode(self) -> bool:
        return self.game_mode.get() == "KATA UNIKORNISA"

    def _is_special_game_mode(self) -> bool:
        return self._is_helicopter_mode() or self._is_unicorn_mode()

    def _change_game_mode(self) -> None:
        if self.mode != "build":
            return
        self.dragged = None
        if self._is_helicopter_mode():
            self.auto_assembling = False
            self.auto_button.configure(state="disabled")
            self.start_button.configure(text="INDULÁS!  ➜", state="normal", bg=BRICK_GREEN, fg="white")
            self.header_text.configure(text="Helikopteres mentőrepülés indulásra kész!")
            self.status.configure(text="Válaszd az INDULÁS gombot a helikopterhez!", fg="#238636")
        elif self._is_unicorn_mode():
            self.auto_assembling = False
            self.auto_button.configure(state="disabled")
            self.start_button.configure(text="▶  JÁTÉK", state="normal", bg="#C75DCE", fg="white")
            self.header_text.configure(text="🦄 Kata unikornisa készen áll!")
            self.status.configure(text="⭐", fg="#C75DCE")
        else:
            ready = all(part.placed for part in self.parts if part.required)
            self.auto_button.configure(state="normal")
            self.start_button.configure(
                text="INDULÁS!  ➜",
                state="normal" if ready else "disabled",
                bg=BRICK_GREEN if ready else "#B9C8D0",
            )
            self.header_text.configure(text="Építsd meg, aztán irány az utca!")
            self.status.configure(text="Húzd a építőkockákat a szaggatott helyükre!", fg=INK)
        self._show_build_controls()
        self._draw_workshop()
    def _show_build_controls(self) -> None:
        for widget in (self.left_button, self.right_button, self.horn_button, self.back_button, self.auto_button, self.settings_button, self.start_button, self.status):
            widget.pack_forget()
        # A jobb oldali indulásgombot foglaljuk le elsőként. A pack így szűk
        # ablaknál sem engedi, hogy a középső állapotszöveg kitolja a képből.
        self.start_button.pack(side="right")
        self.back_button.configure(text="↻  ELÖLRŐL", command=self._reset_build)
        self.back_button.pack(side="left")
        if not self._is_special_game_mode():
            self.auto_button.pack(side="left", padx=(9, 0))
        if not self._is_unicorn_mode():
            self.settings_button.pack(side="left", padx=(9, 0))
        self.status.pack(side="left", expand=True, padx=14)
        self._apply_responsive_layout()
    def _show_task_settings(self) -> None:
        """A muhelyben valaszthato ki, mely tantargyakbol jojjenek feladatok."""
        if self.mode != "build":
            return
        if self.settings_popup and self.settings_popup.winfo_exists():
            self.settings_popup.lift()
            return

        popup = tk.Toplevel(self)
        self.settings_popup = popup
        popup.title("Feladatok be\u00e1ll\u00edt\u00e1sa")
        popup.geometry("440x330")
        popup.resizable(False, False)
        popup.configure(bg="#FFF7D1")
        popup.transient(self)
        popup.grab_set()

        tk.Label(
            popup, text="MELYIK FELADATOK J\u00d6JJENEK?",
            font=("Arial", 18, "bold"), bg="#FFF7D1", fg="#1565C0",
        ).pack(pady=(28, 8))
        tk.Label(
            popup, text="Jel\u00f6ld be a gyakorolni k\u00edv\u00e1nt tant\u00e1rgyakat!",
            font=("Arial", 12), bg="#FFF7D1", fg=INK, wraplength=390,
        ).pack(pady=(0, 14))
        choices = tk.Frame(popup, bg="#FFF7D1")
        choices.pack()
        for subject, detail in (
            ("MATEK", "\u00d6sszead\u00e1s \u00e9s kivon\u00e1s 30-as sz\u00e1mk\u00f6rben"),
            ("ANGOL", "Alap angol-magyar szavak kiejt\u00e9ssel"),
        ):
            tk.Checkbutton(
                choices, text=f"{subject} - {detail}", variable=self.subject_vars[subject],
                font=("Arial", 12, "bold"), bg="#FFF7D1", activebackground="#FFF7D1",
                fg=INK, selectcolor="white", anchor="w", cursor="hand2",
            ).pack(fill="x", pady=5)
        feedback = tk.Label(popup, text="", font=("Arial", 11, "bold"), bg="#FFF7D1")
        feedback.pack(pady=(11, 3))
        tk.Button(
            popup, text="MENT\u00c9S", command=lambda: self._save_task_settings(popup, feedback),
            font=("Arial", 12, "bold"), bg=BRICK_GREEN, fg="white",
            activebackground="#55C16B", activeforeground="white", relief="flat",
            padx=27, pady=8, cursor="hand2",
        ).pack(pady=(4, 14))
        popup.protocol("WM_DELETE_WINDOW", lambda: self._close_task_settings(popup))

    def _close_task_settings(self, popup: tk.Toplevel) -> None:
        popup.grab_release()
        popup.destroy()
        self.settings_popup = None

    def _save_task_settings(self, popup: tk.Toplevel, feedback: tk.Label) -> None:
        selected = tuple(
            subject for subject in TaskManager.AVAILABLE_SUBJECTS if self.subject_vars[subject].get()
        )
        if not selected:
            feedback.configure(text="V\u00e1lassz legal\u00e1bb egy tant\u00e1rgyat!", fg="#D14B3E")
            return
        self.task_manager = TaskManager(enabled_subjects=selected)
        selected_names = ", ".join(subject.title() for subject in selected)
        self.status.configure(text=f"Feladatok: {selected_names}", fg="#238636")
        self._close_task_settings(popup)

    def _show_drive_controls(self) -> None:
        for widget in (self.left_button, self.right_button, self.horn_button, self.back_button, self.auto_button, self.settings_button, self.start_button, self.status):
            widget.pack_forget()
        self.back_button.configure(text="🔧  MŰHELY", command=self._reset_build)
        self.back_button.pack(side="left", padx=(0, 10))
        if self._is_unicorn_mode():
            self.left_button.configure(text="◀", font=("Arial", 24, "bold"), padx=30)
            self.right_button.configure(text="▶", font=("Arial", 24, "bold"), padx=30)
        else:
            self.left_button.configure(text="◀  BALRA", font=("Arial", 12, "bold"), padx=18)
            self.right_button.configure(text="JOBBRA  ▶", font=("Arial", 12, "bold"), padx=18)
        self.left_button.pack(side="left")
        if not self._is_special_game_mode():
            self.horn_button.pack(side="left", padx=(8, 0))
        self.status.pack(side="left", expand=True, padx=10)
        self.right_button.pack(side="right")
        self._apply_responsive_layout()
























    def _start_coloring_challenge(self, delay: int = 0) -> None:
        if self.pending_coloring_challenges <= 0 or self.coloring_active:
            return
        self.pending_coloring_challenges -= 1
        self.coloring_active = True
        self.animation_job = None
        self.after(delay, self._show_coloring_challenge)

    def _show_coloring_challenge(self) -> None:
        if self.mode != "drive" or not self.coloring_active:
            return
        popup = tk.Toplevel(self)
        self.coloring_popup = popup
        popup.title("🎨")
        popup.resizable(False, False)
        popup.configure(bg="#F9D9F3")
        popup.transient(self)
        popup.grab_set()
        canvas = tk.Canvas(popup, width=620, height=450, bg="#CDEFFF", highlightthickness=0, cursor="hand2")
        canvas.pack()
        canvas.create_rectangle(0, 330, 620, 450, fill="#A8E6A3", outline="")
        self._draw_coloring_rainbow(canvas, 350, 18, 210, 155)
        animal = self._next_coloring_animal()
        self._draw_coloring_animal(canvas, animal, 310, 180)
        colors = ("#FF6FAB", "#FF9F43", "#FFD43B", "#58C97B", "#4CA6FF", "#A66CFF")
        selected = {"color": colors[0]}
        rings: dict[str, int] = {}
        for index, color in enumerate(colors):
            x = 92 + index * 87
            rings[color] = canvas.create_oval(x - 29, 365, x + 29, 423, fill=color, outline="" if index else "#263238", width=5, tags=("color", f"color-{index}"))

        painted: set[str] = set()

        def choose(color: str) -> None:
            selected["color"] = color
            for other_color, ring in rings.items():
                canvas.itemconfigure(ring, outline="#263238" if other_color == color else "")

        def paint(tag: str) -> None:
            canvas.itemconfigure(tag, fill=selected["color"])
            painted.add(tag)
            if len(painted) == 5:
                canvas.create_text(310, 280, text="⭐", font=("Arial", 52), fill="#FFD43B")
                self.after(650, lambda: self._finish_coloring_challenge(popup))

        for index, color in enumerate(colors):
            canvas.tag_bind(f"color-{index}", "<Button-1>", lambda _event, color=color: choose(color))
        for tag in COLORING_PAINT_TAGS:
            canvas.tag_bind(tag, "<Button-1>", lambda _event, tag=tag: paint(tag))
        popup.protocol("WM_DELETE_WINDOW", lambda: self._finish_coloring_challenge(popup, celebrate=False))

    def _next_coloring_animal(self) -> str:
        choices = tuple(animal for animal in COLORING_ANIMALS if animal != self.last_coloring_animal)
        animal = random.choice(choices)
        self.last_coloring_animal = animal
        return animal

    def _draw_coloring_animal(self, canvas: tk.Canvas, animal: str, x: float, y: float) -> None:
        tags = COLORING_PAINT_TAGS
        white, edge = "#FFFFFF", "#6F4A8E"

        def oval(x1: float, y1: float, x2: float, y2: float, tag: str) -> None:
            canvas.create_oval(x1, y1, x2, y2, fill=white, outline=edge, width=4, tags=tag)

        def polygon(points: tuple[float, ...], tag: str) -> None:
            canvas.create_polygon(points, fill=white, outline=edge, width=4, tags=tag)

        if animal == "pillango":
            oval(x - 120, y - 80, x - 8, y + 10, tags[0])
            oval(x - 110, y + 5, x - 8, y + 105, tags[1])
            oval(x + 8, y - 80, x + 120, y + 10, tags[2])
            oval(x + 8, y + 5, x + 110, y + 105, tags[3])
            oval(x - 14, y - 55, x + 14, y + 103, tags[4])
            canvas.create_line(x - 6, y - 55, x - 38, y - 82, fill=edge, width=3)
            canvas.create_line(x + 6, y - 55, x + 38, y - 82, fill=edge, width=3)
            return
        if animal == "hal":
            oval(x - 110, y - 48, x + 58, y + 62, tags[0])
            polygon((x + 45, y + 5, x + 132, y - 48, x + 132, y + 90), tags[1])
            polygon((x - 30, y - 30, x + 5, y - 85, x + 30, y - 20), tags[2])
            polygon((x - 30, y + 45, x + 5, y + 105, x + 30, y + 40), tags[3])
            oval(x - 82, y - 5, x - 45, y + 30, tags[4])
            canvas.create_oval(x - 72, y - 2, x - 61, y + 9, fill="#263238", outline="")
            return
        if animal == "teknos":
            oval(x - 110, y - 50, x + 82, y + 78, tags[0])
            oval(x + 62, y - 22, x + 124, y + 40, tags[1])
            oval(x - 82, y + 55, x - 30, y + 105, tags[2])
            oval(x + 25, y + 55, x + 77, y + 105, tags[3])
            polygon((x - 90, y - 5, x - 152, y - 45, x - 137, y + 42), tags[4])
            canvas.create_arc(x - 70, y - 20, x + 50, y + 55, start=10, extent=310, style="arc", outline=edge, width=3)
            return
        if animal in ("madar", "pingvin", "bagoly"):
            oval(x - 65, y - 55, x + 65, y + 105, tags[0])
            oval(x - 48, y - 120, x + 48, y - 22, tags[1])
            polygon((x - 60, y - 35, x - 140, y + 25, x - 58, y + 48), tags[2])
            polygon((x + 60, y - 35, x + 140, y + 25, x + 58, y + 48), tags[3])
            polygon((x - 20, y - 45, x, y - 12, x + 20, y - 45), tags[4])
            if animal == "pingvin":
                canvas.create_oval(x - 35, y - 18, x + 35, y + 82, fill="#F5F5F5", outline="")
            if animal == "bagoly":
                canvas.create_oval(x - 35, y - 88, x - 4, y - 56, fill="white", outline=edge, width=2)
                canvas.create_oval(x + 4, y - 88, x + 35, y - 56, fill="white", outline=edge, width=2)
            return
        if animal == "beka":
            oval(x - 110, y - 10, x + 110, y + 90, tags[0])
            oval(x - 78, y - 88, x - 3, y - 12, tags[1])
            oval(x + 3, y - 88, x + 78, y - 12, tags[2])
            polygon((x - 95, y + 42, x - 160, y + 95, x - 90, y + 92), tags[3])
            polygon((x + 95, y + 42, x + 160, y + 95, x + 90, y + 92), tags[4])
            canvas.create_oval(x - 52, y - 60, x - 36, y - 43, fill="#263238", outline="")
            canvas.create_oval(x + 36, y - 60, x + 52, y - 43, fill="#263238", outline="")
            return
        oval(x - 105, y - 25, x + 48, y + 85, tags[0])
        oval(x + 18, y - 92, x + 110, y - 4, tags[1])
        polygon((x + 25, y - 70, x + 30, y - 132, x + 62, y - 82), tags[2])
        polygon((x + 70, y - 82, x + 98, y - 132, x + 104, y - 70), tags[3])
        polygon((x - 83, y + 5, x - 155, y - 32, x - 127, y + 52), tags[4])
        canvas.create_line(x - 70, y + 78, x - 74, y + 120, fill=edge, width=10)
        canvas.create_line(x + 18, y + 78, x + 23, y + 120, fill=edge, width=10)
        canvas.create_oval(x + 80, y - 60, x + 91, y - 49, fill="#263238", outline="")
        if animal == "nyuszi":
            canvas.create_line(x + 45, y - 75, x + 40, y - 150, fill=edge, width=18)
            canvas.create_line(x + 82, y - 76, x + 93, y - 150, fill=edge, width=18)
        elif animal == "kutya":
            canvas.create_line(x + 35, y - 75, x - 5, y - 108, fill=edge, width=20)
            canvas.create_line(x + 90, y - 76, x + 130, y - 106, fill=edge, width=20)
        elif animal in ("medve", "majom"):
            canvas.create_oval(x + 16, y - 100, x + 58, y - 62, fill="white", outline=edge, width=4)
            canvas.create_oval(x + 70, y - 100, x + 111, y - 62, fill="white", outline=edge, width=4)
        elif animal == "elefant":
            canvas.create_oval(x - 14, y - 72, x + 44, y - 9, fill="white", outline=edge, width=4)
            canvas.create_line(x + 84, y - 20, x + 88, y + 75, fill=edge, width=20)
        elif animal == "zsiraf":
            canvas.create_line(x + 58, y - 80, x + 55, y - 150, fill=edge, width=12)
            canvas.create_line(x + 83, y - 80, x + 85, y - 150, fill=edge, width=12)
            for dx, dy in ((-48, 10), (-10, 45), (55, -50)):
                canvas.create_oval(x + dx, y + dy, x + dx + 22, y + dy + 18, fill="white", outline=edge, width=2)
        elif animal == "zebra":
            for stripe_x in range(-70, 35, 24):
                canvas.create_line(x + stripe_x, y - 15, x + stripe_x + 27, y + 70, fill=edge, width=5)
        elif animal == "lo":
            canvas.create_line(x + 25, y - 70, x - 8, y - 18, fill=edge, width=9)
        elif animal == "tehen":
            canvas.create_oval(x - 52, y - 2, x - 25, y + 24, fill="white", outline=edge, width=2)
            canvas.create_oval(x + 2, y + 34, x + 28, y + 58, fill="white", outline=edge, width=2)
        elif animal == "malac":
            canvas.create_oval(x + 50, y - 43, x + 88, y - 12, fill="white", outline=edge, width=2)
        elif animal == "oroszlan":
            canvas.create_oval(x - 3, y - 112, x + 130, y + 22, fill="", outline=edge, width=11)
        elif animal == "roka":
            canvas.create_polygon(x + 62, y - 36, x + 89, y - 10, x + 64, y + 10, fill="white", outline=edge, width=2)
    @staticmethod
    def _draw_coloring_rainbow(canvas: tk.Canvas, x: float, y: float, width: float, height: float) -> None:
        for index, color in enumerate(("#F45B69", "#FF9F43", "#FFD43B", "#5CCF80", "#4CA6FF", "#A66CFF")):
            inset = index * 10
            canvas.create_arc(x + inset, y + inset, x + width - inset, y + height - inset, start=0, extent=180, style="arc", outline=color, width=12)

    def _finish_coloring_challenge(self, popup: tk.Toplevel, celebrate: bool = True) -> None:
        if self.coloring_popup is popup:
            self.coloring_popup = None
        if popup.winfo_exists():
            popup.grab_release()
            popup.destroy()
        self.coloring_active = False
        if self.mode != "drive":
            return
        if celebrate:
            self._play_sound_effect("bonus_success")
            self.message, self.message_frames = "🎨 ⭐", 35
        self._drive_tick()

























    def _game_over(self) -> None:
        if self.mode != "drive":
            return
        self._stop_siren()
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
