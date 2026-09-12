"""
Modern custom visual widgets for Auto Clicker Pro.
Includes Canvas-based ToggleSwitch, ClickRippleOverlay, and modern Action Cards sequence view
with drag-and-drop reordering, double-click editing, and high-contrast styling.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Any, List
from theme import Theme
from gui_components import ToolTip
from logger import get_logger

logger = get_logger("Widgets")

class ToggleSwitch(tk.Canvas):
    """
    Modern pill-shaped toggle switch (iOS / Fluent style) built with Tkinter Canvas.
    Features high-contrast colors, crisp pure white active thumb, subtle borders,
    tk.BooleanVar binding, and full disabled state management.
    """

    ACTIVE_COLOR = "#4e6d94"       # Harmonious slate-blue accent (2 shades lighter than surface)
    INACTIVE_COLOR = "#252738"     # Deep surface tone (2 shades darker than surface)
    BORDER_COLOR = "#383b50"       # Inactive track contour
    ACTIVE_BORDER = "#5d80ab"      # Active track contour
    THUMB_ACTIVE = "#ffffff"       # Crisp Pure White
    THUMB_INACTIVE = "#6c7086"     # Soft silver/overlay
    THUMB_OUTLINE = "#38567a"      # Subtle definition ring

    def __init__(
        self,
        parent,
        variable: Optional[tk.BooleanVar] = None,
        command: Optional[Callable[[], None]] = None,
        width: int = 32,
        height: int = 16,
        active_color: Optional[str] = None,
        bg_color: Optional[str] = None,
        thumb_color: Optional[str] = None,
        state: str = "normal",
        **kwargs
    ):
        parent_bg = kwargs.pop("bg", parent.cget("bg") if hasattr(parent, "cget") else Theme.BASE)
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent_bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2" if state == "normal" else "arrow",
            **kwargs
        )

        self.width = width
        self.height = height
        self.active_color = active_color or self.ACTIVE_COLOR
        self.bg_color = bg_color or self.INACTIVE_COLOR
        self.thumb_color = thumb_color or self.THUMB_ACTIVE
        self._state = state

        self.variable = variable if variable is not None else tk.BooleanVar(value=False)
        self.command = command

        # Pill dimensions
        self.radius = height // 2
        self.thumb_radius = max(3, self.radius - 2)
        self.left_x = self.radius
        self.right_x = width - self.radius
        self.current_x = self.right_x if self.variable.get() else self.left_x

        self.bind("<Button-1>", self._on_click)
        if hasattr(self.variable, "trace_add"):
            self.variable.trace_add("write", lambda *_: self._on_var_changed())

        self.draw()

    def _on_var_changed(self):
        target_x = self.right_x if self.variable.get() else self.left_x
        if self.current_x != target_x:
            self.current_x = target_x
            self.draw()

    def _on_click(self, event=None):
        if self._state == "disabled":
            return "break"
        new_val = not self.variable.get()
        self.variable.set(new_val)
        self.draw()
        if self.command:
            try:
                self.command()
            except Exception as e:
                logger.debug(f"Error in ToggleSwitch command callback: {e}")
        return "break"

    def config_state(self, state: str):
        self._state = state
        self.configure(cursor="hand2" if state == "normal" else "arrow")
        self.draw()

    def config(self, cnf=None, **kwargs):
        if "state" in kwargs:
            self.config_state(kwargs.pop("state"))
        if cnf and "state" in cnf:
            self.config_state(cnf.pop("state"))
        if cnf or kwargs:
            super().config(cnf, **kwargs)

    def configure(self, cnf=None, **kwargs):
        return self.config(cnf, **kwargs)

    @property
    def state(self) -> str:
        return self._state

    def draw(self):
        self.delete("all")
        is_active = self.variable.get()

        if self._state == "disabled":
            bg = Theme.BASE
            border = Theme.SURFACE_0
            thumb = Theme.SURFACE_1
        else:
            if is_active:
                bg = self.active_color
                border = self.ACTIVE_BORDER if self.active_color == self.ACTIVE_COLOR else self.active_color
                thumb = self.thumb_color
            else:
                bg = self.bg_color
                border = self.BORDER_COLOR
                thumb = self.THUMB_INACTIVE

        r = self.radius
        w = self.width
        h = self.height
        h_idx = h - 1
        w_idx = w - 1

        # 1. Seamless background pill (no inner seams, vertical chords, or lines)
        self.create_oval(0, 0, h_idx, h_idx, fill=bg, outline="")
        self.create_oval(w - h, 0, w_idx, h_idx, fill=bg, outline="")
        self.create_rectangle(r, 0, w - r, h_idx, fill=bg, outline="")

        # 2. Seamless outer contour (style="arc" draws only curved caps without inner chord lines)
        if border:
            self.create_arc(0, 0, h_idx, h_idx, start=90, extent=180, outline=border, style="arc")
            self.create_arc(w - h, 0, w_idx, h_idx, start=270, extent=180, outline=border, style="arc")
            self.create_line(r, 0, w - r, 0, fill=border)
            self.create_line(r, h_idx, w - r, h_idx, fill=border)

        # 3. Clean thumb circle (identical geometry and outline="" for both ON and OFF states)
        tx = self.current_x
        ty = h // 2
        tr = self.thumb_radius
        self.create_oval(tx - tr, ty - tr, tx + tr, ty + tr, fill=thumb, outline="")


class ActionCard(tk.Frame):
    """
    Individual modern action card representing an ActionPoint.
    Features:
    - Left accent stripe matching action color
    - Grip handle (⠿) for visual drag indication
    - Step index (#01, #02)
    - Action type & custom name
    - Parameter badges (pills) for coordinates, delay, hold, keys
    - Built-in ToggleSwitch for mute/enable
    - Quick delete trigger (✕)
    - Full drag & drop reordering and double-click editing
    """
    def __init__(
        self,
        parent,
        view: "ActionCardsView",
        index: int,
        point: Any,
        on_select: Callable[[int], None],
        on_double_click: Callable[[int], None],
        on_toggle_enable: Callable[[int, bool], None],
        on_delete: Callable[[int], None],
        **kwargs
    ):
        super().__init__(
            parent,
            bg=Theme.SURFACE_0,
            highlightthickness=1,
            highlightbackground=Theme.SURFACE_1,
            padx=6,
            pady=4,
            cursor="hand2",
            **kwargs
        )
        self.view = view
        self.index = index
        self.point = point
        self.on_select = on_select
        self.on_double_click = on_double_click
        self.on_toggle_enable = on_toggle_enable
        self.on_delete = on_delete

        self.is_selected = False
        self.is_active_step = False
        self._press_x = 0
        self._press_y = 0
        self._is_dragging = False

        self._build_ui()
        self._bind_all_card_events()

    def _build_ui(self):
        p = self.point
        action = p.get("action", "click")
        enabled = p.get("enabled", True)
        color = Theme.ACTION_COLORS.get(action, Theme.TEXT) if enabled else Theme.OVERLAY

        # 1. Right controls frame (Delete quick button + Enable switch) - PACK FIRST TO GUARANTEE PINNED VISIBILITY
        self.right_ctrls = tk.Frame(self, bg=Theme.SURFACE_0)
        self.right_ctrls.pack(side="right", padx=(4, 0))

        # Delete quick button
        self.del_btn = tk.Label(
            self.right_ctrls,
            text="✕",
            font=("Segoe UI", 9, "bold"),
            fg=Theme.SUBTEXT,
            bg=Theme.SURFACE_0,
            cursor="hand2",
            padx=4
        )
        self.del_btn.pack(side="right", padx=(4, 0))
        self.del_btn.bind("<Enter>", lambda e: self.del_btn.config(fg=Theme.RED))
        self.del_btn.bind("<Leave>", lambda e: self.del_btn.config(fg=Theme.SUBTEXT))
        self.del_btn.bind("<Button-1>", lambda e: self._on_del_clicked())

        # Enable / Mute ToggleSwitch
        self.enable_var = tk.BooleanVar(value=enabled)
        self.enable_switch = ToggleSwitch(
            self.right_ctrls,
            variable=self.enable_var,
            width=28,
            height=14,
            command=self._on_switch_toggled,
            bg=Theme.SURFACE_0
        )
        self.enable_switch.pack(side="right", padx=(2, 4))

        # 2. Left accent bar
        self.accent_bar = tk.Frame(self, width=4, bg=color)
        self.accent_bar.pack(side="left", fill="y", padx=(0, 4))

        # 3. Drag grip handle (⠿)
        self.grip_lbl = tk.Label(
            self,
            text="⠿",
            font=("Segoe UI", 10),
            fg=Theme.OVERLAY,
            bg=Theme.SURFACE_0,
            cursor="fleur",
            padx=2
        )
        self.grip_lbl.pack(side="left", padx=(0, 4))

        # 4. Index Badge (#01, #02)
        self.index_label = tk.Label(
            self,
            text=f"#{self.index + 1:02d}",
            font=Theme.FONT_MONO,
            fg=Theme.SUBTEXT if enabled else Theme.OVERLAY,
            bg=Theme.SURFACE_0,
            width=4,
            anchor="w"
        )
        self.index_label.pack(side="left", padx=(0, 2))

        # 5. Action icon & main name (truncated if long, with tooltip for full text)
        self.title_tooltip = None
        title_text, full_tooltip_text = self._compute_title_text(p, action)
        self.title_label = tk.Label(
            self,
            text=title_text,
            font=Theme.FONT_BOLD,
            fg=Theme.TEXT if enabled else Theme.OVERLAY,
            bg=Theme.SURFACE_0,
            anchor="w"
        )
        self.title_label.pack(side="left", padx=(0, 6))
        if full_tooltip_text:
            self.title_tooltip = ToolTip(self.title_label, full_tooltip_text)

        # 6. Badges / Parameters Pills frame
        self.badges_frame = tk.Frame(self, bg=Theme.SURFACE_0)
        self.badges_frame.pack(side="left", fill="x", expand=True)
        self._populate_pills(self.badges_frame, p, action, enabled)

    def _compute_title_text(self, p, action):
        emoji_map = {
            "click": " 🖱️",
            "drag": " ↔️ ",
            "scroll": " ↕️  ",
            "wait": "⏱️     ",
            "key": "⌨️     ",
        }
        icon = emoji_map.get(action, "⚡")
        name = str(p.get("name") or "").strip()

        if name:
            raw_title = name
        elif action == "click":
            raw_title = f"{p.get('type', 'Left')} Click"
        elif action == "drag":
            raw_title = "Drag Move"
        elif action == "scroll":
            raw_title = f"Scroll {('UP' if p.get('dy', 0) > 0 else 'DOWN')}"
        elif action == "wait":
            raw_title = f"Wait {p.get('delay', 500)}ms"
        elif action == "key":
            raw_title = "Key"
        else:
            raw_title = action.title()

        full_text = f"{icon}  {raw_title}"

        # If title is excessively long, truncate with ellipsis and provide full text for tooltip
        if len(raw_title) > 28:
            truncated = raw_title[:16] + "..." + raw_title[-8:]
            return f"{icon}  {truncated}", full_text

        return full_text, None

    def _populate_pills(self, frame, p, action, enabled):
        def add_pill(text, bg_pill=Theme.BASE, fg_pill=Theme.TEXT):
            pill = tk.Label(
                frame,
                text=text,
                font=Theme.FONT_SMALL,
                bg=bg_pill,
                fg=fg_pill if enabled else Theme.OVERLAY,
                padx=5,
                pady=1,
                relief="flat"
            )
            pill.pack(side="left", padx=2)
            self._bind_widget(pill)
            return pill

        if action == "click":
            add_pill(f"({p.get('x', 0)}, {p.get('y', 0)})", Theme.BASE, Theme.GREEN)
            if p.get("hold", 50) != 50:
                add_pill(f"hold {p.get('hold', 50)}ms", Theme.SURFACE_1, Theme.SUBTEXT)
            if p.get("count", 1) > 1:
                add_pill(f"×{p.get('count', 1)}", Theme.SURFACE_1, Theme.YELLOW)
        elif action == "drag":
            add_pill(f"({p.get('x', 0)}, {p.get('y', 0)}) → ({p.get('drag_x', 0)}, {p.get('drag_y', 0)})", Theme.BASE, Theme.BLUE)
            add_pill(f"{p.get('hold', 300)}ms", Theme.SURFACE_1, Theme.SUBTEXT)
        elif action == "scroll":
            add_pill(f"({p.get('x', 0)}, {p.get('y', 0)})", Theme.BASE, Theme.MAUVE)
            dy_val = p.get('dy', 0)
            amount = abs(dy_val) if dy_val != 0 else p.get('amount', 1)
            add_pill(f"Amount: {amount}", Theme.SURFACE_1, Theme.SUBTEXT)
            if p.get("count", 1) > 1:
                add_pill(f"×{p.get('count', 1)}", Theme.SURFACE_1, Theme.YELLOW)
        elif action == "wait":
            add_pill(f"{p.get('delay', 500)}ms", Theme.BASE, Theme.YELLOW)
        elif action == "key":
            key_val = str(p.get('key', 'a'))
            if len(key_val) > 24:
                pill_txt = f"'{key_val[:14]}...{key_val[-6:]}'"
                pill = add_pill(pill_txt, Theme.BASE, Theme.PEACH)
                ToolTip(pill, f"'{key_val}'")
            else:
                add_pill(f"'{key_val}'", Theme.BASE, Theme.PEACH)
            if p.get("count", 1) > 1:
                add_pill(f"×{p.get('count', 1)}", Theme.SURFACE_1, Theme.YELLOW)

    def _bind_all_card_events(self):
        """Recursively bind card interaction events to all children except control buttons."""
        targets = [self, self.accent_bar, self.grip_lbl, self.index_label, self.title_label, self.badges_frame]
        for t in targets:
            self._bind_widget(t)

    def _bind_widget(self, widget):
        widget.bind("<Button-1>", self._on_press, add="+")
        widget.bind("<Double-Button-1>", self._on_double_click_handler, add="+")
        widget.bind("<B1-Motion>", self._on_motion, add="+")
        widget.bind("<ButtonRelease-1>", self._on_release, add="+")
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")

    def _on_press(self, event):
        self._press_x = event.x_root
        self._press_y = event.y_root
        self._is_dragging = False
        # Immediate selection feedback
        if self.on_select:
            self.on_select(self.index)

    def _on_motion(self, event):
        dx = abs(event.x_root - self._press_x)
        dy = abs(event.y_root - self._press_y)
        if not self._is_dragging and (dy > 4 or dx > 4):
            self._is_dragging = True
            if self.view:
                self.view.start_card_drag(self.index)

        if self._is_dragging and self.view:
            self.view.handle_card_drag(self.index, event.y_root)

    def _on_release(self, event):
        if self._is_dragging and self.view:
            self._is_dragging = False
            self.view.finish_card_drag()
        else:
            self._is_dragging = False
            if self.on_select:
                self.on_select(self.index)

    def _on_double_click_handler(self, event=None):
        self._is_dragging = False
        if self.on_select:
            self.on_select(self.index)
        if self.on_double_click:
            self.on_double_click(self.index)
        return "break"

    def _on_switch_toggled(self):
        new_val = self.enable_var.get()
        self.point["enabled"] = new_val
        self.update_mute_visual(new_val)
        if self.on_toggle_enable:
            self.on_toggle_enable(self.index, new_val)

    def _on_del_clicked(self):
        if self.on_delete:
            self.on_delete(self.index)
        return "break"

    def _on_enter(self, event=None):
        if not self.is_selected and not self.is_active_step:
            self.config(highlightbackground=Theme.SURFACE_2)
            self.grip_lbl.config(fg=Theme.TEXT)

    def _on_leave(self, event=None):
        if not self.is_selected and not self.is_active_step:
            self.config(highlightbackground=Theme.SURFACE_1)
            self.grip_lbl.config(fg=Theme.OVERLAY)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        if self.is_active_step:
            return
        if selected:
            self.config(bg=Theme.SURFACE_1, highlightbackground=Theme.BLUE, highlightthickness=1)
            self._update_children_bg(Theme.SURFACE_1)
        else:
            self.config(bg=Theme.SURFACE_0, highlightbackground=Theme.SURFACE_1, highlightthickness=1)
            self._update_children_bg(Theme.SURFACE_0)

    def set_drag_active(self, active: bool):
        """Distinct visual highlight while this card slot is actively being dragged/reordered."""
        if active:
            self.config(bg=Theme.SURFACE_1, highlightbackground=Theme.PEACH, highlightthickness=2)
            self.grip_lbl.config(fg=Theme.PEACH)
            self._update_children_bg(Theme.SURFACE_1)
        else:
            self.grip_lbl.config(fg=Theme.OVERLAY)
            self.set_selected(self.is_selected)

    def set_highlighted(self, active: bool):
        self.is_active_step = active
        if active:
            self.config(bg=Theme.SURFACE_1, highlightbackground=Theme.GREEN, highlightthickness=2)
            self._update_children_bg(Theme.SURFACE_1)
        else:
            self.set_selected(self.is_selected)

    def update_mute_visual(self, enabled: bool):
        action = self.point.get("action", "click")
        color = Theme.ACTION_COLORS.get(action, Theme.TEXT) if enabled else Theme.OVERLAY
        self.accent_bar.config(bg=color)
        self.index_label.config(fg=Theme.SUBTEXT if enabled else Theme.OVERLAY)
        self.title_label.config(fg=Theme.TEXT if enabled else Theme.OVERLAY)

    def update_index_and_data(self, new_index: int, new_point: Any):
        """Update existing card's index and content in place without widget destruction."""
        self.index = new_index
        self.point = new_point
        action = new_point.get("action", "click")
        enabled = new_point.get("enabled", True)

        self.index_label.config(text=f"#{new_index + 1:02d}")
        title_text, full_tooltip_text = self._compute_title_text(new_point, action)
        self.title_label.config(text=title_text)
        if full_tooltip_text:
            if self.title_tooltip:
                self.title_tooltip.text = full_tooltip_text
            else:
                self.title_tooltip = ToolTip(self.title_label, full_tooltip_text)
        else:
            if self.title_tooltip:
                self.title_tooltip.text = ""

        color = Theme.ACTION_COLORS.get(action, Theme.TEXT) if enabled else Theme.OVERLAY
        self.accent_bar.config(bg=color)

        for child in self.badges_frame.winfo_children():
            child.destroy()
        self._populate_pills(self.badges_frame, new_point, action, enabled)

        self.enable_var.set(enabled)
        self.update_mute_visual(enabled)

    def _update_children_bg(self, bg_color: str):
        for w in (self.grip_lbl, self.index_label, self.title_label, self.badges_frame, self.right_ctrls, self.del_btn):
            try:
                w.config(bg=bg_color)
            except tk.TclError as e:
                logger.debug(f"Child background update skipped: {e}")
        try:
            self.enable_switch.config(bg=bg_color)
            self.enable_switch.draw()
        except tk.TclError as e:
            logger.debug(f"Enable switch background update skipped: {e}")


class ActionCardsView(tk.Frame):
    """
    Scrollable modern container for ActionCard items.
    Replaces standard Listbox with full card layout, auto-scroll, empty-state placeholder,
    mouse wheel support, live Drag & Drop reordering, and double-click editing.
    """
    def __init__(self, parent, on_select=None, on_edit=None, on_delete=None, on_reorder=None, **kwargs):
        super().__init__(parent, bg=Theme.BASE, **kwargs)
        self.on_select = on_select
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_reorder = on_reorder

        self.cards: List[ActionCard] = []
        self.selected_index: Optional[int] = None
        self.highlighted_index: Optional[int] = None
        self._state = "normal"
        self._app_points_ref = None
        self._drag_active: bool = False
        self._current_drag_index: Optional[int] = None

        self._create_ui()

    def _create_ui(self):
        self.canvas = tk.Canvas(self, bg=Theme.BASE, highlightthickness=0, bd=0, height=170)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner_frame = tk.Frame(self.canvas, bg=Theme.BASE)

        self.window_id = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.config(yscrollcommand=self.scrollbar.set)

        self.inner_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.bind_mousewheel(self)
        self.bind_mousewheel(self.canvas)
        self.bind_mousewheel(self.inner_frame)

    def bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        for child in widget.winfo_children():
            self.bind_mousewheel(child)

    def _on_mousewheel(self, event):
        if self.canvas.winfo_exists():
            delta = -1 if event.delta < 0 else 1
            self.canvas.yview_scroll(-1 * delta, "units")
        return "break"

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)

    def render(self, points, selected_index=None, active_index=None):
        self._app_points_ref = points
        self._drag_active = False
        self._current_drag_index = None
        for child in self.inner_frame.winfo_children():
            child.destroy()
        self.cards.clear()

        if not points:
            # Modern empty state banner
            empty_box = tk.Frame(self.inner_frame, bg=Theme.SURFACE_0, padx=16, pady=28)
            empty_box.pack(fill="x", padx=4, pady=8)
            lbl1 = tk.Label(empty_box, text="⚡ No Actions in Sequence", font=Theme.FONT_BOLD,
                            bg=Theme.SURFACE_0, fg=Theme.BLUE)
            lbl1.pack()
            lbl2 = tk.Label(empty_box, text="Click 'Add Click', 'Add Drag', 'Add Wait', or 'Record' to get started",
                            font=Theme.FONT_SMALL, bg=Theme.SURFACE_0, fg=Theme.SUBTEXT)
            lbl2.pack(pady=(4, 0))
            self.bind_mousewheel(empty_box)
            self._on_frame_configure()
            return

        for i, p in enumerate(points):
            card = ActionCard(
                self.inner_frame,
                view=self,
                index=i,
                point=p,
                on_select=self._on_card_selected,
                on_double_click=self._on_card_double_clicked,
                on_toggle_enable=self._on_card_toggled,
                on_delete=self._on_card_deleted,
            )
            card.pack(fill="x", padx=2, pady=2)
            self.bind_mousewheel(card)
            self.cards.append(card)

        if selected_index is not None and 0 <= selected_index < len(self.cards):
            self.select(selected_index)
        if active_index is not None and 0 <= active_index < len(self.cards):
            self.highlight_current(active_index)

        self._on_frame_configure()

    def start_card_drag(self, initial_index: int):
        """Begin a smooth drag-and-drop session for the given card index."""
        if self._state == "disabled" or not self._app_points_ref or len(self.cards) <= 1:
            return
        self._drag_active = True
        self._current_drag_index = initial_index
        if 0 <= initial_index < len(self.cards):
            self.cards[initial_index].set_drag_active(True)

    def handle_card_drag(self, dragged_index: Optional[int], mouse_y_root: int):
        """
        Process live drag-and-drop reordering with stable index tracking and midpoint hysteresis.
        Eliminates oscillation, rapid flickering, and erratic slot jumps.
        """
        if self._state == "disabled" or not self._app_points_ref or len(self.cards) <= 1:
            return

        # Initialize drag session if not already active
        if not self._drag_active or self._current_drag_index is None:
            self._drag_active = True
            self._current_drag_index = dragged_index if dragged_index is not None else 0

        curr_idx = self._current_drag_index
        if curr_idx < 0 or curr_idx >= len(self.cards):
            return

        # Identify which card boundary mouse_y_root currently falls into
        target_idx = None
        for i, card in enumerate(self.cards):
            card_y = card.winfo_rooty()
            card_h = card.winfo_height()
            if card_y <= mouse_y_root <= card_y + card_h:
                target_idx = i
                break

        # Dragged outside top or bottom boundary
        if target_idx is None:
            first_card_y = self.cards[0].winfo_rooty()
            last_card = self.cards[-1]
            last_card_bottom = last_card.winfo_rooty() + last_card.winfo_height()
            if mouse_y_root < first_card_y:
                target_idx = 0
            elif mouse_y_root > last_card_bottom:
                target_idx = len(self.cards) - 1

        if target_idx is None or target_idx == curr_idx:
            return

        # Midpoint hysteresis: for neighboring card moves, require mouse passing halfway across the target
        target_card = self.cards[target_idx]
        target_card_h = target_card.winfo_height()
        if target_card_h > 10:  # In valid rendered geometry
            target_card_mid = target_card.winfo_rooty() + (target_card_h // 2)
            if target_idx == curr_idx + 1 and mouse_y_root < target_card_mid:
                return
            elif target_idx == curr_idx - 1 and mouse_y_root > target_card_mid:
                return

        # Reorder item in data list
        item = self._app_points_ref.pop(curr_idx)
        self._app_points_ref.insert(target_idx, item)

        # Update tracked index immediately to the new slot
        self._current_drag_index = target_idx
        self.selected_index = target_idx

        # Update card contents in place without losing mouse capture
        for idx, card in enumerate(self.cards):
            card.update_index_and_data(idx, self._app_points_ref[idx])
            card.set_selected(idx == target_idx)
            card.set_drag_active(idx == target_idx)

        # Smooth auto-scroll if dragging near canvas boundaries
        try:
            canvas_y = self.canvas.winfo_rooty()
            canvas_h = self.canvas.winfo_height()
            if mouse_y_root < canvas_y + 20:
                self.canvas.yview_scroll(-1, "units")
            elif mouse_y_root > canvas_y + canvas_h - 20:
                self.canvas.yview_scroll(1, "units")
        except (tk.TclError, RuntimeError) as e:
            logger.debug(f"Auto-scroll on drag skipped: {e}")

        if self.on_select:
            self.on_select(target_idx)

    def finish_card_drag(self):
        """Finalize drag-and-drop action, clear visual drag highlight, and notify listener."""
        was_dragging = self._drag_active
        final_idx = self._current_drag_index
        self._drag_active = False
        self._current_drag_index = None

        for card in self.cards:
            if isinstance(card, ActionCard):
                card.set_drag_active(False)

        if was_dragging and final_idx is not None and 0 <= final_idx < len(self.cards):
            self.select(final_idx)
            if self.on_reorder:
                self.on_reorder()

    def _on_card_selected(self, index: int):
        if self._state == "disabled":
            return
        self.select(index)
        if self.on_select:
            self.on_select(index)

    def _on_card_double_clicked(self, index: int):
        if self._state == "disabled":
            return
        self.select(index)
        if self.on_edit:
            self.on_edit(index)

    def _on_card_toggled(self, index: int, enabled: bool):
        pass

    def _on_card_deleted(self, index: int):
        if self._state == "disabled":
            return
        if self.on_delete:
            self.on_delete(index)

    def select(self, index: int):
        self.selected_index = index
        for i, card in enumerate(self.cards):
            if isinstance(card, ActionCard):
                card.set_selected(i == index)
        self.see(index)

    def highlight_current(self, index: int):
        self.highlighted_index = index
        for i, card in enumerate(self.cards):
            if isinstance(card, ActionCard):
                card.set_highlighted(i == index)
        self.see(index)

    def clear_highlight(self):
        self.highlighted_index = None
        for card in self.cards:
            if isinstance(card, ActionCard):
                card.set_highlighted(False)

    def see(self, index: int):
        """
        Scroll canvas to ensure the card at index is visible ('scrollIntoView nearest').
        If the card is already visible inside the viewport, it does NOT scroll at all,
        preventing unexpected visual jumps when selecting items.
        """
        if not (0 <= index < len(self.cards)):
            return

        target = self.cards[index]
        if not isinstance(target, ActionCard):
            return

        try:
            self.update_idletasks()
            total_h = self.inner_frame.winfo_height()
            canvas_h = self.canvas.winfo_height()
            if total_h <= 0 or canvas_h <= 0:
                return

            if total_h <= canvas_h:
                self.canvas.yview_moveto(0.0)
                return

            y_top_ratio, y_bottom_ratio = self.canvas.yview()
            visible_top_px = y_top_ratio * total_h
            visible_bottom_px = y_bottom_ratio * total_h

            card_top_px = target.winfo_y()
            card_bottom_px = card_top_px + target.winfo_height()

            # 1. Already fully visible inside the viewport -> do not scroll
            if card_top_px >= visible_top_px - 2 and card_bottom_px <= visible_bottom_px + 2:
                return

            # 2. Hidden above viewport -> scroll up to align card top with viewport top
            if card_top_px < visible_top_px:
                new_top = max(0.0, min(1.0, card_top_px / total_h))
                self.canvas.yview_moveto(new_top)
                return

            # 3. Hidden below viewport -> scroll down just enough to reveal card bottom
            if card_bottom_px > visible_bottom_px:
                target_top_for_reveal = card_bottom_px - canvas_h
                new_top = max(0.0, min(1.0, target_top_for_reveal / total_h))
                self.canvas.yview_moveto(new_top)
                return

        except Exception as e:
            logger.debug(f"Error scrolling card into view: {e}")

    def config_state(self, state: str):
        self._state = state
        for card in self.cards:
            if isinstance(card, ActionCard):
                card.enable_switch.config_state(state)

    def config(self, cnf=None, **kwargs):
        if "state" in kwargs:
            self.config_state(kwargs.pop("state"))
        if cnf and "state" in cnf:
            self.config_state(cnf.pop("state"))
        if cnf or kwargs:
            super().config(cnf, **kwargs)

    def configure(self, cnf=None, **kwargs):
        return self.config(cnf, **kwargs)

    # Compatibility methods mimicking tk.Listbox for backwards compatibility
    def size(self) -> int:
        return len(self.cards)

    def curselection(self):
        if self.selected_index is not None and 0 <= self.selected_index < len(self.cards):
            return (self.selected_index,)
        return ()

    def selection_clear(self, first, last=None):
        self.selected_index = None
        for card in self.cards:
            if isinstance(card, ActionCard):
                card.set_selected(False)

    def selection_set(self, first, last=None):
        self.select(first)

    def activate(self, index):
        self.select(index)

    def delete(self, first, last=None):
        for child in self.inner_frame.winfo_children():
            child.destroy()
        self.cards.clear()


class ClickRippleOverlay:
    """
    Transient, transparent, click-through overlay showing a glowing expanding ripple
    on the physical screen where a simulated click or drag occurs.
    """

    def __init__(self, root: tk.Tk, x: int, y: int, color: str = "#22c55e", max_radius: int = 28):
        self.root = root
        self.x = int(x)
        self.y = int(y)
        self.color = color
        self.max_radius = max_radius
        self.current_radius = 4
        self.max_steps = 10
        self.current_step = 0

        size = (max_radius + 6) * 2
        self.size = size

        try:
            self.win = tk.Toplevel(root)
            self.win.overrideredirect(True)
            self.win.attributes("-topmost", True)

            transparent_key = "#010101"
            try:
                self.win.attributes("-transparentcolor", transparent_key)
            except tk.TclError:
                transparent_key = Theme.BASE

            self.win.geometry(f"{size}x{size}+{self.x - size // 2}+{self.y - size // 2}")

            self.canvas = tk.Canvas(
                self.win, width=size, height=size,
                bg=transparent_key, highlightthickness=0, bd=0
            )
            self.canvas.pack()
            self._animate()
        except Exception as e:
            logger.debug(f"Could not spawn click ripple overlay: {e}")
            if hasattr(self, "win") and self.win:
                try:
                    self.win.destroy()
                except tk.TclError:
                    pass

    def _animate(self):
        try:
            if not hasattr(self, "win") or not self.win or not self.win.winfo_exists():
                return
            if not hasattr(self, "root") or not self.root or not self.root.winfo_exists():
                return
            if self.current_step >= self.max_steps:
                try:
                    self.win.destroy()
                except tk.TclError:
                    pass
                return

            self.canvas.delete("all")
            progress = self.current_step / self.max_steps
            radius = self.current_radius + (self.max_radius - self.current_radius) * progress
            center = self.size // 2

            # Line width thins as it expands (3 -> 1)
            line_w = max(1, int(3 * (1.0 - progress * 0.7)))

            # Draw expanding ring
            self.canvas.create_oval(
                center - radius, center - radius,
                center + radius, center + radius,
                outline=self.color, width=line_w, fill=""
            )

            # Small inner dot in early steps
            if progress < 0.5:
                dot_r = max(1, int(3 * (1.0 - progress * 2)))
                self.canvas.create_oval(
                    center - dot_r, center - dot_r,
                    center + dot_r, center + dot_r,
                    fill=self.color, outline=""
                )

            self.current_step += 1
            self.root.after(20, self._animate)
        except (tk.TclError, RuntimeError) as e:
            logger.debug(f"Ripple animation step skipped: {e}")


def show_click_ripple(root: tk.Tk, x: int, y: int, color: str = "#22c55e"):
    """Safely launch a click ripple animation on the main GUI thread."""
    try:
        ClickRippleOverlay(root, x, y, color)
    except Exception as e:
        logger.debug(f"Error triggering click ripple: {e}")
