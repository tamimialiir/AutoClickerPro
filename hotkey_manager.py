"""
Global hotkey management for Auto Clicker Pro.
Handles background keyboard listening, re-binding, and shortcut dispatching.
"""

from typing import Callable, Dict, Optional
from pynput.keyboard import Key, Listener as KeyboardListener
from utils import key_to_str
from logger import get_logger

logger = get_logger("HotkeyManager")

class HotkeyManager:
    def __init__(self, is_focus_on_input: Callable[[], bool]):
        self.is_focus_on_input = is_focus_on_input

        # Configured hotkeys
        self.start_hotkey = "f1"
        self.pause_hotkey = "f2"
        self.stop_hotkey = "f3"
        self.record_start_hotkey = "f4"
        self.record_stop_hotkey = "f5"

        # Enabled flags
        self.start_enabled = True
        self.pause_enabled = True
        self.stop_enabled = True
        self.record_start_enabled = True
        self.record_stop_enabled = True

        # Callbacks
        self.on_start: Optional[Callable[[], None]] = None
        self.on_pause: Optional[Callable[[], None]] = None
        self.on_stop: Optional[Callable[[], None]] = None
        self.on_record_start: Optional[Callable[[], None]] = None
        self.on_record_stop: Optional[Callable[[], None]] = None

        # Re-binding state
        self.waiting_for_action: Optional[str] = None
        self.on_rebind_success: Optional[Callable[[str, str], None]] = None
        self.on_rebind_error: Optional[Callable[[str], None]] = None
        self.on_rebind_cancel: Optional[Callable[[], None]] = None

        self._listener: Optional[KeyboardListener] = None

    def start(self):
        """Start the background keyboard listener."""
        self.stop()
        logger.info("Starting global hotkey keyboard listener.")
        self._listener = KeyboardListener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        """Stop the background listener if active."""
        if self._listener:
            try:
                if hasattr(self._listener, "is_alive") and self._listener.is_alive():
                    self._listener.stop()
                    logger.info("Stopped global keyboard listener.")
            except Exception as e:
                logger.debug(f"Error stopping hotkey listener: {e}")
            finally:
                self._listener = None

    def start_rebind(
        self,
        action_name: str,
        on_success: Callable[[str, str], None],
        on_error: Callable[[str], None],
        on_cancel: Callable[[], None]
    ):
        """Put the hotkey manager into re-binding mode for an action."""
        self.waiting_for_action = action_name
        self.on_rebind_success = on_success
        self.on_rebind_error = on_error
        self.on_rebind_cancel = on_cancel
        logger.info(f"Awaiting new hotkey for action: {action_name}")

    def cancel_rebind(self):
        self.waiting_for_action = None
        if self.on_rebind_cancel:
            self.on_rebind_cancel()

    def get_all_hotkeys(self) -> Dict[str, str]:
        return {
            "start": self.start_hotkey,
            "pause": self.pause_hotkey,
            "stop": self.stop_hotkey,
            "record_start": self.record_start_hotkey,
            "record_stop": self.record_stop_hotkey,
        }

    def _on_press(self, key):
        try:
            kstr = key_to_str(key)
            if not kstr:
                return

            # Handling Re-binding mode
            if self.waiting_for_action:
                self._handle_rebind_press(key, kstr)
                return

            # Check if focus is on an active text input widget
            if self.is_focus_on_input():
                return

            # Dispatch configured shortcuts
            if self.start_enabled and kstr == self.start_hotkey:
                logger.debug("Start hotkey pressed.")
                if self.on_start:
                    self.on_start()
            elif self.pause_enabled and kstr == self.pause_hotkey:
                logger.debug("Pause hotkey pressed.")
                if self.on_pause:
                    self.on_pause()
            elif self.stop_enabled and kstr == self.stop_hotkey:
                logger.debug("Stop hotkey pressed.")
                if self.on_stop:
                    self.on_stop()
            elif self.record_start_enabled and kstr == self.record_start_hotkey:
                logger.debug("Record Start hotkey pressed.")
                if self.on_record_start:
                    self.on_record_start()
            elif self.record_stop_enabled and kstr == self.record_stop_hotkey:
                logger.debug("Record Stop hotkey pressed.")
                if self.on_record_stop:
                    self.on_record_stop()

        except Exception as e:
            logger.debug(f"Error handling key press: {e}")

    def _handle_rebind_press(self, key, kstr: str):
        if key == Key.esc:
            self.cancel_rebind()
            return

        if kstr in ("ctrl", "alt", "shift", "cmd"):
            return

        kstr_lower = kstr.lower().replace("key.", "").replace(" ", "_")
        is_media = (
            kstr_lower.startswith(("media_", "volume_", "brightness_", "launch_", "browser_"))
            or any(s in kstr_lower for s in (
                "volume_up", "volume_down", "volume_mute",
                "play_pause", "next_track", "prev_track", "stop_media",
                "media_play", "media_pause", "media_stop"
            ))
        )
        if is_media:
            if self.on_rebind_error:
                self.on_rebind_error("Media and system keys are not allowed!")
            self.waiting_for_action = None
            return

        # Check collision with existing hotkeys
        current_map = self.get_all_hotkeys()
        for act, existing_key in current_map.items():
            if act != self.waiting_for_action and existing_key == kstr:
                if self.on_rebind_error:
                    self.on_rebind_error(f"Key '{kstr.upper()}' is already used for {act.upper()}!")
                self.waiting_for_action = None
                return

        action = self.waiting_for_action
        self.waiting_for_action = None

        # Update key
        if action == "start":
            self.start_hotkey = kstr
        elif action == "pause":
            self.pause_hotkey = kstr
        elif action == "stop":
            self.stop_hotkey = kstr
        elif action == "record_start":
            self.record_start_hotkey = kstr
        elif action == "record_stop":
            self.record_stop_hotkey = kstr

        logger.info(f"Rebound hotkey for {action} to {kstr}")
        if self.on_rebind_success:
            self.on_rebind_success(action, kstr)
