"""
Auto Clicker Pro - Main Entry Point & Application Coordinator.
Orchestrates components using Composition (ActionsEngine, RecorderEngine, ListManager, ProfilesManager, HotkeyManager, GuiLayout).
"""

import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox

# Infrastructure
from utils import resource_path
from theme import Theme
from logger import setup_logging, get_logger
from models import ActionPoint
import system_utils
import updater
from hotkey_manager import HotkeyManager

# Components
import popups
import gui_components
from actions_engine import ActionsEngine
from recorder_engine import RecorderEngine
from list_manager import ListManager
from profiles_manager import ProfilesManager
from gui_layout import GuiLayout

logger = setup_logging()

class AutoClickerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Auto Clicker Pro")
        self.root.configure(bg=Theme.BASE)
        self.root.resizable(False, False)
        self.version = "v6.1"
        self.repo_slug = "tamimialiir/AutoClickerPro"
        self.github_url = f"https://github.com/{self.repo_slug}"

        # Application Icon
        try:
            icon_path = resource_path("icon.png")
            if os.path.exists(icon_path):
                self._app_icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, self._app_icon)
        except Exception as e:
            logger.debug(f"Could not set window icon: {e}")

        # Core State
        self.points = []
        self.preview_windows = []
        self.click_listener = None
        self.adding_mode = None
        self.temp_drag_start = None

        # Setting variables
        self.random_var = tk.IntVar(value=0)
        self.pos_random_var = tk.IntVar(value=0)
        self.rep_var = tk.IntVar(value=1)
        self.infinite = tk.BooleanVar(value=False)
        self.speed_var = tk.DoubleVar(value=1.0)
        self.always_on_top = tk.BooleanVar(value=False)

        self.g_hotkey_enabled = tk.BooleanVar(value=True)
        self.p_hotkey_enabled = tk.BooleanVar(value=True)
        self.s_hotkey_enabled = tk.BooleanVar(value=True)
        self.rs_hotkey_enabled = tk.BooleanVar(value=True)
        self.re_hotkey_enabled = tk.BooleanVar(value=True)
        self.show_ripple_var = tk.BooleanVar(value=True)

        # Initialize Subsystem Managers (Composition)
        self.hotkey_manager = HotkeyManager(is_focus_on_input=self.is_focus_on_input)
        self.actions_engine = ActionsEngine(app=self)
        self.recorder_engine = RecorderEngine(app=self)
        self.list_manager = ListManager(app=self)
        self.gui = GuiLayout(app=self)

        # Wire Hotkey Callbacks
        self._setup_hotkey_bindings()

        # Build UI & Listeners
        system_utils.force_english_keyboard()
        self.root.bind("<FocusIn>", lambda e: system_utils.force_english_keyboard())

        self.gui.setup_ui()
        self.list_manager.bind_list_shortcuts()
        self.hotkey_manager.start()

        # Center Window
        system_utils.center_window(self.root, width=540, offset_y=-30)
        logger.info("Auto Clicker Pro initialized successfully.")

    def _setup_hotkey_bindings(self):
        """Connect hotkey triggers to engine methods."""
        self.hotkey_manager.on_start = lambda: self.root.after(0, self.actions_engine.start_clicking)
        self.hotkey_manager.on_pause = lambda: self.root.after(0, self.actions_engine.toggle_pause)
        self.hotkey_manager.on_stop = lambda: self.root.after(0, self.actions_engine.stop_clicking)
        self.hotkey_manager.on_record_start = lambda: self.root.after(0, self.recorder_engine.start_recording)
        self.hotkey_manager.on_record_stop = lambda: self.root.after(0, lambda: self.recorder_engine.stop_recording(from_ui=False))

    # Convenience accessors to GUI widgets
    @property
    def status_label(self):
        return self.gui.status_label

    @property
    def progress_label(self):
        return self.gui.progress_label

    @property
    def edit_btn(self):
        return self.gui.edit_btn

    @property
    def record_btn(self):
        return self.gui.record_btn

    @property
    def start_btn(self):
        return self.gui.start_btn

    @property
    def pause_btn(self):
        return self.gui.pause_btn

    @property
    def stop_btn(self):
        return self.gui.stop_btn

    @property
    def exit_btn(self):
        return self.gui.exit_btn

    @property
    def points_listbox(self):
        return self.gui.points_listbox

    @property
    def selected_index(self):
        return self.list_manager.selected_index

    @selected_index.setter
    def selected_index(self, val):
        self.list_manager.selected_index = val

    @property
    def clipboard_point(self):
        return self.list_manager.clipboard_point

    @clipboard_point.setter
    def clipboard_point(self, val):
        self.list_manager.clipboard_point = val

    @property
    def is_running(self) -> bool:
        return self.actions_engine.is_running

    @property
    def is_paused(self) -> bool:
        return self.actions_engine.is_paused

    @property
    def is_recording(self) -> bool:
        return self.recorder_engine.is_recording

    # Delegation methods to GuiLayout
    def set_ui_lock_state(self, state_type: str):
        self.gui.set_ui_lock_state(state_type)

    def set_record_indicator(self, active: bool):
        self.gui.set_record_indicator(active)

    def _on_speed_change(self, value=None):
        self.gui._on_speed_change(value)

    # State checks
    def is_focus_on_input(self) -> bool:
        return system_utils.is_focus_on_input(self.root)

    def is_busy(self) -> bool:
        """True when actively running (not paused) or recording — blocks list edits."""
        return self.recorder_engine.is_recording or (
            self.actions_engine.is_running and not self.actions_engine.is_paused
        )

    def validate_number(self, action: str, value_if_allowed: str) -> bool:
        if action == "1":
            return value_if_allowed.isdigit() or value_if_allowed == ""
        return True

    def get_safe_int(self, var, default: int, min_val: int = 0, max_val: int = 999999) -> int:
        try:
            return max(min_val, min(int(var.get()), max_val))
        except Exception:
            return default

    def toggle_infinite(self):
        if self.gui.rep_spin:
            self.gui.rep_spin.config(state="disabled" if self.infinite.get() else "normal")

    def toggle_topmost(self):
        self.root.attributes("-topmost", self.always_on_top.get())

    # Profile Operations
    def save_profile(self):
        data = {
            "points": [p.to_dict() if hasattr(p, "to_dict") else p for p in self.points],
            "random": self.random_var.get(),
            "pos_random": self.pos_random_var.get(),
            "cycles": self.rep_var.get(),
            "infinite": self.infinite.get(),
            "speed": self.speed_var.get(),
            "start_hotkey": self.hotkey_manager.start_hotkey,
            "pause_hotkey": self.hotkey_manager.pause_hotkey,
            "stop_hotkey": self.hotkey_manager.stop_hotkey,
            "record_start_hotkey": self.hotkey_manager.record_start_hotkey,
            "record_stop_hotkey": self.hotkey_manager.record_stop_hotkey,
            "start_enabled": self.g_hotkey_enabled.get(),
            "pause_enabled": self.p_hotkey_enabled.get(),
            "stop_enabled": self.s_hotkey_enabled.get(),
            "record_start_enabled": self.rs_hotkey_enabled.get(),
            "record_stop_enabled": self.re_hotkey_enabled.get(),
            "always_on_top": self.always_on_top.get(),
            "show_ripple": self.show_ripple_var.get(),
        }
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Profile", "*.json")])
        if path:
            try:
                ProfilesManager.save_profile_to_file(path, data)
                self.status_label.config(text="Profile saved", fg=Theme.GREEN)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def load_profile(self):
        if self.is_busy():
            messagebox.showwarning("Warning", "Stop running or recording before loading a profile.")
            return
        path = filedialog.askopenfilename(filetypes=[("JSON Profile", "*.json")])
        if not path:
            return
        try:
            data = ProfilesManager.load_profile_from_file(path)
            self.points = data["points"]
            self.list_manager.refresh_points_list()

            self.random_var.set(data["random"])
            self.pos_random_var.set(data["pos_random"])
            self.rep_var.set(data["cycles"])
            self.infinite.set(data["infinite"])
            self.toggle_infinite()

            self.speed_var.set(data["speed"])
            self._on_speed_change()

            # Hotkeys
            self.hotkey_manager.start_hotkey = data["start_hotkey"]
            self.hotkey_manager.pause_hotkey = data["pause_hotkey"]
            self.hotkey_manager.stop_hotkey = data["stop_hotkey"]
            self.hotkey_manager.record_start_hotkey = data["record_start_hotkey"]
            self.hotkey_manager.record_stop_hotkey = data["record_stop_hotkey"]

            self.gui.start_hk_label.config(text=f"▶ Start: {self.hotkey_manager.start_hotkey.upper()}")
            self.gui.pause_hk_label.config(text=f"⏸ Pause: {self.hotkey_manager.pause_hotkey.upper()}")
            self.gui.stop_hk_label.config(text=f"⏹ Stop: {self.hotkey_manager.stop_hotkey.upper()}")
            self.gui.record_start_hk_label.config(text=f"⏺ Start Rec: {self.hotkey_manager.record_start_hotkey.upper()}")
            self.gui.record_stop_hk_label.config(text=f"⏹ Stop Rec: {self.hotkey_manager.record_stop_hotkey.upper()}")

            self.g_hotkey_enabled.set(data["start_enabled"])
            self.p_hotkey_enabled.set(data["pause_enabled"])
            self.s_hotkey_enabled.set(data["stop_enabled"])
            self.rs_hotkey_enabled.set(data["record_start_enabled"])
            self.re_hotkey_enabled.set(data["record_stop_enabled"])

            self.always_on_top.set(data["always_on_top"])
            self.toggle_topmost()

            self.show_ripple_var.set(data.get("show_ripple", True))

            self.list_manager.selected_index = None
            self.edit_btn.config(state="disabled")
            self.status_label.config(text="Profile loaded", fg=Theme.GREEN)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Hotkey Re-binding
    def change_hotkey(self, which: str):
        system_utils.force_english_keyboard()
        labels = {
            "start": "START", "pause": "PAUSE/RESUME", "stop": "STOP",
            "record_start": "START RECORD", "record_stop": "STOP RECORD"
        }
        self.status_label.config(text=f"Press a key for {labels.get(which, which.upper())}...", fg=Theme.YELLOW)

        def on_success(act: str, key_str: str):
            lbl_map = {
                "start": self.gui.start_hk_label,
                "pause": self.gui.pause_hk_label,
                "stop": self.gui.stop_hk_label,
                "record_start": self.gui.record_start_hk_label,
                "record_stop": self.gui.record_stop_hk_label,
            }
            prefixes = {
                "start": "▶ Start: ", "pause": "⏸ Pause: ", "stop": "⏹ Stop: ",
                "record_start": "⏺ Start Rec: ", "record_stop": "⏹ Stop Rec: "
            }
            if act in lbl_map and lbl_map[act]:
                lbl_map[act].config(text=f"{prefixes[act]}{key_str.upper()}")
            self.status_label.config(text=f"Hotkey → {key_str.upper()}", fg=Theme.GREEN)

        def on_error(err_msg: str):
            self.status_label.config(text=err_msg, fg=Theme.RED)

        def on_cancel():
            self.status_label.config(text="Cancelled", fg=Theme.YELLOW)

        self.hotkey_manager.start_rebind(
            action_name=which,
            on_success=lambda a, k: self.root.after(0, lambda: on_success(a, k)),
            on_error=lambda m: self.root.after(0, lambda: on_error(m)),
            on_cancel=lambda: self.root.after(0, on_cancel)
        )

    # Updates
    def check_for_update(self):
        self.status_label.config(text="Checking for updates...", fg=Theme.YELLOW)

        def on_found(latest_tag, releases_url):
            def show_dialog():
                msg = f"A new version is available!\n\nCurrent:  {self.version}\nLatest:   {latest_tag}"
                result = messagebox.askyesno("Update Available", msg + "\n\nOpen the Releases page to download?", parent=self.root)
                if result:
                    webbrowser.open(releases_url)
                self.status_label.config(text=f"Update available: {latest_tag}", fg=Theme.GREEN)
            self.root.after(0, show_dialog)

        def on_current():
            def show_dialog():
                messagebox.showinfo("Up to Date", f"You are using the latest version ({self.version}).", parent=self.root)
                self.status_label.config(text="You're up to date", fg=Theme.GREEN)
            self.root.after(0, show_dialog)

        def on_error(err):
            def show_dialog():
                messagebox.showwarning("Update Check Failed", f"Could not check for updates.\n\n{err}", parent=self.root)
                self.status_label.config(text="Update check failed", fg=Theme.RED)
            self.root.after(0, show_dialog)

        updater.check_for_updates_async(
            self.version, self.repo_slug, on_found, on_current, on_error
        )

    # Engine & List Manager delegations
    def refresh_points_list(self):
        self.list_manager.refresh_points_list()

    def select_index(self, index: int):
        self.list_manager.select_index(index)

    def highlight_current(self, index: int):
        self.list_manager.highlight_current(index)

    def clear_highlight(self):
        self.list_manager.clear_highlight()

    def move_up(self):
        self.list_manager.move_up()

    def move_down(self):
        self.list_manager.move_down()

    def remove_point(self):
        self.list_manager.remove_point()

    def clear_points(self):
        self.list_manager.clear_points()

    def start_clicking(self):
        self.actions_engine.start_clicking()

    def toggle_pause(self):
        self.actions_engine.toggle_pause()

    def stop_clicking(self):
        self.actions_engine.stop_clicking()

    def start_recording(self):
        self.recorder_engine.start_recording()

    def stop_recording(self, from_ui: bool = False):
        self.recorder_engine.stop_recording(from_ui)

    def toggle_recording(self):
        self.recorder_engine.toggle_recording()

    # Popups delegations
    def open_add_popup(self, action, data):
        popups.open_add_popup(self, action, data)

    def open_edit_popup(self):
        popups.open_edit_popup(self)

    def _open_edit_key_popup(self, p):
        popups._open_edit_key_popup(self, p)

    def add_wait(self):
        popups.add_wait(self)

    def start_add_scroll(self):
        popups.start_add_scroll(self)

    def add_scroll_action(self, preset=None):
        popups.add_scroll_action(self, preset)

    def add_key_action(self):
        popups.add_key_action(self)

    def minimize_for_capture(self):
        popups.minimize_for_capture(self)

    def restore_after_capture(self):
        popups.restore_after_capture(self)

    def start_add_point(self, mode):
        popups.start_add_point(self, mode)

    def finish_add_point_and_edit(self, action, data):
        popups.finish_add_point_and_edit(self, action, data)

    # Previews delegates
    def clear_previews(self):
        gui_components.clear_previews(self.preview_windows)

    def show_point_preview(self, x, y, color=Theme.RED, label=""):
        return gui_components.show_point_preview(self.root, self.preview_windows, x, y, color, label)

    def _move_preview(self, preview_win, x_var, y_var):
        gui_components.move_preview(preview_win, x_var, y_var)

    def make_preview_draggable(self, preview_win, x_var, y_var):
        gui_components.make_preview_draggable(preview_win, x_var, y_var)

    def exit_app(self):
        """Clean shutdown of application and listeners."""
        logger.info("Exiting application...")
        if self.click_listener and hasattr(self.click_listener, "is_alive") and self.click_listener.is_alive():
            try:
                self.click_listener.stop()
            except Exception as e:
                logger.debug(f"Error stopping click listener: {e}")
        self.actions_engine.stop_clicking()
        self.recorder_engine.stop_recording()
        self.hotkey_manager.stop()
        self.clear_previews()
        self.root.destroy()

# Backwards compatibility alias
AutoClicker = AutoClickerApp

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.exit_app)
    root.mainloop()
