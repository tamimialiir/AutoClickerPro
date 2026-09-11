"""
Event recorder engine for Auto Clicker Pro.
Captures real-time mouse and keyboard actions and converts them into editable macro points.
"""

import time
from tkinter import messagebox
from pynput import mouse
from pynput.mouse import Button
from pynput.keyboard import Listener as KeyboardListener
from utils import key_to_str
from theme import Theme
from models import ActionPoint
from logger import get_logger

logger = get_logger("RecorderEngine")

class RecorderEngine:
    def __init__(self, app):
        self.app = app
        self.is_recording = False
        self.record_events = []
        self.record_start_time = 0.0
        self.record_mouse_listener = None
        self.record_keyboard_listener = None

        self._rec_drag_start = None
        self._rec_last_time = 0.0
        self._rec_held_mods = set()

    def toggle_recording(self):
        """Toggle recording state."""
        if self.app.actions_engine.is_running:
            messagebox.showwarning("Warning", "Stop the running sequence first.")
            return
        if self.is_recording:
            self.stop_recording(from_ui=True)
        else:
            self.start_recording()

    def start_recording(self):
        """Begin capturing mouse and keyboard events."""
        if self.app.actions_engine.is_running or self.is_recording:
            return

        logger.info("Starting recording session.")
        self.is_recording = True
        self.record_events = []
        self.record_start_time = time.time()
        self._rec_last_time = self.record_start_time
        self._rec_drag_start = None
        self._rec_held_mods = set()

        self.app.set_record_indicator(True)
        try:
            self.app.set_ui_lock_state("recording")
        except Exception as e:
            logger.debug(f"Error updating UI lock state for recording: {e}")

        stop_hk = self.app.hotkey_manager.record_stop_hotkey.upper()
        self.app.status_label.config(text=f"Recording... Press {stop_hk} to stop", fg=Theme.RED)
        self.app.minimize_for_capture()

        for lst in (self.record_mouse_listener, self.record_keyboard_listener):
            if lst and getattr(lst, "is_alive", lambda: False)():
                try:
                    lst.stop()
                except Exception as e:
                    logger.debug(f"Error stopping prior listener: {e}")

        def rec_on_click(x, y, button, pressed):
            if not self.is_recording:
                return False
            now = time.time()
            delay_ms = int((now - self._rec_last_time) * 1000)
            self._rec_last_time = now
            btn_name = {Button.right: "Right", Button.middle: "Middle"}.get(button, "Left")

            if pressed:
                self._rec_drag_start = (x, y, btn_name, delay_ms)
            elif self._rec_drag_start:
                sx, sy, bname, dly = self._rec_drag_start
                if dly > 30:
                    self.record_events.append(ActionPoint(action="wait", delay=dly))
                if abs(x - sx) > 5 or abs(y - sy) > 5:
                    self.record_events.append(ActionPoint(
                        action="drag", x=sx, y=sy, drag_x=x, drag_y=y,
                        hold=750, count=1, delay_after=50, type="Left"
                    ))
                else:
                    self.record_events.append(ActionPoint(
                        action="click", x=sx, y=sy, hold=50,
                        count=1, delay_after=50, type=bname
                    ))
                self._rec_drag_start = None
            return True

        cx_val, cy_val = 0, 0
        def rec_on_scroll(x, y, dx, dy):
            if not self.is_recording:
                return False
            now = time.time()
            delay_ms = int((now - self._rec_last_time) * 1000)
            self._rec_last_time = now
            if delay_ms > 30:
                self.record_events.append(ActionPoint(action="wait", delay=delay_ms))
            if dy == 0:
                return True
            self.record_events.append(ActionPoint(
                action="scroll", x=cx_val, y=cy_val, dx=0, dy=int(dy),
                count=1, delay_after=30
            ))
            return True

        def rec_on_press(key):
            if not self.is_recording:
                return False
            kstr = key_to_str(key, self._rec_held_mods)
            if kstr == self.app.hotkey_manager.record_stop_hotkey:
                self.app.root.after(0, lambda: self.stop_recording(from_ui=False))
                return False
            if kstr in ("ctrl", "alt", "shift", "cmd"):
                self._rec_held_mods.add(kstr)
                return True
            now = time.time()
            delay_ms = int((now - self._rec_last_time) * 1000)
            self._rec_last_time = now
            if delay_ms > 30:
                self.record_events.append(ActionPoint(action="wait", delay=delay_ms))
            order = ["ctrl", "alt", "shift", "cmd"]
            mods = [m for m in order if m in self._rec_held_mods]
            combo = "+".join(mods + [kstr]) if mods else kstr
            self.record_events.append(ActionPoint(
                action="key", key=combo, count=1, delay_after=50
            ))
            return True

        def rec_on_release(key):
            if not self.is_recording:
                return False
            try:
                name = key_to_str(key)
                if name in ("ctrl", "alt", "shift", "cmd"):
                    self._rec_held_mods.discard(name)
            except Exception as e:
                logger.debug(f"Error handling key release in recorder: {e}")
            return True

        def track_move(x, y):
            nonlocal cx_val, cy_val
            cx_val, cy_val = x, y
            return True

        self.record_mouse_listener = mouse.Listener(
            on_click=rec_on_click, on_scroll=rec_on_scroll, on_move=track_move
        )
        self.record_mouse_listener.daemon = True
        self.record_mouse_listener.start()

        self.record_keyboard_listener = KeyboardListener(
            on_press=rec_on_press, on_release=rec_on_release
        )
        self.record_keyboard_listener.daemon = True
        self.record_keyboard_listener.start()

    def stop_recording(self, from_ui: bool = False):
        """Finish recording and append captured events to main points list."""
        self.is_recording = False
        for attr in ("record_mouse_listener", "record_keyboard_listener"):
            lst = getattr(self, attr)
            if lst:
                try:
                    if lst.is_alive():
                        lst.stop()
                except Exception as e:
                    logger.debug(f"Error stopping {attr}: {e}")
                setattr(self, attr, None)

        if from_ui:
            # User clicked Stop Rec button on the UI: remove the button click and pre-wait
            if self.record_events:
                last_click_idx = None
                for i in range(len(self.record_events) - 1, -1, -1):
                    if self.record_events[i].get("action") == "click":
                        last_click_idx = i
                        break
                if last_click_idx is not None:
                    self.record_events.pop(last_click_idx)
                    wait_idx = last_click_idx - 1
                    if wait_idx >= 0 and self.record_events[wait_idx].get("action") == "wait":
                        self.record_events.pop(wait_idx)
        else:
            # Stopped by global hotkey: pop the stop key event
            stop_key = self.app.hotkey_manager.record_stop_hotkey
            if self.record_events and self.record_events[-1].get("action") == "key":
                k_val = self.record_events[-1].get("key", "")
                if k_val == stop_key:
                    self.record_events.pop()

        # Pop any trailing wait
        if self.record_events and self.record_events[-1].get("action") == "wait":
            self.record_events.pop()

        count_before = len(self.app.points)
        self.app.points.extend(self.record_events)
        added = len(self.app.points) - count_before
        self.record_events = []

        self.app.list_manager.refresh_points_list()
        if self.app.points:
            self.app.list_manager.select_index(len(self.app.points) - 1)

        self.app.restore_after_capture()
        self.app.set_record_indicator(False)
        try:
            self.app.set_ui_lock_state("stopped")
        except Exception as e:
            logger.debug(f"Error setting UI lock state: {e}")

        self.app.status_label.config(text=f"Recording stopped — {added} actions added", fg=Theme.GREEN)
        logger.info(f"Recording stopped. Added {added} actions.")
