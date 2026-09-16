"""A főalkalmazásból kiemelt, önálló felelősségű műveletek."""

from __future__ import annotations

import math
import random
import threading
import tkinter as tk
from tudasjargany.learning_tasks import LearningTask
from tudasjargany.app import BRICK_GREEN, INK, TASK_TIME_LIMIT
from tudasjargany.core.rules import lose_life, restore_life

class TaskDialogMixin:

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
                self.task_resolved = True
                self._cancel_math_timer()
                for button in buttons:
                    button.configure(state="disabled")
                clicked.configure(bg=BRICK_GREEN, disabledforeground="white")
                if self.challenge_life_reward:
                    if self.lives < 3:
                        self.lives = restore_life(self.lives)
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
            self.lives = lose_life(self.lives)
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
