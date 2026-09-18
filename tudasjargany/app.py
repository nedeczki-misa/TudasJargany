"""TudasJargany autóépítő és könnyű utcai vezetős játék gyerekeknek."""

from __future__ import annotations

import math
import random
import threading
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from dataclasses import dataclass

try:
    import winsound
except ImportError:  # Nem Windows rendszeren a Tk csengője lesz a tartalék.
    winsound = None

from .learning.tasks import LearningTask
from .learning.manager import TaskManager
from .services.speech import EnglishSpeaker
from .services.scoreboard import load_top_scores, save_result


BG = "#EAF7FF"
INK = "#183153"
BRICK_RED = "#E53935"
BRICK_BLUE = "#1976D2"
BRICK_YELLOW = "#FFD43B"
BRICK_GREEN = "#35A853"
BASE_ROAD_SPEED = 6.5
SPEED_STEP = 1.6
TASK_TIME_LIMIT = 30
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOUND_DIR = PROJECT_ROOT / "assets" / "sounds"
SOUND_FILES = {
    "engine_start": SOUND_DIR / "engine_start.wav",
    "speed_up": SOUND_DIR / "speed_up.wav",
    "brake_screech": SOUND_DIR / "brake_screech.wav",
    "collision_light": SOUND_DIR / "collision_light.wav",
    "collision_heavy": SOUND_DIR / "collision_heavy.wav",
    "bonus_success": SOUND_DIR / "bonus_success.wav",
    "horn": SOUND_DIR / "horn.wav",
    "siren_loop": SOUND_DIR / "siren_loop.wav",
    "star_pickup": SOUND_DIR / "star_pickup_retro.wav",
}

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
        self.game_started_at: float | None = None
        self.tasks_shown = 0
        self.tasks_correct = 0
        self.tasks_wrong = 0
        self.tasks_timed_out = 0
        self.highest_speed_level = 0
        self.result_saved = False
        self.speed_level = 0
        self.road_speed = BASE_ROAD_SPEED
        self.drive_paused = False
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
        self.bind("<space>", self._toggle_drive_pause)
        self.bind("<Up>", self._increase_drive_speed)
        self.bind("<Down>", self._decrease_drive_speed)
        self.bind("<w>", self._increase_drive_speed)
        self.bind("<s>", self._decrease_drive_speed)
        self.bind("<A>", lambda _event: self._change_lane(-1))
        self.bind("<D>", lambda _event: self._change_lane(1))
        self.bind("<W>", self._increase_drive_speed)
        self.bind("<S>", self._decrease_drive_speed)

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
        self.drive_paused = False
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
        self.mode = "drive"
        self.lane, self.frame, self.score, self.lives = 1, 0, 0, 3
        self.game_started_at = time.monotonic()
        self.tasks_shown = self.tasks_correct = self.tasks_wrong = self.tasks_timed_out = 0
        self.highest_speed_level = 0
        self.result_saved = False
        self.speed_level, self.road_speed = 0, BASE_ROAD_SPEED
        self.drive_paused = False
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

    def _toggle_drive_pause(self, _event=None) -> str:
        """A Space gombbal megállítja vagy folytatja a vezetést."""
        if self.mode != "drive" or self.math_active or self.coloring_active:
            return "break"
        self.drive_paused = not self.drive_paused
        if self.drive_paused:
            if self.animation_job:
                try:
                    self.after_cancel(self.animation_job)
                except tk.TclError:
                    pass
                self.animation_job = None
            self.message, self.message_frames = "SZÜNET – SPACE A FOLYTATÁSHOZ", 999999
            self._draw_road()
        else:
            self.message, self.message_frames = "MEHET!", 24
            self._drive_tick()
        return "break"

    def _increase_drive_speed(self, _event=None) -> str:
        return self._change_drive_speed(1)

    def _decrease_drive_speed(self, _event=None) -> str:
        return self._change_drive_speed(-1)

    def _change_drive_speed(self, change: int) -> str:
        """Kézzel állítja a sebességet; a -1. szint a teljes megállás."""
        if self.mode != "drive" or self.math_active or self.coloring_active:
            return "break"
        old_level = self.speed_level
        self.speed_level = max(-1, self.speed_level + change)
        if self.speed_level == old_level:
            return "break"
        self.road_speed = 0 if self.speed_level < 0 else BASE_ROAD_SPEED + self.speed_level * SPEED_STEP
        self.highest_speed_level = max(self.highest_speed_level, self.speed_level)
        self.speed_just_increased = False
        if self.road_speed == 0:
            self.message, self.message_frames = "MEGÁLLTÁL! ↑ VAGY W AZ INDULÁSHOZ", 999999
        elif change > 0:
            self.message, self.message_frames = "GYORSÍTÁS!", 24
            self._play_speed_up_sound()
        else:
            self.message, self.message_frames = "LASSÍTÁS!", 24
        self.last_drive_status = None
        self._update_drive_status()
        self._draw_road()
        return "break"

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
        if self._is_unicorn_mode():
            old_score = self.score
            self.score += amount
            first_milestone = (old_score // 10 + 1) * 10
            coloring_queued = False
            for milestone in range(first_milestone, self.score + 1, 10):
                self.pending_coloring_challenges += 1
                self.message = "🎨"
                self.message_frames = 45
                coloring_queued = True
            self._update_drive_status()
            return coloring_queued
        old_score = self.score
        self.score += amount
        sped_up = False
        first_milestone = (old_score // 10 + 1) * 10
        for milestone in range(first_milestone, self.score + 1, 10):
            if milestone % 30 == 0:
                self.pending_life_challenges += 1
                self.message = f"{milestone} PONT! ÉLETBÓNUSZ-FELADAT!"
            else:
                self.pending_bonus_challenges += 1
                self.message = f"{milestone} PONT! SEBESSÉGVÁLTÁS!"
            self.speed_level += 1
            self.highest_speed_level = max(self.highest_speed_level, self.speed_level)
            self.road_speed = BASE_ROAD_SPEED + self.speed_level * SPEED_STEP
            self.message_frames = 45
            sped_up = True
            self.speed_just_increased = True
        if sped_up:
            self._play_speed_up_sound()
        self._update_drive_status()
        return sped_up
    def _slow_down_after_collision(self, obstacle_kind: str) -> None:
        self._play_collision_sound(obstacle_kind)
        self.speed_just_increased = False
        if self.speed_level > 0:
            self.speed_level -= 1
            self.road_speed = BASE_ROAD_SPEED + self.speed_level * SPEED_STEP
            self.message = "ÜTKÖZÉS – EGY SEBESSÉGGEL LASSABB!"
        else:
            self.message = "ÜTKÖZÉS – MARAD AZ ALAPSEBESSÉG!"
        self.message_frames = 45
        self._update_drive_status()

    def _play_tones(self, tones: tuple[tuple[int, int], ...]) -> None:
        """Tartalek hangjelzes, ha egy hangfajl nem erheto el."""
        if winsound is None:
            self.bell()
            return

        def play() -> None:
            try:
                for frequency, duration in tones:
                    winsound.Beep(frequency, duration)
            except RuntimeError:
                winsound.MessageBeep()

        threading.Thread(target=play, daemon=True).start()

    def _play_sound_effect(self, name: str) -> None:
        sound_file = SOUND_FILES[name]
        if winsound is not None and sound_file.is_file():
            restart_siren = self.siren_running
            self.siren_running = False
            winsound.PlaySound(str(sound_file), winsound.SND_FILENAME | winsound.SND_ASYNC)
            if restart_siren:
                self.after(900, self._start_siren_loop)
            return
        fallback = {
            "speed_up": ((523, 70), (659, 70), (784, 120)),
            "collision_light": ((330, 100), (220, 180)),
            "collision_heavy": ((280, 130), (180, 210)),
            "bonus_success": ((659, 80), (784, 140)),
        }
        self._play_tones(fallback.get(name, ((523, 100),)))

    def _play_collision_sound(self, obstacle_kind: str) -> None:
        if obstacle_kind in ("cloud", "bird", "plane"):
            self._play_sound_effect("collision_light")
            return
        self._play_sound_effect("brake_screech")
        impact = "collision_light" if obstacle_kind == "cone" else "collision_heavy"
        self.after(170, lambda: self._play_sound_effect(impact))
    def _play_speed_up_sound(self) -> None:
        self._play_sound_effect("speed_up")

    def _honk(self) -> None:
        if self.mode == "drive" and not self.math_active and not self._is_helicopter_mode():
            self._play_sound_effect("horn")

    def _start_siren_loop(self) -> None:
        has_siren = any(part.kind == "siren" and part.placed for part in self.parts)
        sound_file = SOUND_FILES["siren_loop"]
        if self.mode == "drive" and not self._is_helicopter_mode() and not self.math_active and has_siren and winsound is not None and sound_file.is_file():
            winsound.PlaySound(str(sound_file), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            self.siren_running = True

    def _stop_siren(self) -> None:
        if self.siren_running and winsound is not None:
            winsound.PlaySound(None, 0)
        self.siren_running = False
    @staticmethod
    def _random_road_kind(helicopter: bool = False, unicorn: bool = False) -> str:
        roll = random.random()
        if unicorn:
            return "unicorn_star" if roll < 0.72 else "unicorn_dragon"
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
        if roll < 0.95:
            return "asphalt_paver"
        if roll < 0.97:
            return "truck"
        if roll < 0.99:
            return "dumper"
        return "closure"

    @staticmethod
    def _collision_distance(item: dict[str, float | int | str]) -> float:
        """Az akadály magasságához illő ütközési távolság."""
        if item["kind"] == "truck":
            return 280.0
        if item["kind"] in ("closure", "asphalt_paver", "dumper"):
            return 72.0
        return 54.0

    @staticmethod
    def _dumper_dirt_pile(lane: int) -> dict[str, float | int | str]:
        """A dömper után egy földkupac marad ugyanabban a sávban."""
        return {"kind": "dirt_pile", "lane": lane, "y": -150.0}

    @staticmethod
    def _road_item_lanes(item: dict[str, float | int | str]) -> tuple[int, ...]:
        """Megadja az akadály által elfoglalt sávokat."""
        first_lane = int(item["lane"])
        lane_span = int(item.get("lane_span", 1))
        return tuple(range(first_lane, min(4, first_lane + lane_span)))

    @staticmethod
    def _road_item_hits_lane(item: dict[str, float | int | str], lane: int) -> bool:
        if int(item.get("lane_span", 1)) > 1:
            return lane in TudasJarganyGame._road_item_lanes(item)
        return abs(float(item.get("lane_position", item["lane"])) - lane) < 0.43

    @staticmethod
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
        if self.mode != "drive" or self.math_active or self.coloring_active or self.drive_paused:
            return
        if self.road_speed <= 0:
            self.animation_job = self.after(80, self._drive_tick)
            return
        self.frame += 1
        spawn_interval = 32 if self._is_unicorn_mode() else 48
        if self.frame % spawn_interval == 0:
            occupied = {
                lane
                for item in self.road_items
                if float(item["y"]) < 120
                for lane in self._road_item_lanes(item)
            }
            free_lanes = [lane for lane in range(4) if lane not in occupied] or [0, 1, 2, 3]
            kind = self._random_road_kind(self._is_helicopter_mode(), self._is_unicorn_mode())
            if kind == "dumper":
                free_pairs = [lane for lane in range(3) if lane not in occupied and lane + 1 not in occupied]
                lane = random.choice(free_pairs or [0, 1, 2])
            else:
                lane = random.choice(free_lanes)
            item_y = -250.0 if kind == "truck" else -45.0
            item: dict[str, float | int | str] = {"kind": kind, "lane": lane, "y": item_y}
            if kind == "truck":
                item["vehicle_length"] = 440.0
            elif kind == "motorcycle":
                item["lane_position"] = float(lane)
                item["lane_direction"] = random.choice((-1.0, 1.0))
            elif kind == "dumper":
                item["lane_span"] = 2
                item["lane_position"] = lane + 0.5
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
            collision_distance = self._collision_distance(item)
            if (
                hit_obstacle is None
                and self._road_item_hits_lane(item, self.lane)
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
                elif item["kind"] == "unicorn_dragon":
                    self.message, self.message_frames = "🐉 KERÜLD KI A SÁRKÁNYT!", 35
                else:
                    hit_obstacle = str(item["kind"])
                    self._slow_down_after_collision(hit_obstacle)
                continue
            half_length = float(item.get("vehicle_length", 0.0)) / 2
            if float(item["y"]) < height + 60 + half_length:
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
                "truck": "Egy hosszú kamion elállta az utat!",
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
    def _begin_learning_challenge(
        self,
        count: int,
        reward: int,
        title: str,
        reason: str,
        is_collision: bool,
        life_reward: bool = False,
        delay: int = 0,
    ) -> None:
        if self._is_unicorn_mode():
            return
        self.math_active = True
        self._stop_siren()
        self.animation_job = None
        self.challenge_tasks_left = count
        self.challenge_reward = reward
        self.challenge_title = title
        self.challenge_reason = reason
        self.challenge_is_collision = is_collision
        self.challenge_life_reward = life_reward
        self.challenge_life_granted = False
        self.after(delay, self._show_learning_task)

    def _start_pending_life(self, delay: int = 0) -> None:
        if self.pending_life_challenges <= 0:
            return
        self.pending_life_challenges -= 1
        self._begin_learning_challenge(
            count=1,
            reward=0,
            title="30 PONTOS ÉLETBÓNUSZ!",
            reason="Oldd meg a feladatot, hogy visszakapj egy életet!",
            is_collision=False,
            life_reward=True,
            delay=delay,
        )
    def _start_pending_bonus(self, delay: int = 0) -> None:
        if self.pending_bonus_challenges <= 0:
            return
        self.pending_bonus_challenges -= 1
        self._begin_learning_challenge(
            count=1,
            reward=2,
            title="10 CSILLAGOS BÓNUSZ!",
            reason="Elértél egy újabb 10 csillagos mérföldkövet!",
            is_collision=False,
            delay=delay,
        )

    def _show_learning_task(self) -> None:
        """Megállítja a vezetést, és kattintható tanulási feladatot mutat."""
        if self.mode != "drive" or not self.math_active:
            return
        self._cancel_math_timer()
        self.task_seconds_left = TASK_TIME_LIMIT
        self.task_resolved = False
        task = self.task_manager.next_task()
        self.current_task = task
        self.current_math_task = task
        self.tasks_shown += 1
        task_title = f"{self.challenge_title} - {task.subject}"
        popup = tk.Toplevel(self)
        self.math_popup = popup
        popup.title(task_title.title())
        popup.geometry("510x470")
        popup.resizable(False, False)
        popup.configure(bg="#FFF7D1")
        popup.transient(self)
        popup.grab_set()
        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - popup.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - popup.winfo_height()) // 2
        popup.geometry(f"+{x}+{y}")

        tk.Label(
            popup, text=f"🔧  {task_title}",
            font=("Arial", 21, "bold"), bg="#FFF7D1", fg="#1565C0"
        ).pack(pady=(24, 5))
        progress_text = ""
        if self.challenge_tasks_left > 1 or self.challenge_title.startswith("3"):
            solved = 3 - self.challenge_tasks_left
            progress_text = f"  ({solved + 1}/3. feladat)"
        tk.Label(
            popup,
            text=f"{self.challenge_reason}{progress_text}\nVálaszd ki a helyes választ!",
            font=("Arial", 12), bg="#FFF7D1", fg=INK, wraplength=460,
        ).pack(pady=(0, 8))
        timer_label = tk.Label(
            popup, text=f"⏱  {TASK_TIME_LIMIT} másodperc",
            font=("Arial", 14, "bold"), bg="#FFF7D1", fg="#26734D"
        )
        timer_label.pack(pady=(0, 8))
        prompt_label = tk.Label(
            popup, text=task.prompt,
            font=("Arial", 32, "bold"), bg="white", fg=INK,
            padx=30, pady=15, relief="solid", borderwidth=2,
            wraplength=430, justify="center",
            cursor="hand2" if task.subject == "ANGOL" and not task.choices_in_english else "",
        )
        prompt_label.pack()
        if task.subject == "ANGOL":
            tk.Label(
                popup, text="Húzd az egeret az angol szó fölé a kiejtéshez!",
                font=("Arial", 11, "bold"), bg="#FFF7D1", fg="#526D7A",
            ).pack(pady=(5, 0))
            if task.pronunciation and not task.choices_in_english:
                prompt_label.bind(
                    "<Enter>",
                    lambda _event, word=task.pronunciation: self._speak_english_word(word),
                )

        answers = tk.Frame(popup, bg="#FFF7D1")
        answers.pack(pady=20)
        feedback = tk.Label(
            popup, text="Kattints a helyes válaszra!",
            font=("Arial", 12, "bold"), bg="#FFF7D1", fg="#526D7A",
            wraplength=460, justify="center",
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
                command=lambda value=choice, widget=button: self._check_learning_answer(
                    value, widget, buttons, feedback, task, popup
                )
            )
            button.pack(side="left", padx=8)
            buttons.append(button)
            if task.subject == "ANGOL" and task.choices_in_english:
                button.bind(
                    "<Enter>",
                    lambda _event, word=choice: self._speak_english_word(word),
                )
        popup.protocol(
            "WM_DELETE_WINDOW",
            lambda: feedback.configure(text="Előbb válassz egy választ!", fg="#D14B3E")
        )
        self.task_timer_job = self.after(
            1000,
            lambda: self._tick_task_timer(popup, timer_label, buttons, feedback),
        )

    def _speak_english_word(self, word: str | None) -> None:
        if word:
            self.english_speaker.speak(word)

    def _check_learning_answer(
        self,
        choice: str,
        clicked: tk.Button,
        buttons: list[tk.Button],
        feedback: tk.Label,
        task: LearningTask,
        popup: tk.Toplevel,
    ) -> None:
        if self.task_resolved:
            return
        if choice == task.answer:
            self.tasks_correct += 1
            self.task_resolved = True
            self._cancel_math_timer()
            for button in buttons:
                button.configure(state="disabled")
            clicked.configure(bg=BRICK_GREEN, disabledforeground="white")
            if self.challenge_life_reward:
                if self.lives < 3:
                    self.lives += 1
                    self.challenge_life_granted = True
                    reward_note = "  Visszakaptál egy életet!"
                else:
                    reward_note = "  Már mindhárom életed megvan!"
                self._update_drive_status()
            elif self.challenge_reward:
                self._add_stars(self.challenge_reward)
                reward_note = f"  +{self.challenge_reward} csillag!"
            else:
                reward_note = "  Nem vesztettél életet!"
            feedback.configure(
                text=f"Ügyes vagy!  {task.explanation}{reward_note}", fg="#238636"
            )
            self._play_sound_effect("bonus_success")
            self.after(1000, lambda: self._finish_learning_task(popup, success=True))
        else:
            self.tasks_wrong += 1
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
                    self.after(900, lambda: self._finish_learning_task(popup, success=False))
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

    def _tick_task_timer(
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
                lambda: self._tick_task_timer(popup, timer_label, buttons, feedback),
            )
            return

        self.task_resolved = True
        self.task_timer_job = None
        self.tasks_timed_out += 1
        for button in buttons:
            button.configure(state="disabled")
        if self.challenge_is_collision:
            self._lose_life()
            feedback.configure(text="Lejárt az idő: −1 élet.", fg="#D14B3E")
        elif self.challenge_life_reward:
            feedback.configure(text="Lejárt az idő, az élet most nem töltődött vissza.", fg="#D14B3E")
        else:
            feedback.configure(text="Lejárt az idő, most nem jár bónuszcsillag.", fg="#D14B3E")
        self.after(1300, lambda: self._finish_learning_task(popup, success=False))

    def _finish_learning_task(self, popup: tk.Toplevel, success: bool) -> None:
        self._cancel_math_timer()
        if popup.winfo_exists():
            popup.grab_release()
            popup.destroy()
        self.math_popup = None
        if self.mode != "drive":
            return
        self.challenge_tasks_left -= 1
        if self.challenge_tasks_left > 0 and self.lives > 0:
            self.after(250, self._show_learning_task)
            return

        self.math_active = False
        if self.challenge_life_reward:
            if self.challenge_life_granted:
                reward_text = "ÉLET VISSZATÖLTVE!"
            elif success:
                reward_text = "MÁR MINDHÁROM ÉLETED MEGVAN!"
            else:
                reward_text = "AZ ÉLET MOST NEM TÖLTŐDÖTT VISSZA"
            self.speed_just_increased = False
        elif self.speed_just_increased:
            reward_text = "10 PONT! GYORSABB FOKOZAT!"
            self.speed_just_increased = False
        elif self.challenge_is_collision:
            reward_text = "HELYES! MEHETSZ TOVÁBB!" if success else "INDULÁS TOVÁBB!"
        else:
            reward_text = "+2 ★ BÓNUSZ!" if success else "A BÓNUSZ MOST NEM JÁRT"
        self.message, self.message_frames = reward_text, 40
        if self.lives <= 0:
            self.after(350, self._game_over)
        elif self.pending_life_challenges:
            self._start_pending_life(delay=250)
        elif self.pending_bonus_challenges:
            self._start_pending_bonus(delay=250)
        else:
            self._start_siren_loop()
            self._drive_tick()

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
            elif kind == "truck":
                self._draw_truck(x, y)
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
            x, y = self._lane_x(float(item["lane"])), float(item["y"])
            if item["kind"] == "unicorn_star":
                self._draw_star(x, y, 30)
            elif item["kind"] == "unicorn_dragon":
                self._draw_unicorn_dragon(x, y)
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
        """Felülnézetes versenymotor sisakos vezetővel."""
        lean = 10 if direction > 0 else -10
        front_x = x - lean
        rear_x = x + lean

        # A két széles versenygumi és a motor váza.
        self.canvas.create_oval(front_x - 14, y - 58, front_x + 14, y - 25, fill="#151A1E", outline="#05080A", width=2)
        self.canvas.create_oval(rear_x - 16, y + 29, rear_x + 16, y + 63, fill="#151A1E", outline="#05080A", width=2)
        self.canvas.create_line(front_x, y - 35, rear_x, y + 43, fill="#B0BEC5", width=8)

        # Áramvonalas piros idom, szélvédő és első lámpák.
        self.canvas.create_polygon(
            front_x - 18, y - 31, front_x + 18, y - 31,
            x + 23, y - 5, rear_x + 20, y + 33,
            rear_x - 20, y + 33, x - 23, y - 5,
            fill="#E53935", outline="#751A1A", width=3,
        )
        self.canvas.create_polygon(
            front_x - 13, y - 28, front_x + 13, y - 28,
            x + 12, y - 13, x - 12, y - 13,
            fill="#BDEBFF", outline="#315C6A", width=2,
        )
        self.canvas.create_oval(front_x - 13, y - 22, front_x - 3, y - 12, fill="#FFF3A3", outline="")
        self.canvas.create_oval(front_x + 3, y - 22, front_x + 13, y - 12, fill="#FFF3A3", outline="")

        # A motoros teste, kezei a kormányon, és a fényes bukósisakja.
        self.canvas.create_oval(x - 17, y - 5, x + 17, y + 29, fill="#263238", outline="#101820", width=2)
        self.canvas.create_line(x - 17, y + 3, x - 31, y - 12, fill="#263238", width=7)
        self.canvas.create_line(x + 17, y + 3, x + 31, y - 12, fill="#263238", width=7)
        self.canvas.create_line(x - 35, y - 13, x + 35, y - 13, fill="#C7DDE7", width=4)
        self.canvas.create_oval(x - 16, y - 31, x + 16, y + 1, fill="#FFD23F", outline="#6D5100", width=2)
        self.canvas.create_arc(x - 13, y - 26, x + 13, y - 5, start=195, extent=150, style="arc", outline="#234A73", width=5)
        self.canvas.create_line(rear_x - 12, y + 44, rear_x + 12, y + 44, fill="#FF5252", width=5)
    def _draw_rainbow(self, x: float, y: float, width: float, height: float) -> None:
        for index, color in enumerate(("#F45B69", "#FF9F43", "#FFD43B", "#5CCF80", "#4CA6FF", "#A66CFF")):
            inset = index * 12
            self.canvas.create_arc(x + inset, y + inset, x + width - inset, y + height - inset, start=0, extent=180, style="arc", outline=color, width=14)

    def _draw_flower(self, x: float, y: float, color: str) -> None:
        for dx, dy in ((-10, 0), (10, 0), (0, -10), (0, 10)):
            self.canvas.create_oval(x + dx - 8, y + dy - 8, x + dx + 8, y + dy + 8, fill=color, outline="")
        self.canvas.create_oval(x - 7, y - 7, x + 7, y + 7, fill="#FFD43B", outline="#C88A00")
        self.canvas.create_line(x, y + 9, x, y + 35, fill="#3E9D56", width=4)

    def _draw_unicorn_dragon(self, x: float, y: float) -> None:
        """Kedves, felülnézetes sárkány Kata pályájára."""
        wing_flap = math.sin(self.frame * 0.25) * 8
        self.canvas.create_polygon(x - 18, y + 6, x - 72, y - 24 - wing_flap, x - 48, y + 34, fill="#B59AE8", outline="#6E52A3", width=2)
        self.canvas.create_polygon(x + 18, y + 6, x + 72, y - 24 + wing_flap, x + 48, y + 34, fill="#B59AE8", outline="#6E52A3", width=2)
        self.canvas.create_oval(x - 31, y - 35, x + 31, y + 47, fill="#65C96A", outline="#287D42", width=3)
        self.canvas.create_oval(x - 25, y - 66, x + 25, y - 18, fill="#7ADD7F", outline="#287D42", width=3)
        self.canvas.create_polygon(x - 17, y - 58, x - 24, y - 83, x - 4, y - 67, fill="#F4D35E", outline="#B88319", width=2)
        self.canvas.create_polygon(x + 17, y - 58, x + 24, y - 83, x + 4, y - 67, fill="#F4D35E", outline="#B88319", width=2)
        self.canvas.create_oval(x - 15, y - 51, x - 7, y - 43, fill="#263238", outline="")
        self.canvas.create_oval(x + 7, y - 51, x + 15, y - 43, fill="#263238", outline="")
        self.canvas.create_arc(x - 12, y - 43, x + 12, y - 25, start=205, extent=130, style="arc", outline="#B33D68", width=2)
        self.canvas.create_line(x - 16, y + 39, x - 47, y + 70, x - 26, y + 56, x - 5, y + 78, fill="#65C96A", width=10, smooth=True)
        self.canvas.create_oval(x - 20, y - 5, x + 20, y + 29, fill="#A7E4A9", outline="")
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

    def _draw_truck(self, x: float, y: float) -> None:
        """Négy személyautónyi hosszú, egy sávban haladó kamion."""
        self.canvas.create_rectangle(x - 46, y - 220, x + 46, y + 120, fill="#1976D2", outline="#0D3F74", width=3)
        self.canvas.create_rectangle(x - 36, y - 200, x + 36, y + 92, fill="#42A5F5", outline="#0D3F74", width=2)
        for cargo_y in (-168, -96, -24, 48):
            self.canvas.create_rectangle(x - 31, y + cargo_y, x + 31, y + cargo_y + 43, fill="#90CAF9", outline="#1565C0", width=2)
        self.canvas.create_rectangle(x - 46, y + 120, x + 46, y + 220, fill="#F57C00", outline="#713800", width=3)
        self.canvas.create_rectangle(x - 32, y + 133, x + 32, y + 168, fill="#BDEBFF", outline="#315C6A", width=2)
        self.canvas.create_text(x, y + 188, text="KAMION", font=("Arial", 9, "bold"), fill="#542600")
        for wheel_y in (-176, -84, 8, 100, 168, 211):
            self.canvas.create_oval(x - 55, y + wheel_y - 12, x - 37, y + wheel_y + 12, fill="#20262A", outline="#101418")
            self.canvas.create_oval(x + 37, y + wheel_y - 12, x + 55, y + wheel_y + 12, fill="#20262A", outline="#101418")
        self.canvas.create_rectangle(x - 33, y + 202, x - 13, y + 215, fill="#E53935", outline="")
        self.canvas.create_rectangle(x + 13, y + 202, x + 33, y + 215, fill="#E53935", outline="")

    def _draw_asphalt_paver(self, x: float, y: float) -> None:
        """Sárga aszfaltozó gép, amely elfoglal egy teljes sávot."""
        self.canvas.create_rectangle(x - 52, y - 55, x + 52, y + 52, fill="#F4B400", outline="#6D5200", width=3)
        self.canvas.create_rectangle(x - 31, y - 42, x + 31, y - 5, fill="#BDEBFF", outline="#315C6A", width=2)
        self.canvas.create_rectangle(x - 68, y + 25, x + 68, y + 62, fill="#455A64", outline="#263238", width=3)
        for wheel_x in (-38, 38):
            self.canvas.create_oval(x + wheel_x - 13, y + 36, x + wheel_x + 13, y + 62, fill="#20262A", outline="#101418")
        self.canvas.create_text(x, y + 10, text="ASZFALT", font=("Arial", 8, "bold"), fill="#3E2B00")

    def _draw_dumper(self, x: float, y: float) -> None:
        """Keresztben álló, két szomszédos sávot elfoglaló dömper."""
        self.canvas.create_rectangle(x - 112, y - 40, x + 54, y + 39, fill="#F57C00", outline="#6D3A00", width=3)
        self.canvas.create_polygon(
            x - 105, y - 34, x + 38, y - 34, x + 20, y + 10, x - 88, y + 10,
            fill="#8D5A3B", outline="#5D4037", width=2,
        )
        self.canvas.create_rectangle(x + 54, y - 29, x + 111, y + 39, fill="#FF9800", outline="#6D3A00", width=3)
        self.canvas.create_rectangle(x + 65, y - 20, x + 101, y + 8, fill="#BDEBFF", outline="#315C6A", width=2)
        for wheel_x in (-75, 15, 80):
            self.canvas.create_oval(
                x + wheel_x - 15, y + 25, x + wheel_x + 15, y + 55,
                fill="#20262A", outline="#101418", width=2,
            )
        self.canvas.create_text(x - 28, y + 24, text="DÖMPER", font=("Arial", 9, "bold"), fill="#FFF3D6")

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

    def _game_duration_seconds(self) -> int:
        if self.game_started_at is None:
            return 0
        return max(0, int(time.monotonic() - self.game_started_at))

    def _game_stats(self) -> dict[str, int]:
        return {
            "duration_seconds": self._game_duration_seconds(),
            "tasks_shown": self.tasks_shown,
            "tasks_correct": self.tasks_correct,
            "tasks_wrong": self.tasks_wrong,
            "tasks_timed_out": self.tasks_timed_out,
            "lives": self.lives,
            "top_speed": max(0, self.highest_speed_level + 1),
        }

    @staticmethod
    def _format_duration(seconds: int) -> str:
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes}:{seconds:02}"

    def _game_stats_text(self) -> str:
        stats = self._game_stats()
        return (
            f"Játékidő: {self._format_duration(stats['duration_seconds'])}    Életek: {stats['lives']}\n"
            f"Feladatok: {stats['tasks_shown']}    Helyes: {stats['tasks_correct']}    "
            f"Hibás: {stats['tasks_wrong']}    Lejárt: {stats['tasks_timed_out']}\n"
            f"Legnagyobb sebesség: {stats['top_speed']}. fokozat"
        )

    @staticmethod
    def _leaderboard_text(scores: list[dict]) -> str:
        if not scores:
            return "TOP 10\nMég nincs elmentett eredmény."
        lines = ["TOP 10"]
        for place, result in enumerate(scores, start=1):
            lines.append(
                f"{place}. {result['name']} — {result['stars']} ★  ({result['when']})"
            )
        return "\n".join(lines)

    def _save_game_result(
        self,
        name_entry: tk.Entry,
        save_button: tk.Button,
        feedback: tk.Label,
        leaderboard: tk.Label,
    ) -> None:
        if self.result_saved:
            return
        result = {
            "name": name_entry.get(),
            "stars": self.score,
            "when": datetime.now().strftime("%Y.%m.%d. %H:%M"),
            "mode": self.game_mode.get(),
            "stats": self._game_stats(),
        }
        try:
            scores = save_result(result)
        except OSError:
            feedback.configure(text="Most nem sikerült elmenteni. Próbáld újra!", fg="#D14B3E")
            return
        self.result_saved = True
        name_entry.configure(state="disabled")
        save_button.configure(state="disabled", text="ELMENTVE! ✓")
        feedback.configure(text="Szuper! Az eredményed bekerült a ranglistába.", fg="#238636")
        leaderboard.configure(text=self._leaderboard_text(scores))

    def _game_over(self) -> None:
        if self.mode != "drive":
            return
        self._stop_siren()
        self.mode = "stopped"
        popup = tk.Toplevel(self)
        popup.title("Menet vége")
        popup.geometry("620x650")
        popup.resizable(False, False)
        popup.configure(bg="#FFF5CC")
        popup.transient(self)
        popup.grab_set()
        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - popup.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - popup.winfo_height()) // 2
        popup.geometry(f"+{x}+{y}")

        tk.Label(
            popup, text="SZÉP VEZETÉS!", font=("Arial", 24, "bold"),
            bg="#FFF5CC", fg="#1565C0",
        ).pack(pady=(20, 6))
        tk.Label(
            popup, text=f"Összegyűjtöttél {self.score} csillagot! ★",
            font=("Arial", 16, "bold"), bg="#FFF5CC", fg=INK,
        ).pack(pady=4)
        tk.Label(
            popup, text=self._game_stats_text(), font=("Arial", 10, "bold"),
            bg="#FFF5CC", fg="#526D7A", justify="center",
        ).pack(pady=(4, 12))

        name_row = tk.Frame(popup, bg="#FFF5CC")
        name_row.pack()
        tk.Label(
            name_row, text="NEVED:", font=("Arial", 12, "bold"),
            bg="#FFF5CC", fg=INK,
        ).pack(side="left", padx=(0, 8))
        name_entry = tk.Entry(name_row, font=("Arial", 14, "bold"), width=18, justify="center")
        name_entry.pack(side="left")
        name_entry.focus_set()

        feedback = tk.Label(popup, text="Írd be a neved, majd mentsd el!", font=("Arial", 10, "bold"), bg="#FFF5CC", fg="#526D7A")
        feedback.pack(pady=(6, 2))
        leaderboard = tk.Label(
            popup, text=self._leaderboard_text(load_top_scores()),
            font=("Arial", 10, "bold"), bg="#FFFDF1", fg=INK,
            justify="left", anchor="w", width=56, height=11, padx=12, pady=7,
            relief="solid", borderwidth=2,
        )
        leaderboard.pack(padx=24, pady=4)

        save_button = tk.Button(
            popup, text="EREDMÉNY MENTÉSE", font=("Arial", 11, "bold"),
            bg="#1565C0", fg="white", relief="flat", padx=16, pady=7, cursor="hand2",
        )
        save_button.configure(
            command=lambda: self._save_game_result(name_entry, save_button, feedback, leaderboard)
        )
        save_button.pack(pady=(5, 3))
        name_entry.bind("<Return>", lambda _event: self._save_game_result(name_entry, save_button, feedback, leaderboard))

        tk.Button(
            popup, text="VEZETEK MÉG!", command=lambda: (popup.destroy(), self._start_driving()),
            font=("Arial", 12, "bold"), bg=BRICK_GREEN, fg="white", relief="flat", padx=20, pady=8, cursor="hand2",
        ).pack(pady=3)
        tk.Button(
            popup, text="VISSZA A MŰHELYBE", command=lambda: (popup.destroy(), self._reset_build()),
            font=("Arial", 10, "bold"), bg="#E1F0F8", fg=INK, relief="flat", padx=18, pady=6, cursor="hand2",
        ).pack(pady=2)

if __name__ == "__main__":
    TudasJarganyGame().mainloop()
