"""Theme definitions, persistence, and application for the calculator GUI."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gui import CalculatorApp

DEFAULT_THEME = "Light"
CONFIG_FILENAME = "calculator_settings.json"


def _get_config_path() -> Path:
    """Get appropriate config file path for packaged or development environment."""
    # Try user home directory first (works for packaged apps)
    try:
        home_dir = Path.home()
        config_dir = home_dir / ".calculator"
        config_dir.mkdir(exist_ok=True)
        return config_dir / CONFIG_FILENAME
    except (OSError, PermissionError):
        pass
    
    # Fallback to current directory (development environment)
    return Path(__file__).resolve().parent / CONFIG_FILENAME


@dataclass(frozen=True)
class ThemePalette:
    """Color and style tokens for one visual theme."""

    window_bg: str
    foreground: str
    accent: str
    frame_bg: str
    entry_bg: str
    entry_fg: str
    button_bg: str
    button_fg: str
    button_active: str
    label_fg: str
    text_bg: str
    text_fg: str
    text_select_bg: str
    tab_bg: str
    tab_fg: str
    tab_selected_bg: str
    border: str
    menu_bg: str
    menu_fg: str


THEMES: dict[str, ThemePalette] = {
    "Light": ThemePalette(
        window_bg="#f8f9fa",
        foreground="#212529",
        accent="#0d6efd",
        frame_bg="#f8f9fa",
        entry_bg="#ffffff",
        entry_fg="#212529",
        button_bg="#e9ecef",
        button_fg="#212529",
        button_active="#dee2e6",
        label_fg="#495057",
        text_bg="#ffffff",
        text_fg="#212529",
        text_select_bg="#cfe2ff",
        tab_bg="#e9ecef",
        tab_fg="#212529",
        tab_selected_bg="#ffffff",
        border="#dee2e6",
        menu_bg="#f8f9fa",
        menu_fg="#212529",
    ),
    "Dark": ThemePalette(
        window_bg="#1e1e1e",
        foreground="#e9ecef",
        accent="#3d8bfd",
        frame_bg="#1e1e1e",
        entry_bg="#2d2d2d",
        entry_fg="#f8f9fa",
        button_bg="#343a40",
        button_fg="#f8f9fa",
        button_active="#495057",
        label_fg="#ced4da",
        text_bg="#212529",
        text_fg="#e9ecef",
        text_select_bg="#1f4e79",
        tab_bg="#2d2d2d",
        tab_fg="#ced4da",
        tab_selected_bg="#1e1e1e",
        border="#495057",
        menu_bg="#1e1e1e",
        menu_fg="#e9ecef",
    ),
    "Blue": ThemePalette(
        window_bg="#e8f0fe",
        foreground="#1a365d",
        accent="#2563eb",
        frame_bg="#e8f0fe",
        entry_bg="#ffffff",
        entry_fg="#1a365d",
        button_bg="#dbeafe",
        button_fg="#1a365d",
        button_active="#bfdbfe",
        label_fg="#1e40af",
        text_bg="#ffffff",
        text_fg="#1a365d",
        text_select_bg="#bfdbfe",
        tab_bg="#dbeafe",
        tab_fg="#1a365d",
        tab_selected_bg="#e8f0fe",
        border="#93c5fd",
        menu_bg="#e8f0fe",
        menu_fg="#1a365d",
    ),
    "Green": ThemePalette(
        window_bg="#f0fdf4",
        foreground="#14532d",
        accent="#16a34a",
        frame_bg="#f0fdf4",
        entry_bg="#ffffff",
        entry_fg="#14532d",
        button_bg="#dcfce7",
        button_fg="#14532d",
        button_active="#bbf7d0",
        label_fg="#166534",
        text_bg="#ffffff",
        text_fg="#14532d",
        text_select_bg="#bbf7d0",
        tab_bg="#dcfce7",
        tab_fg="#14532d",
        tab_selected_bg="#f0fdf4",
        border="#86efac",
        menu_bg="#f0fdf4",
        menu_fg="#14532d",
    ),
}


def theme_names() -> tuple[str, ...]:
    """Return available theme names in display order."""
    return tuple(THEMES.keys())


def normalize_theme_name(name: str | None) -> str:
    """Return a valid theme name, falling back to the default."""
    if name in THEMES:
        return name
    return DEFAULT_THEME


class ThemeManager:
    """Loads, saves, and applies the selected theme."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or _get_config_path()
        self._current = self.load_saved_theme()

    @property
    def current_theme(self) -> str:
        return self._current

    def load_saved_theme(self) -> str:
        """Read theme from config file; use Light on any error."""
        try:
            raw = self.config_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if isinstance(data, dict):
                return normalize_theme_name(data.get("theme"))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
        return DEFAULT_THEME

    def save_theme(self, name: str) -> None:
        """Persist the theme name to the configuration file."""
        valid = normalize_theme_name(name)
        self._current = valid
        try:
            self.config_path.write_text(
                json.dumps({"theme": valid}, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    def set_theme(self, name: str) -> None:
        """Switch theme in memory and save preference."""
        self.save_theme(normalize_theme_name(name))

    def apply(self, app: CalculatorApp) -> None:
        """Apply the current theme to the running application."""
        palette = THEMES[self._current]
        root = app.root

        root.configure(bg=palette.window_bg)

        style = app.style
        style.theme_use("clam")

        style.configure(".", background=palette.frame_bg, foreground=palette.foreground)
        style.configure("TFrame", background=palette.frame_bg)
        style.configure(
            "TLabel",
            background=palette.frame_bg,
            foreground=palette.label_fg,
        )
        style.configure(
            "TButton",
            background=palette.button_bg,
            foreground=palette.button_fg,
            bordercolor=palette.border,
            focusthickness=1,
            focuscolor=palette.accent,
        )
        style.map(
            "TButton",
            background=[("active", palette.button_active), ("pressed", palette.button_active)],
            foreground=[("active", palette.button_fg)],
        )
        style.configure(
            "TEntry",
            fieldbackground=palette.entry_bg,
            foreground=palette.entry_fg,
            insertcolor=palette.entry_fg,
            bordercolor=palette.border,
        )
        style.configure(
            "TNotebook",
            background=palette.frame_bg,
            bordercolor=palette.border,
            tabmargins=(2, 4, 2, 0),
        )
        style.configure(
            "TNotebook.Tab",
            background=palette.tab_bg,
            foreground=palette.tab_fg,
            padding=(10, 4),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", palette.tab_selected_bg)],
            foreground=[("selected", palette.tab_fg)],
        )
        style.configure("TSeparator", background=palette.border)

        if app.history_text is not None:
            app.history_text.configure(
                bg=palette.text_bg,
                fg=palette.text_fg,
                insertbackground=palette.text_fg,
                selectbackground=palette.text_select_bg,
                highlightbackground=palette.border,
                highlightcolor=palette.accent,
            )

        if app.appearance_menu is not None:
            app.appearance_menu.configure(
                bg=palette.menu_bg,
                fg=palette.menu_fg,
                activebackground=palette.button_active,
                activeforeground=palette.menu_fg,
            )

        if app.menubar is not None:
            app.menubar.configure(
                bg=palette.menu_bg,
                fg=palette.menu_fg,
                activebackground=palette.button_active,
                activeforeground=palette.menu_fg,
            )

        app.update_theme_status()
