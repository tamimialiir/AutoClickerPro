"""
Actions execution engine for Auto Clicker Pro.
Simulates mouse and keyboard automation sequences with timing and position jitter.
"""

import time
import random
import threading
from tkinter import messagebox
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController
from utils import parse_key_combo, str_to_key
from theme import Theme
from widgets import show_click_ripple
from logger import get_logger

logger = get_logger("ActionsEngine")

class ActionsEngine:
    def __init__(self, app, mouse=None, keyboard=None):
        self.app = app
        self._mouse = mouse
        self._keyboard = keyboard

        self.is_running = False
        self.is_paused = False
        self.stop_flag = False
        self.current_cycle = 0
        self.current_step_index = 0

    @property
    def mouse(self):
        if self._mouse is None:
            self._mouse = MouseController()
        return self._mouse

    @mouse.setter
    def mouse(self, val):
        self._mouse = val

    @property
    def keyboard(self):
        if self._keyboard is None:
            self._keyboard = KeyboardController()
        return self._keyboard

    @keyboard.setter
    def keyboard(self, val):
        self._keyboard = val

    def apply_pos_random(self, x: int, y: int, pos_rand: int) -> tuple:
        """Apply random position jitter within [-pos_rand, +pos_rand] pixels."""
        if pos_rand <= 0:
            return x, y
        return x + random.randint(-pos_rand, pos_rand), y + random.randint(-pos_rand, pos_rand)

    def wait_if_paused(self) -> bool:
        """Block execution while paused; return True if sequence was aborted (stop_flag)."""
        while self.is_paused and not self.stop_flag:
            time.sleep(0.05)
        return self.stop_flag

    def get_speed_factor(self) -> float:
        """Retrieve current speed multiplier from app state."""
        try:
            v = float(self.app.speed_var.get())
            return max(0.1, min(20.0, v))
        except Exception as e:
            logger.debug(f"Error reading speed factor, using 1.0: {e}")
            return 1.0

    def interruptible_sleep(self, duration_ms: int):
        """Sleep in small intervals so stop/pause can react immediately. Respects global speed."""
        if duration_ms <= 0:
            return
        factor = self.get_speed_factor()
        scaled = duration_ms / factor
        end = time.time() + scaled / 1000.0
        while time.time() < end:
            if self.stop_flag:
                return
            if self.wait_if_paused():
                return
            remaining = end - time.time()
            time.sleep(min(0.05, max(0, remaining)))

    def perform_click(self, p, pos_rand: int):
        """Execute a mouse click action."""
        x, y = self.apply_pos_random(p.get("x", 0), p.get("y", 0), pos_rand)
        hold = p.get("hold", 50)
        typ = p.get("type", "Left")
        btn = {"Left": Button.left, "Right": Button.right, "Middle": Button.middle}.get(typ, Button.left)

        try:
            self.mouse.position = (x, y)

            if getattr(self.app, "show_ripple_var", None) and self.app.show_ripple_var.get():
                color = Theme.GREEN
                if typ == "Right":
                    color = Theme.BLUE
                elif typ == "Middle":
                    color = Theme.YELLOW
                elif typ == "Double":
                    color = Theme.PEACH
                self.app.root.after(0, lambda rx=x, ry=y, c=color: show_click_ripple(self.app.root, rx, ry, c))

            if typ == "Double":
                self.mouse.click(btn, 2)
            else:
                self.mouse.press(btn)
                self.interruptible_sleep(hold)
                self.mouse.release(btn)
        except Exception as e:
            logger.error(f"Error performing click ({x}, {y}, {typ}): {e}", exc_info=True)

    def perform_drag(self, p, pos_rand: int):
        """Execute a mouse drag action."""
        sx, sy = self.apply_pos_random(p.get("x", 0), p.get("y", 0), pos_rand)
        ex, ey = self.apply_pos_random(p.get("drag_x", 0), p.get("drag_y", 0), pos_rand)
        factor = self.get_speed_factor()
        duration = (p.get("hold", 300) / factor) / 1000.0

        try:
            self.mouse.position = (sx, sy)

            if getattr(self.app, "show_ripple_var", None) and self.app.show_ripple_var.get():
                self.app.root.after(0, lambda rx=sx, ry=sy: show_click_ripple(self.app.root, rx, ry, Theme.MAUVE))

            self.mouse.press(Button.left)
            steps = max(8, int(duration * 50))
            for i in range(1, steps + 1):
                if self.stop_flag or self.wait_if_paused():
                    break
                t = i / steps
                self.mouse.position = (sx + int((ex - sx) * t), sy + int((ey - sy) * t))
                time.sleep(duration / steps)
            self.mouse.release(Button.left)
        except Exception as e:
            logger.error(f"Error performing drag from ({sx},{sy}) to ({ex},{ey}): {e}", exc_info=True)

    def perform_key(self, p):
        """Execute a keyboard action."""
        key_str = p.get("key", "a")
        modifiers, main = parse_key_combo(key_str)
        main_obj = str_to_key(main)

        try:
            for mod in modifiers:
                self.keyboard.press(mod)
            try:
                self.keyboard.press(main_obj)
                self.keyboard.release(main_obj)
            except Exception as e:
                logger.debug(f"Direct key object press failed for {main}, falling back to char: {e}")
                self.keyboard.press(main)
                self.keyboard.release(main)
            for mod in reversed(modifiers):
                self.keyboard.release(mod)
        except Exception as e:
            logger.error(f"Failed to execute key combo '{key_str}': {e}", exc_info=True)

    def perform_scroll(self, p, pos_rand: int):
        """Execute a mouse scroll action."""
        x, y = self.apply_pos_random(p.get("x", 0), p.get("y", 0), pos_rand)
        try:
            self.mouse.position = (x, y)
            self.mouse.scroll(p.get("dx", 0), p.get("dy", 0))
        except Exception as e:
            logger.error(f"Error performing scroll at ({x},{y}): {e}", exc_info=True)

    def click_loop(self, random_ms: int, pos_rand: int, cycles: int):
        """Main background execution loop."""
        logger.info(f"Starting click loop: cycles={cycles}, random_ms={random_ms}, pos_rand={pos_rand}")
        cycle = 0
        max_cycles = float("inf") if self.app.infinite.get() else cycles

        while not self.stop_flag and cycle < max_cycles:
            self.current_cycle = cycle
            idx = 0
            while idx < len(self.app.points):
                if self.stop_flag or self.wait_if_paused():
                    break

                if idx >= len(self.app.points):
                    break

                p = self.app.points[idx]

                # Skip disabled (muted) action points
                if not p.get("enabled", True):
                    idx += 1
                    continue

                self.current_step_index = idx
                total_points = len(self.app.points)

                self.app.root.after(0, lambda i=idx: self.app.list_manager.highlight_current(i))

                # Calculate progress display
                if not self.app.infinite.get():
                    total_steps = total_points * max_cycles
                    current_step_num = cycle * total_points + idx + 1
                    pct = int((current_step_num / total_steps) * 100)
                    prog = f"Cycle {cycle + 1}/{max_cycles}  |  Step {idx + 1}/{total_points}  |  {pct}%"
                else:
                    prog = f"Cycle {cycle + 1}  |  Step {idx + 1}/{total_points}"

                self.app.root.after(0, lambda t=prog: self.app.progress_label.config(text=t))

                action = p.get("action")
                if action == "wait":
                    delay = p.get("delay", 500)
                    if random_ms > 0:
                        delay += random.randint(-random_ms, random_ms)
                    self.interruptible_sleep(max(0, delay))
                    idx += 1
                    continue

                count = p.get("count", 1)
                delay_between = p.get("delay_after", 0)

                runners = {
                    "drag": self.perform_drag,
                    "key": lambda pt, pr: self.perform_key(pt),
                    "scroll": self.perform_scroll,
                }
                runner = runners.get(action, self.perform_click)

                for i in range(count):
                    if self.stop_flag or self.wait_if_paused():
                        break

                    if idx >= len(self.app.points):
                        break
                    p = self.app.points[idx]
                    action = p.get("action")
                    if action == "wait":
                        break
                    else:
                        runner = runners.get(action, self.perform_click)
                        runner(p, pos_rand)

                    if i < count - 1 and delay_between > 0:
                        d = delay_between + (random.randint(-random_ms, random_ms) if random_ms > 0 else 0)
                        self.interruptible_sleep(max(0, d))

                idx += 1

            cycle += 1

        self.is_running = False
        self.is_paused = False
        self.app.root.after(0, self.on_clicking_finished)

    def start_clicking(self):
        """Start playing the action sequence."""
        if not self.app.points:
            messagebox.showwarning("Warning", "Add at least one point!")
            return
        if self.is_running or self.app.recorder_engine.is_recording:
            return

        self.is_running = True
        self.is_paused = False
        self.stop_flag = False
        self.current_cycle = 0
        self.current_step_index = 0

        self.app.set_ui_lock_state("running")
        self.app.status_label.config(text="Running...", fg=Theme.BLUE)
        self.app.progress_label.config(text="")

        random_ms = self.app.get_safe_int(self.app.random_var, 0, 0, 500)
        pos_rand = self.app.get_safe_int(self.app.pos_random_var, 0, 0, 50)
        cycles = self.app.get_safe_int(self.app.rep_var, 1, 1, 99999)

        threading.Thread(target=self.click_loop, args=(random_ms, pos_rand, cycles), daemon=True).start()

    def toggle_pause(self):
        """Toggle pause/resume during execution."""
        if not self.is_running:
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.app.set_ui_lock_state("paused")
            self.app.status_label.config(text="Paused — edit list freely, then Resume", fg=Theme.YELLOW)
            logger.info("Sequence paused.")
        else:
            self.app.set_ui_lock_state("running")
            self.app.status_label.config(text="Running...", fg=Theme.BLUE)
            logger.info("Sequence resumed.")

    def on_clicking_finished(self):
        """Callback invoked when execution finishes or is stopped."""
        self.app.set_ui_lock_state("stopped")
        self.app.list_manager.clear_highlight()
        self.app.status_label.config(text="Stopped", fg=Theme.RED)
        self.app.progress_label.config(text="")
        logger.info("Sequence execution finished.")

    def stop_clicking(self):
        """Signal execution loop to terminate."""
        self.stop_flag = True
        self.is_paused = False
        self.app.status_label.config(text="Stopping...", fg=Theme.YELLOW)
        logger.info("Stop requested by user.")
