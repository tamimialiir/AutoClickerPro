"""
Graphical User Interface layout for Auto Clicker Pro.
Constructs widgets with Catppuccin Mocha theme, tooltips, and state management.
"""

import webbrowser
import tkinter as tk
from tkinter import ttk
from gui_components import ToolTip
from theme import Theme
from widgets import ToggleSwitch, ActionCardsView
from logger import get_logger

logger = get_logger("GuiLayout")

class GuiLayout:
    def __init__(self, app):
        self.app = app
        self.root = app.root

        # Widget references
        self.points_frame = None
        self.points_listbox = None
        self.global_frame = None
        self.hotkey_frame = None
        self.profile_frame = None

        self.record_btn = None
        self.edit_btn = None
        self.start_btn = None
        self.pause_btn = None
        self.stop_btn = None
        self.exit_btn = None

        self.speed_scale = None
        self.speed_value_label = None
        self.speed_reset_btn = None
        self.rep_spin = None

        self.status_label = None
        self.progress_label = None

        # Hotkey labels
        self.start_hk_label = None
        self.pause_hk_label = None
        self.stop_hk_label = None
        self.record_start_hk_label = None
        self.record_stop_hk_label = None

        self._rec_dot_idle = None
        self._rec_dot_active = None

    def _make_dot_image(self, color: str, size: int = 10) -> tk.PhotoImage:
        """Create a solid circle PhotoImage (works inside ttk.Button via compound)."""
        img = tk.PhotoImage(width=size, height=size)
        r = size // 2
        cx = cy = r
        for y in range(size):
            for x in range(size):
                if (x - cx + 0.5) ** 2 + (y - cy + 0.5) ** 2 <= (r - 0.2) ** 2:
                    img.put(color, (x, y))
        return img

    def set_record_indicator(self, active: bool):
        """Dot always visible inside the button: bright red when recording, dark red when idle."""
        if not self.record_btn:
            return
        img = self._rec_dot_active if active else self._rec_dot_idle
        self.record_btn.config(
            image=img,
            compound="left",
            text="Stop Rec" if active else "Record"
        )

    def _on_speed_change(self, value=None):
        try:
            v = float(self.app.speed_var.get())
            if self.speed_value_label:
                self.speed_value_label.config(text=f"x{v:.1f}")
        except Exception as e:
            logger.debug(f"Error updating speed label: {e}")

    def reset_speed(self):
        self.app.speed_var.set(1.0)
        self._on_speed_change()

    def set_speed_controls_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        try:
            if self.speed_scale:
                self.speed_scale.config(state=state)
            if self.speed_reset_btn:
                self.speed_reset_btn.config(state=state)
        except Exception as e:
            logger.debug(f"Error setting speed controls state: {e}")

    def _set_widgets_state(self, widget, state, exclude_widgets=None):
        if exclude_widgets is None:
            exclude_widgets = ()
        interactive_classes = (tk.Button, ttk.Button, tk.Scale, ttk.Spinbox, ttk.Checkbutton, tk.Listbox, ttk.Entry, tk.Entry)
        if isinstance(widget, interactive_classes):
            try:
                if widget not in exclude_widgets and widget not in (self.pause_btn, self.stop_btn, self.exit_btn):
                    widget.config(state=state)
            except Exception as e:
                logger.debug(f"Error changing widget state: {e}")
        elif hasattr(widget, "config_state"):
            try:
                if widget not in exclude_widgets:
                    widget.config_state(state)
            except Exception as e:
                logger.debug(f"Error changing custom widget state: {e}")
        for child in widget.winfo_children():
            self._set_widgets_state(child, state, exclude_widgets)

    def set_ui_lock_state(self, state_type: str):
        """Enable or disable UI controls depending on application state (running, paused, recording, stopped)."""
        if state_type == "running":
            self._set_widgets_state(self.global_frame, "disabled")
            self._set_widgets_state(self.hotkey_frame, "disabled")
            self._set_widgets_state(self.profile_frame, "disabled")
            self._set_widgets_state(self.points_frame, "disabled")

            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="normal", text="Pause")
            self.stop_btn.config(state="normal")
            self.exit_btn.config(state="normal")

        elif state_type == "paused":
            self._set_widgets_state(self.global_frame, "disabled")
            self._set_widgets_state(self.hotkey_frame, "disabled")
            self._set_widgets_state(self.profile_frame, "disabled")

            # Enable points sequence (allows editing during pause)
            self._set_widgets_state(self.points_frame, "normal")

            if self.app.list_manager.selected_index is None or self.app.list_manager.selected_index >= len(self.app.points):
                self.edit_btn.config(state="disabled")
            else:
                self.edit_btn.config(state="normal")

            self.speed_scale.config(state="normal")
            self.speed_reset_btn.config(state="normal")

            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="normal", text="Resume")
            self.stop_btn.config(state="normal")
            self.exit_btn.config(state="normal")

        elif state_type == "recording":
            self._set_widgets_state(self.global_frame, "disabled")
            self._set_widgets_state(self.hotkey_frame, "disabled")
            self._set_widgets_state(self.profile_frame, "disabled")
            self._set_widgets_state(self.points_frame, "disabled", exclude_widgets=(self.record_btn,))

            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")
            self.exit_btn.config(state="normal")
            self.record_btn.config(state="normal")

        elif state_type == "stopped":
            self._set_widgets_state(self.global_frame, "normal")
            self._set_widgets_state(self.hotkey_frame, "normal")
            self._set_widgets_state(self.profile_frame, "normal")
            self._set_widgets_state(self.points_frame, "normal")

            if self.app.list_manager.selected_index is None or self.app.list_manager.selected_index >= len(self.app.points):
                self.edit_btn.config(state="disabled")
            else:
                self.edit_btn.config(state="normal")

            self.start_btn.config(state="normal")
            self.pause_btn.config(state="disabled", text="Pause")
            self.stop_btn.config(state="disabled")
            self.exit_btn.config(state="normal")
            self.record_btn.config(state="normal")

    def setup_ui(self):
        """Construct the main GUI window layout."""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TCombobox",
            fieldbackground=Theme.SURFACE_0, background=Theme.SURFACE_0,
            foreground=Theme.TEXT, arrowcolor=Theme.TEXT,
            bordercolor=Theme.SURFACE_1, darkcolor=Theme.SURFACE_0, lightcolor=Theme.SURFACE_0,
            selectbackground=Theme.SURFACE_0, selectforeground=Theme.TEXT)

        style.map("TCombobox",
            fieldbackground=[("readonly", Theme.SURFACE_0), ("!disabled", Theme.SURFACE_0)],
            foreground=[("readonly", Theme.TEXT), ("!disabled", Theme.TEXT)],
            selectbackground=[("readonly", Theme.SURFACE_0)],
            selectforeground=[("readonly", Theme.TEXT)])

        style.configure("TButton", padding=3, font=Theme.FONT_MAIN)
        style.configure("TLabel", background=Theme.BASE, foreground=Theme.TEXT, font=Theme.FONT_MAIN)
        style.configure("TCheckbutton", background=Theme.BASE, foreground=Theme.TEXT, font=Theme.FONT_MAIN)
        style.configure("TSpinbox", fieldbackground=Theme.SURFACE_0, foreground=Theme.TEXT)
        style.configure("TLabelframe", background=Theme.BASE, foreground=Theme.BLUE)
        style.configure("TLabelframe.Label", background=Theme.BASE, foreground=Theme.BLUE, font=Theme.FONT_BOLD)
        style.configure("Hotkey.TButton", padding=(1, 1), font=(Theme.FONT_FAMILY, 7))
        style.configure("Hotkey.TCheckbutton", background=Theme.SURFACE_0, foreground=Theme.TEXT, font=Theme.FONT_SMALL)

        vcmd = (self.root.register(self.app.validate_number), "%d", "%P")

        tk.Label(self.root, text="Auto Clicker Pro", font=Theme.FONT_TITLE,
                 bg=Theme.BASE, fg=Theme.BLUE).pack(pady=(6, 3))

        # Points Sequence Frame (Action Cards)
        self.points_frame = ttk.LabelFrame(self.root, text=" Points Sequence", padding=5)
        self.points_frame.pack(fill="x", padx=10, pady=2)

        self.action_cards_view = ActionCardsView(
            self.points_frame,
            on_select=self.app.list_manager.select_index,
            on_edit=lambda idx: (self.app.list_manager.select_index(idx), self.app.open_edit_popup()),
            on_delete=self.app.list_manager.remove_point_at,
            on_reorder=self.app.list_manager.on_cards_reordered
        )
        self.action_cards_view.pack(fill="x", pady=(2, 4))
        self.points_listbox = self.action_cards_view  # Alias for compatibility
        ToolTip(self.action_cards_view, "Action sequence cards. Click to select, double-click to edit, toggle switch to mute/enable.")

        btn_row = tk.Frame(self.points_frame, bg=Theme.BASE)
        btn_row.pack(fill="x", pady=(4, 0))

        btn_add_click = ttk.Button(btn_row, text="Add Click", command=lambda: self.app.start_add_point("click"))
        btn_add_click.pack(side="left", expand=True, fill="x", padx=(0, 2))
        ToolTip(btn_add_click, "Capture a click point on screen")

        btn_add_drag = ttk.Button(btn_row, text="Add Drag", command=lambda: self.app.start_add_point("drag"))
        btn_add_drag.pack(side="left", expand=True, fill="x", padx=2)
        ToolTip(btn_add_drag, "Capture a drag action (press, move, release)")

        btn_add_scroll = ttk.Button(btn_row, text="Add Scroll", command=self.app.start_add_scroll)
        btn_add_scroll.pack(side="left", expand=True, fill="x", padx=2)
        ToolTip(btn_add_scroll, "Add a mouse scroll action at a chosen position")

        btn_add_key = ttk.Button(btn_row, text="Add Key", command=self.app.add_key_action)
        btn_add_key.pack(side="left", expand=True, fill="x", padx=2)
        ToolTip(btn_add_key, "Add a keyboard key or key combination")

        btn_add_wait = ttk.Button(btn_row, text="Add Wait", command=self.app.add_wait)
        btn_add_wait.pack(side="left", expand=True, fill="x", padx=(2, 0))
        ToolTip(btn_add_wait, "Add a timed delay (wait) step")

        btn_row2 = tk.Frame(self.points_frame, bg=Theme.BASE)
        btn_row2.pack(fill="x", pady=(3, 0))

        self._rec_dot_idle = self._make_dot_image("#5c1a1a", size=10)
        self._rec_dot_active = self._make_dot_image(Theme.RED, size=10)

        self.record_btn = ttk.Button(btn_row2, text="Record", command=self.app.recorder_engine.toggle_recording,
                                     image=self._rec_dot_idle, compound="left")
        self.record_btn.pack(side="left", expand=True, fill="x", padx=(0, 2))
        ToolTip(self.record_btn, "Start / stop recording mouse & keyboard actions")

        self.edit_btn = ttk.Button(btn_row2, text="Edit", command=self.app.open_edit_popup, state="disabled")
        self.edit_btn.pack(side="left", expand=True, fill="x", padx=2)
        ToolTip(self.edit_btn, "Edit the selected action (or double-click the list item)")

        btn_up = ttk.Button(btn_row2, text="↑", width=3, command=self.app.list_manager.move_up)
        btn_up.pack(side="left", padx=2)
        ToolTip(btn_up, "Move selected action up")

        btn_down = ttk.Button(btn_row2, text="↓", width=3, command=self.app.list_manager.move_down)
        btn_down.pack(side="left", padx=2)
        ToolTip(btn_down, "Move selected action down")

        btn_remove = ttk.Button(btn_row2, text="Remove", command=self.app.list_manager.remove_point)
        btn_remove.pack(side="left", expand=True, fill="x", padx=2)
        ToolTip(btn_remove, "Remove the selected action (Delete key)")

        btn_clear = ttk.Button(btn_row2, text="Clear", command=self.app.list_manager.clear_points)
        btn_clear.pack(side="left", expand=True, fill="x", padx=(2, 0))
        ToolTip(btn_clear, "Clear all actions from the list")

        # Global Settings Frame
        self.global_frame = ttk.LabelFrame(self.root, text=" Global Settings ", padding=8)
        self.global_frame.pack(fill="x", padx=10, pady=2)

        speed_row = tk.Frame(self.global_frame, bg=Theme.BASE)
        speed_row.pack(fill="x", pady=(0, 6))
        speed_box = tk.Frame(speed_row, bg=Theme.SURFACE_0, padx=8, pady=6)
        speed_box.pack(fill="x", expand=True)
        sp = tk.Frame(speed_box, bg=Theme.SURFACE_0)
        sp.pack(fill="x")

        tk.Label(sp, text="   Speed", bg=Theme.SURFACE_0, fg=Theme.SUBTEXT, font=Theme.FONT_SMALL).pack(side="left")
        self.speed_scale = tk.Scale(sp, from_=0.1, to=20.0, resolution=0.1, orient="horizontal",
                                    variable=self.app.speed_var, showvalue=0, bg=Theme.SURFACE_0, fg=Theme.TEXT,
                                    troughcolor=Theme.SURFACE_1, highlightthickness=0, activebackground=Theme.BLUE,
                                    command=self._on_speed_change)
        self.speed_scale.pack(side="left", padx=(10, 6), fill="x", expand=True)
        ToolTip(self.speed_scale, "Playback speed multiplier (0.1x – 20x). Higher = faster.")

        self.speed_value_label = tk.Label(sp, text="x1.0", bg=Theme.SURFACE_0, fg=Theme.BLUE,
                                          font=Theme.FONT_BOLD, width=6, anchor="w")
        self.speed_value_label.pack(side="left")

        self.speed_reset_btn = ttk.Button(sp, text="↺", width=3, command=self.reset_speed)
        self.speed_reset_btn.pack(side="left", padx=(4, 0))
        ToolTip(self.speed_reset_btn, "Reset speed to 1.0x")

        settings_grid = tk.Frame(self.global_frame, bg=Theme.BASE)
        settings_grid.pack(fill="x")
        settings_grid.columnconfigure(0, weight=1, uniform="g_col")
        settings_grid.columnconfigure(1, weight=1, uniform="g_col")

        # Row 0, Col 0: Time Jitter
        rand_box = tk.Frame(settings_grid, bg=Theme.SURFACE_0, padx=8, pady=6)
        rand_box.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=(0, 4))
        rt = tk.Frame(rand_box, bg=Theme.SURFACE_0)
        rt.pack(fill="x")
        tk.Label(rt, text="⏱  Time Jitter", bg=Theme.SURFACE_0, fg=Theme.SUBTEXT, font=Theme.FONT_SMALL).pack(side="left")
        spin_time_jitter = ttk.Spinbox(rt, from_=0, to=500, textvariable=self.app.random_var, width=5,
                                       validate="key", validatecommand=vcmd)
        spin_time_jitter.pack(side="left", padx=(8, 0))
        ToolTip(spin_time_jitter, "Randomize delays by ± this many milliseconds (human-like timing)")
        tk.Label(rt, text="±ms", bg=Theme.SURFACE_0, fg=Theme.OVERLAY, font=Theme.FONT_SMALL).pack(side="left", padx=(2, 0))

        # Row 0, Col 1: Pos. Jitter
        pos_box = tk.Frame(settings_grid, bg=Theme.SURFACE_0, padx=8, pady=6)
        pos_box.grid(row=0, column=1, sticky="nsew", padx=(2, 0), pady=(0, 4))
        rp = tk.Frame(pos_box, bg=Theme.SURFACE_0)
        rp.pack(fill="x")
        tk.Label(rp, text=" Pos. Jitter     ", bg=Theme.SURFACE_0, fg=Theme.SUBTEXT, font=Theme.FONT_SMALL).pack(side="left")
        spin_pos_jitter = ttk.Spinbox(rp, from_=0, to=50, textvariable=self.app.pos_random_var, width=5,
                                      validate="key", validatecommand=vcmd)
        spin_pos_jitter.pack(side="left", padx=(8, 0))
        ToolTip(spin_pos_jitter, "Randomize click/drag positions by ± this many pixels")
        tk.Label(rp, text="±px", bg=Theme.SURFACE_0, fg=Theme.OVERLAY, font=Theme.FONT_SMALL).pack(side="left", padx=(2, 0))

        # Row 1, Col 0: Cycles & Infinite
        cyc_box = tk.Frame(settings_grid, bg=Theme.SURFACE_0, padx=8, pady=6)
        cyc_box.grid(row=1, column=0, sticky="nsew", padx=(0, 2), pady=0)
        cy = tk.Frame(cyc_box, bg=Theme.SURFACE_0)
        cy.pack(fill="x")
        tk.Label(cy, text=" Cycles", bg=Theme.SURFACE_0, fg=Theme.SUBTEXT, font=Theme.FONT_SMALL).pack(side="left")
        self.rep_spin = ttk.Spinbox(cy, from_=1, to=99999, textvariable=self.app.rep_var, width=5,
                                    validate="key", validatecommand=vcmd)
        self.rep_spin.pack(side="left", padx=(8, 0))
        ToolTip(self.rep_spin, "Number of times to repeat the entire sequence")

        # Modern ToggleSwitch for Infinite
        sw_inf = ToggleSwitch(cy, variable=self.app.infinite, command=self.app.toggle_infinite,
                              width=32, height=16, bg=Theme.SURFACE_0)
        sw_inf.pack(side="left", padx=(10, 4))
        lbl_inf = tk.Label(cy, text="Infinite", bg=Theme.SURFACE_0, fg=Theme.TEXT, font=Theme.FONT_SMALL, cursor="hand2")
        lbl_inf.pack(side="left")
        lbl_inf.bind("<Button-1>", lambda e: sw_inf._on_click())
        ToolTip(sw_inf, "Repeat the sequence forever until Stop is pressed")
        ToolTip(lbl_inf, "Repeat the sequence forever until Stop is pressed")

        # Row 1, Col 1: Options (Always on Top)
        opt_box = tk.Frame(settings_grid, bg=Theme.SURFACE_0, padx=8, pady=6)
        opt_box.grid(row=1, column=1, sticky="nsew", padx=(2, 0), pady=0)
        op = tk.Frame(opt_box, bg=Theme.SURFACE_0)
        op.pack(fill="x")
        tk.Label(op, text="⚙  Options ", bg=Theme.SURFACE_0, fg=Theme.SUBTEXT, font=Theme.FONT_SMALL).pack(side="left")

        # Always on top ToggleSwitch
        sw_top = ToggleSwitch(op, variable=self.app.always_on_top, command=self.app.toggle_topmost,
                              width=32, height=16, bg=Theme.SURFACE_0)
        sw_top.pack(side="left", padx=(8, 4))
        lbl_top = tk.Label(op, text="Always on Top", bg=Theme.SURFACE_0, fg=Theme.TEXT, font=Theme.FONT_SMALL, cursor="hand2")
        lbl_top.pack(side="left")
        lbl_top.bind("<Button-1>", lambda e: sw_top._on_click())
        ToolTip(sw_top, "Keep the Auto Clicker Pro window above all other windows")
        ToolTip(lbl_top, "Keep the Auto Clicker Pro window above all other windows")

        # Hotkeys Frame
        self.hotkey_frame = ttk.LabelFrame(self.root, text=" Hotkeys ", padding=8)
        self.hotkey_frame.pack(fill="x", padx=10, pady=2)

        def make_hk_box(parent, label_attr, text, which, enabled_var, col, tip_change, tip_on):
            box = tk.Frame(parent, bg=Theme.SURFACE_0, padx=4, pady=3)
            box.grid(row=0, column=col, sticky="nsew", padx=2)
            inner = tk.Frame(box, bg=Theme.SURFACE_0)
            inner.pack(fill="x")

            # Pack RIGHT controls first so they are never clipped or overlapped
            btn_change = ttk.Button(inner, text="Change", style="Hotkey.TButton",
                                    command=lambda w=which: self.app.change_hotkey(w))
            btn_change.pack(side="right", padx=(2, 0))
            ToolTip(btn_change, tip_change)

            sw_on = ToggleSwitch(inner, variable=enabled_var, width=26, height=14, bg=Theme.SURFACE_0)
            sw_on.pack(side="right", padx=(2, 3))
            ToolTip(sw_on, tip_on)

            # Pack LEFT label last so it occupies remaining space smoothly
            lbl = tk.Label(inner, text=text, bg=Theme.SURFACE_0, fg=Theme.TEXT, font=(Theme.FONT_FAMILY, 7), anchor="w")
            lbl.pack(side="left", fill="x", expand=True)
            setattr(self, label_attr, lbl)
            return box

        hk_row1 = tk.Frame(self.hotkey_frame, bg=Theme.BASE)
        hk_row1.pack(fill="x", pady=(0, 4))
        for i in range(3):
            hk_row1.columnconfigure(i, weight=1, uniform="hk1")

        make_hk_box(hk_row1, "start_hk_label", f"▶ Start: {self.app.hotkey_manager.start_hotkey.upper()}", "start",
                    self.app.g_hotkey_enabled, 0,
                    "Click then press a key to set the Start hotkey", "Enable or disable the Start hotkey")
        make_hk_box(hk_row1, "pause_hk_label", f"⏸ Pause: {self.app.hotkey_manager.pause_hotkey.upper()}", "pause",
                    self.app.p_hotkey_enabled, 1,
                    "Click then press a key to set the Pause/Resume hotkey", "Enable or disable the Pause hotkey")
        make_hk_box(hk_row1, "stop_hk_label", f"⏹ Stop: {self.app.hotkey_manager.stop_hotkey.upper()}", "stop",
                    self.app.s_hotkey_enabled, 2,
                    "Click then press a key to set the Stop hotkey", "Enable or disable the Stop hotkey")

        hk_row2 = tk.Frame(self.hotkey_frame, bg=Theme.BASE)
        hk_row2.pack(fill="x")
        for i in range(2):
            hk_row2.columnconfigure(i, weight=1, uniform="hk2")

        make_hk_box(hk_row2, "record_start_hk_label", f"⏺ Start Rec: {self.app.hotkey_manager.record_start_hotkey.upper()}", "record_start",
                    self.app.rs_hotkey_enabled, 0,
                    "Click then press a key to set the Start Recording hotkey", "Enable or disable the Start Recording hotkey")
        make_hk_box(hk_row2, "record_stop_hk_label", f"⏹ Stop Rec: {self.app.hotkey_manager.record_stop_hotkey.upper()}", "record_stop",
                    self.app.re_hotkey_enabled, 1,
                    "Click then press a key to set the Stop Recording hotkey", "Enable or disable the Stop Recording hotkey")

        # Profile Frame
        self.profile_frame = tk.Frame(self.root, bg=Theme.BASE)
        self.profile_frame.pack(fill="x", padx=10, pady=3)

        btn_save = ttk.Button(self.profile_frame, text="Save Profile", command=self.app.save_profile)
        btn_save.pack(side="left", expand=True, fill="x", padx=(0, 3))
        ToolTip(btn_save, "Save the current sequence and settings to a JSON file")

        btn_load = ttk.Button(self.profile_frame, text="Load Profile", command=self.app.load_profile)
        btn_load.pack(side="left", expand=True, fill="x", padx=(3, 0))
        ToolTip(btn_load, "Load a previously saved profile from a JSON file")

        # Action Control Frame
        action_frame = tk.Frame(self.root, bg=Theme.BASE)
        action_frame.pack(fill="x", padx=10, pady=2)

        self.start_btn = ttk.Button(action_frame, text="Start", command=self.app.actions_engine.start_clicking)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=(0, 2))
        ToolTip(self.start_btn, "Start playing the action sequence")

        self.pause_btn = ttk.Button(action_frame, text="Pause", command=self.app.actions_engine.toggle_pause, state="disabled")
        self.pause_btn.pack(side="left", expand=True, fill="x", padx=2)
        ToolTip(self.pause_btn, "Pause / resume the running sequence (you can edit the list while paused)")

        self.stop_btn = ttk.Button(action_frame, text="Stop", command=self.app.actions_engine.stop_clicking, state="disabled")
        self.stop_btn.pack(side="left", expand=True, fill="x", padx=2)
        ToolTip(self.stop_btn, "Stop the running sequence immediately")

        self.exit_btn = ttk.Button(action_frame, text="Exit", command=self.app.exit_app)
        self.exit_btn.pack(side="left", expand=True, fill="x", padx=(2, 0))
        ToolTip(self.exit_btn, "Close the application")

        # Status & Footer bar
        bottom = tk.Frame(self.root, bg=Theme.BASE)
        bottom.pack(fill="x", padx=10, pady=(4, 6))

        self.status_label = tk.Label(bottom, text="Ready", font=Theme.FONT_MAIN, bg=Theme.BASE, fg=Theme.YELLOW)
        self.status_label.pack(side="left")

        self.progress_label = tk.Label(bottom, text="", font=Theme.FONT_SMALL, bg=Theme.BASE, fg=Theme.SUBTEXT)
        self.progress_label.pack(side="left", padx=(10, 0))

        right_bottom = tk.Frame(bottom, bg=Theme.BASE)
        right_bottom.pack(side="right")

        tk.Label(right_bottom, text=self.app.version, font=Theme.FONT_SMALL, bg=Theme.BASE, fg=Theme.OVERLAY).pack(side="right")
        tk.Label(right_bottom, text=" · ", font=Theme.FONT_SMALL, bg=Theme.BASE, fg=Theme.OVERLAY).pack(side="right")

        github_lbl = tk.Label(right_bottom, text="GitHub", font=(Theme.FONT_FAMILY, 8, "underline"),
                              bg=Theme.BASE, fg=Theme.BLUE, cursor="hand2")
        github_lbl.pack(side="right")
        github_lbl.bind("<Button-1>", lambda e: webbrowser.open(self.app.github_url))
        ToolTip(github_lbl, "Open the project repository on GitHub")

        tk.Label(right_bottom, text=" · ", font=Theme.FONT_SMALL, bg=Theme.BASE, fg=Theme.OVERLAY).pack(side="right")
        check_update_lbl = tk.Label(right_bottom, text="Check Update", font=(Theme.FONT_FAMILY, 8, "underline"),
                                    bg=Theme.BASE, fg=Theme.BLUE, cursor="hand2")
        check_update_lbl.pack(side="right")
        check_update_lbl.bind("<Button-1>", lambda e: self.app.check_for_update())
        ToolTip(check_update_lbl, "Check GitHub for a newer version")
