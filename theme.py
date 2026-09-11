"""
Theme definition for Auto Clicker Pro.
Centralized color palette based on Catppuccin Mocha.
"""

class Theme:
    # Backgrounds
    CRUST = "#11111b"
    MANTLE = "#181825"
    BASE = "#1e1e2e"          # Main application background
    SURFACE_0 = "#313244"     # Card / Section / Secondary background
    SURFACE_1 = "#45475a"     # Active / Hover / Input background
    SURFACE_2 = "#585b70"     # Borders / Separators

    # Text & Foreground
    TEXT = "#cdd6f4"          # Primary text
    SUBTEXT = "#a6adc8"       # Secondary / Muted text
    OVERLAY = "#6c7086"       # Placeholder / Disabled

    # Accents & States
    GREEN = "#a6e3a1"         # Start / Success / Running indicator
    RED = "#f38ba8"           # Stop / Delete / Error / Recording indicator
    BLUE = "#89b4fa"          # Primary button / Highlight
    YELLOW = "#f9e2af"        # Warning / Pause
    PEACH = "#fab387"         # Notice / Key indicator
    MAUVE = "#cba6f7"         # Special / Secondary accent
    TEAL = "#94e2d5"          # Info / Alternate accent

    # Action type colors
    ACTION_COLORS = {
        "click": GREEN,
        "drag": BLUE,
        "scroll": MAUVE,
        "wait": YELLOW,
        "key": PEACH,
    }

    # Font definitions
    FONT_FAMILY = "Segoe UI"
    FONT_MAIN = (FONT_FAMILY, 9)
    FONT_BOLD = (FONT_FAMILY, 9, "bold")
    FONT_TITLE = (FONT_FAMILY, 11, "bold")
    FONT_SMALL = (FONT_FAMILY, 8)
    FONT_MONO = ("Consolas", 9)
