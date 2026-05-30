"""Tkinter GUI for the scientific calculator.

All math is delegated to core.py and parser.py. This module handles layout,
input, and presenting results or errors only.
"""

from __future__ import annotations

import math
import sys
import tkinter as tk
from collections.abc import Callable, Sequence
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from __version__ import __app_name__, __author__, __description__, __version__
from core import (
    CalculatorError,
    absolute,
    add,
    arccosine,
    arcsine,
    arctangent,
    ceil_value,
    cosine,
    degree_conversion,
    div,
    exponential,
    factorial_value,
    floor_value,
    gcd_value,
    log_base10,
    mul,
    natural_log,
    power,
    radian_conversion,
    sine,
    square_root,
    sub,
    tangent,
    trunc_value,
)
from history import HistoryManager
from memory import CalculatorMemory
from parser import ParserError, evaluate_expression, expression_parser
from themes import ThemeManager, theme_names

# --- Layout constants ---
PADDING = 14
PAD_BUTTON = 5
PAD_TAB = 10
FONT_DISPLAY = ("Segoe UI", 24)
FONT_HINT = ("Segoe UI", 9)
FONT_HISTORY = ("Consolas", 10)
BUTTON_WIDTH = 18
BUTTON_WIDTH_KEYPAD = 8
HINT_WRAP = 380
HISTORY_HEIGHT = 16
KEYPAD_ROWS = [
    ("7", "8", "9", "/"),
    ("4", "5", "6", "*"),
    ("1", "2", "3", "-"),
    ("0", ".", "(", "+"),
    ("C", "⌫", ")", "="),
]


def format_result(value: float | int) -> str:
    """Format a numeric result for the display."""
    if isinstance(value, int):
        return str(value)
    if value == int(value):
        return str(int(value))
    return str(value)


def parse_number_list(text: str) -> list[float]:
    """Parse comma-separated numbers from user input."""
    return [float(part.strip()) for part in text.split(",") if part.strip()]


def format_value_list(values: Sequence[float]) -> str:
    """Format numbers for history input display."""
    return ", ".join(format_result(value) for value in values)


class CalculatorApp:
    """Main calculator window: display, keypad, and operation tabs."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(__app_name__)
        self.root.resizable(True, True)
        self.root.minsize(450, 600)
        self._set_window_icon()
        self.display_var = tk.StringVar(value="0")
        self.display_entry: ttk.Entry | None = None
        self.history = HistoryManager()
        self.memory = CalculatorMemory()
        self.history_text: tk.Text | None = None
        self.memory_var = tk.StringVar(value="Memory: 0")
        self.theme_var = tk.StringVar()
        self.theme_menu_var = tk.StringVar()
        self.style = ttk.Style()
        self.theme_manager = ThemeManager()
        self.theme_menu_var.set(self.theme_manager.current_theme)
        self.container: ttk.Frame | None = None
        self.notebook: ttk.Notebook | None = None
        self.menubar: tk.Menu | None = None
        self.appearance_menu: tk.Menu | None = None
        self.help_menu: tk.Menu | None = None
        self._build_ui()
        self._build_appearance_menu()
        self._build_help_menu()
        self.theme_manager.apply(self)
        self._bind_keyboard()

    def _build_ui(self) -> None:
        self.container = ttk.Frame(self.root, padding=PADDING)
        container = self.container
        container.grid(row=0, column=0, sticky="nsew")

        self.display_entry = ttk.Entry(
            container,
            textvariable=self.display_var,
            font=FONT_DISPLAY,
            justify="right",
        )
        self.display_entry.grid(
            row=0,
            column=0,
            columnspan=4,
            sticky="ew",
            pady=(0, 10),
            ipady=14,
        )

        self._build_memory_bar(container)
        self._build_keypad(container)
        self._build_notebook(container)

        for col_index in range(4):
            container.columnconfigure(col_index, weight=1)
        
        # Configure row weights to allow notebook expansion
        container.rowconfigure(9, weight=1)

    def _build_memory_bar(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            textvariable=self.memory_var,
            font=FONT_HINT,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(
            parent,
            textvariable=self.theme_var,
            font=FONT_HINT,
        ).grid(row=1, column=2, columnspan=2, sticky="e", pady=(0, 8))

        memory_buttons = [
            ("MC", self._memory_clear),
            ("MR", self._memory_recall),
            ("M+", self._memory_add),
            ("M-", self._memory_subtract),
        ]
        for col_index, (label, command) in enumerate(memory_buttons):
            ttk.Button(
                parent,
                text=label,
                command=command,
                width=BUTTON_WIDTH_KEYPAD,
            ).grid(
                row=2,
                column=col_index,
                sticky="nsew",
                padx=PAD_BUTTON,
                pady=PAD_BUTTON,
                ipady=6,
            )

    def _build_keypad(self, parent: ttk.Frame) -> None:
        for row_index, row in enumerate(KEYPAD_ROWS, start=3):
            for col_index, label in enumerate(row):
                self._add_keypad_button(parent, label, row_index, col_index)

        ttk.Separator(parent, orient="horizontal").grid(
            row=8,
            column=0,
            columnspan=4,
            sticky="ew",
            pady=(16, 16),
        )

    def _build_notebook(self, parent: ttk.Frame) -> None:
        self.notebook = ttk.Notebook(parent)
        notebook = self.notebook
        notebook.grid(row=9, column=0, columnspan=4, sticky="nsew")

        self._add_tab(
            notebook,
            "Basic",
            "Keypad: build expressions and press =. "
            "List ops: comma-separated values (e.g. 5,3,2).",
            [
                ("Add", lambda: self._run_sequence(add, "Add")),
                ("Subtract", lambda: self._run_sequence(sub, "Subtract")),
                ("Multiply", lambda: self._run_sequence(mul, "Multiply")),
                ("Divide", lambda: self._run_sequence(div, "Divide")),
                (
                    "Power",
                    lambda: self._run_binary(
                        power, "Power", "Base", "Exponent", history_name="pow"
                    ),
                ),
            ],
        )
        self._add_tab(
            notebook,
            "Scientific",
            "Unary ops use the display. GCD prompts for two integers.",
            [
                ("Square Root", lambda: self._run_unary(square_root, "sqrt")),
                ("Absolute Value", lambda: self._run_unary(absolute, "abs")),
                ("Factorial", lambda: self._run_unary(factorial_value, "factorial")),
                (
                    "GCD",
                    lambda: self._run_binary(
                        gcd_value,
                        "GCD",
                        "First integer",
                        "Second integer",
                        history_name="gcd",
                    ),
                ),
            ],
        )
        self._add_tab(
            notebook,
            "Trig",
            "Direct trig: degrees in, ratio out. "
            "Inverse trig: ratio in (-1 to 1), degrees out.",
            [
                ("Sine (deg)", lambda: self._run_unary(sine, "sin")),
                ("Cosine (deg)", lambda: self._run_unary(cosine, "cos")),
                ("Tangent (deg)", lambda: self._run_unary(tangent, "tan")),
                ("Arc Sine", lambda: self._run_unary(arcsine, "asin")),
                ("Arc Cosine", lambda: self._run_unary(arccosine, "acos")),
                ("Arc Tangent", lambda: self._run_unary(arctangent, "atan")),
            ],
        )
        self._add_tab(
            notebook,
            "Logs",
            "Uses the current display value.",
            [
                ("Natural Log (ln)", lambda: self._run_unary(natural_log, "ln")),
                ("Log Base 10", lambda: self._run_unary(log_base10, "log10")),
                ("e^x", lambda: self._run_unary(exponential, "exp")),
            ],
        )
        self._add_tab(
            notebook,
            "Convert",
            "Unit and rounding tools for the display value.",
            [
                (
                    "Radians → Degrees",
                    lambda: self._run_unary(degree_conversion, "to_degrees"),
                ),
                (
                    "Degrees → Radians",
                    lambda: self._run_unary(radian_conversion, "to_radians"),
                ),
                ("Floor", lambda: self._run_unary(floor_value, "floor")),
                ("Ceiling", lambda: self._run_unary(ceil_value, "ceil")),
                ("Truncate", lambda: self._run_unary(trunc_value, "trunc")),
            ],
        )
        self._add_tab(
            notebook,
            "Constants",
            "Insert a constant into the display.",
            [
                ("π (PI)", lambda: self._set_constant(math.pi, "π")),
                ("e (Euler)", lambda: self._set_constant(math.e, "e")),
            ],
        )
        self._add_tab(
            notebook,
            "Expression",
            "Evaluate the display with +, -, *, / and parentheses. "
            "Both buttons use the same safe parser.",
            [
                ("Evaluate (=)", lambda: self._run_parser(expression_parser, "Expression")),
                (
                    "Evaluate (alias)",
                    lambda: self._run_parser(evaluate_expression, "Evaluate"),
                ),
            ],
        )
        self._build_history_tab(notebook)

    def _add_tab(
        self,
        notebook: ttk.Notebook,
        title: str,
        hint: str,
        buttons: list[tuple[str, Callable[[], None]]],
    ) -> None:
        frame = ttk.Frame(notebook, padding=PAD_TAB)
        notebook.add(frame, text=title)

        ttk.Label(frame, text=hint, font=FONT_HINT, wraplength=HINT_WRAP).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 16),
        )

        for index, (label, command) in enumerate(buttons):
            ttk.Button(
                frame,
                text=label,
                command=command,
                width=BUTTON_WIDTH,
            ).grid(
                row=1 + index // 2,
                column=index % 2,
                padx=PAD_BUTTON,
                pady=PAD_BUTTON,
                sticky="ew",
                ipady=6,
            )

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

    def _build_history_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=PAD_TAB)
        notebook.add(frame, text="History")

        ttk.Label(
            frame,
            text="Successful calculations appear here automatically.",
            font=FONT_HINT,
            wraplength=HINT_WRAP,
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        text_frame = ttk.Frame(frame)
        text_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_text = tk.Text(
            text_frame,
            height=HISTORY_HEIGHT,
            width=46,
            font=FONT_HISTORY,
            wrap=tk.WORD,
            state="disabled",
            yscrollcommand=scrollbar.set,
        )
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_text.yview)

        self._refresh_history_view()

        button_row = ttk.Frame(frame)
        button_row.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        ttk.Button(
            button_row,
            text="Clear History",
            command=self._clear_history,
            width=16,
        ).pack(side=tk.LEFT, padx=(0, PAD_BUTTON))

        ttk.Button(
            button_row,
            text="Copy Selected",
            command=self._copy_selected_history,
            width=16,
        ).pack(side=tk.LEFT, padx=PAD_BUTTON)

        ttk.Button(
            button_row,
            text="Copy All",
            command=self._copy_all_history,
            width=16,
        ).pack(side=tk.LEFT, padx=PAD_BUTTON)

    def _add_keypad_button(
        self,
        parent: ttk.Frame,
        label: str,
        row: int,
        column: int,
    ) -> None:
        if label == "C":
            command = self._clear
        elif label == "⌫":
            command = self._backspace
        elif label == "=":
            command = self._evaluate_expression
        else:
            command = lambda char=label: self._append(char)

        ttk.Button(parent, text=label, command=command, width=BUTTON_WIDTH_KEYPAD).grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=PAD_BUTTON,
            pady=PAD_BUTTON,
            ipady=10,
        )

    # --- Display helpers ---

    def _display_text(self) -> str:
        return self.display_var.get()

    def _set_display(self, text: str) -> None:
        self.display_var.set(text)

    def _append(self, text: str) -> None:
        current = self._display_text()
        if current == "0":
            if text in "0123456789(":
                self._set_display(text)
            elif text == ".":
                self._set_display("0.")
            elif text in "+-*/":
                self._set_display("0" + text)
            else:
                self._set_display(text)
            return
        self._set_display(current + text)

    def _clear(self) -> None:
        self._set_display("0")

    def _backspace(self) -> None:
        current = self._display_text()
        if len(current) <= 1:
            self._set_display("0")
            return
        self._set_display(current[:-1])

    def _apply_result(self, result: float | int) -> None:
        self._set_display(format_result(result))

    def _show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message, parent=self.root)

    # --- History ---

    def _refresh_history_view(self) -> None:
        if self.history_text is None:
            return

        self.history_text.config(state="normal")
        self.history_text.delete("1.0", tk.END)

        if self.history.is_empty():
            self.history_text.insert(tk.END, "No calculations yet.\n")
        else:
            for entry in self.history.entries():
                self.history_text.insert(tk.END, entry.format_line() + "\n")

        self.history_text.see(tk.END)
        self.history_text.config(state="disabled")

    def _record_success(
        self,
        operation: str,
        input_text: str,
        result: float | int,
    ) -> None:
        entry = self.history.record(operation, input_text, format_result(result))
        if self.history_text is None:
            return

        self.history_text.config(state="normal")
        if self.history.entries() == (entry,):
            self.history_text.delete("1.0", tk.END)
        self.history_text.insert(tk.END, entry.format_line() + "\n")
        self.history_text.see(tk.END)
        self.history_text.config(state="disabled")

    def _clear_history(self) -> None:
        self.history.clear()
        self._refresh_history_view()

    def _copy_all_history(self) -> None:
        if self.history.is_empty():
            self._show_error("History", "There is no history to copy.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(self.history.format_all())

    def _copy_selected_history(self) -> None:
        if self.history_text is None:
            return

        try:
            self.history_text.config(state="normal")
            selected = self.history_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            self._show_error("History", "Select one or more lines to copy.")
            return
        finally:
            self.history_text.config(state="disabled")

        if not selected.strip():
            self._show_error("History", "Select one or more lines to copy.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(selected)

    # --- Memory ---

    def _update_memory_status(self) -> None:
        self.memory_var.set(f"Memory: {format_result(self.memory.recall())}")

    def _read_display_number(self) -> float | None:
        """Read a single number from the display for memory operations."""
        text = self._display_text().strip()
        if not text:
            return None

        try:
            return float(text)
        except ValueError:
            return None

    def _memory_clear(self) -> None:
        self.memory.clear()
        self._update_memory_status()

    def _memory_recall(self) -> None:
        self._set_display(format_result(self.memory.recall()))

    def _memory_add(self) -> None:
        value = self._read_display_number()
        if value is None:
            self._show_error(
                "Memory Error",
                "Display must contain a single number for M+.",
            )
            return
        self.memory.add(value)
        self._update_memory_status()

    def _memory_subtract(self) -> None:
        value = self._read_display_number()
        if value is None:
            self._show_error(
                "Memory Error",
                "Display must contain a single number for M-.",
            )
            return
        self.memory.subtract(value)
        self._update_memory_status()

    # --- Dialogs ---

    def _prompt_number_list(self, title: str) -> list[float] | None:
        initial = self._display_text()
        if initial == "0":
            initial = ""

        text = simpledialog.askstring(
            title,
            "Enter numbers separated by commas (e.g. 5, 3, 2):",
            initialvalue=initial,
            parent=self.root,
        )
        if text is None:
            return None

        try:
            values = parse_number_list(text)
        except ValueError:
            return None

        if not values:
            self._show_error("Invalid Input", "Enter at least one number.")
            return None

        return values

    def _prompt_two_floats(
        self,
        title: str,
        label_a: str,
        label_b: str,
    ) -> tuple[float, float] | None:
        first = simpledialog.askfloat(
            title,
            f"{label_a}:",
            parent=self.root,
        )
        if first is None:
            return None

        second = simpledialog.askfloat(
            title,
            f"{label_b}:",
            parent=self.root,
        )
        if second is None:
            return None

        return first, second

    # --- Operation runners (delegate to core / parser) ---

    def _handle_core(
        self,
        compute: Callable[[], float | int],
        *,
        operation: str,
        input_text: str,
    ) -> None:
        try:
            result = compute()
            self._apply_result(result)
            self._record_success(operation, input_text, result)
        except CalculatorError as error:
            self._show_error("Calculator Error", str(error))
        except (ValueError, OverflowError, ArithmeticError):
            self._show_error("Invalid Input", "Could not complete the operation.")

    def _run_unary(
        self,
        operation: Callable[[float], float | int],
        history_name: str,
    ) -> None:
        input_text = self._display_text()
        self._handle_core(
            lambda: operation(float(input_text)),
            operation=history_name,
            input_text=input_text,
        )

    def _run_sequence(
        self,
        operation: Callable[[Sequence[float]], float],
        title: str,
    ) -> None:
        values = self._prompt_number_list(title)
        if values is None:
            return
        input_text = format_value_list(values)
        self._handle_core(
            lambda: operation(values),
            operation=title,
            input_text=input_text,
        )

    def _run_binary(
        self,
        operation: Callable[[float, float], float | int],
        title: str,
        label_a: str,
        label_b: str,
        *,
        history_name: str | None = None,
    ) -> None:
        values = self._prompt_two_floats(title, label_a, label_b)
        if values is None:
            return
        operation_name = history_name or title
        input_text = f"{format_result(values[0])}, {format_result(values[1])}"
        self._handle_core(
            lambda: operation(values[0], values[1]),
            operation=operation_name,
            input_text=input_text,
        )

    def _set_constant(self, value: float, constant_name: str) -> None:
        self._set_display(format_result(value))
        self._record_success("Constant", constant_name, value)

    def _evaluate_expression(self) -> None:
        self._run_parser(expression_parser, "Expression")

    def _run_parser(
        self,
        operation: Callable[[str], float],
        history_name: str,
    ) -> None:
        expression = self._display_text()
        try:
            result = operation(expression)
            self._apply_result(result)
            self._record_success(history_name, expression, result)
        except ZeroDivisionError:
            self._show_error("Expression Error", "Cannot divide by zero.")
        except ParserError as error:
            self._show_error("Expression Error", str(error))
        except ValueError:
            self._show_error("Invalid Input", "Could not read the expression.")

    # --- Appearance ---

    def _build_appearance_menu(self) -> None:
        self.menubar = tk.Menu(self.root)
        self.appearance_menu = tk.Menu(self.menubar, tearoff=0)

        self.appearance_menu.add_radiobutton(
            label="Light",
            variable=self.theme_menu_var,
            value="Light",
            command=lambda: self._select_theme("Light"),
        )
        self.appearance_menu.add_radiobutton(
            label="Dark",
            variable=self.theme_menu_var,
            value="Dark",
            command=lambda: self._select_theme("Dark"),
        )
        self.appearance_menu.add_separator()
        self.appearance_menu.add_radiobutton(
            label="Blue",
            variable=self.theme_menu_var,
            value="Blue",
            command=lambda: self._select_theme("Blue"),
        )
        self.appearance_menu.add_radiobutton(
            label="Green",
            variable=self.theme_menu_var,
            value="Green",
            command=lambda: self._select_theme("Green"),
        )

        self.menubar.add_cascade(label="Appearance", menu=self.appearance_menu)
        self.menubar.add_cascade(label="Help", menu=self.help_menu)
        self.root.config(menu=self.menubar)

    def _build_help_menu(self) -> None:
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.help_menu.add_command(label="About", command=self._show_about_dialog)

    def _show_about_dialog(self) -> None:
        about_text = (
            f"{__app_name__}\n"
            f"Version: {__version__}\n"
            f"\n"
            f"{__description__}\n"
            f"\n"
            f"Author: {__author__}\n"
            f"Python Version: {sys.version.split()[0]}"
        )
        messagebox.showinfo(f"About {__app_name__}", about_text, parent=self.root)

    def _set_window_icon(self) -> None:
        """Set application window icon with graceful fallback if missing."""
        icon_paths = [
            Path("icon.ico"),
            Path("icon.png"),
            Path("assets/icon.ico"),
            Path("assets/icon.png"),
        ]
        
        for icon_path in icon_paths:
            if icon_path.exists():
                try:
                    self.root.iconbitmap(str(icon_path))
                    return
                except tk.TclError:
                    continue
        
        # Icon not found or failed to load - continue without icon

    def update_theme_status(self) -> None:
        self.theme_var.set(f"Theme: {self.theme_manager.current_theme}")

    def _select_theme(self, name: str) -> None:
        self.theme_manager.set_theme(name)
        self.theme_menu_var.set(self.theme_manager.current_theme)
        self.theme_manager.apply(self)

    # --- Keyboard shortcuts ---

    def _bind_keyboard(self) -> None:
        # Keypad-style input on the window (when focus is not in the display).
        for digit in "0123456789":
            self.root.bind(digit, lambda _e, char=digit: self._append(char))

        for char in "+-*/().":
            self.root.bind(char, lambda _e, char=char: self._append(char))

        self.root.bind("=", lambda _e: self._evaluate_expression())
        self.root.bind("<Escape>", lambda _e: self._clear())
        self.root.bind("<Delete>", lambda _e: self._clear())

        # Display field: allow free typing (e.g. 2+3); shortcuts only.
        if self.display_entry is not None:
            self.display_entry.bind("<Return>", lambda _e: self._evaluate_expression())
            self.display_entry.bind("<KP_Enter>", lambda _e: self._evaluate_expression())
            self.display_entry.bind("=", lambda _e: self._evaluate_expression())
            self.display_entry.bind("<Escape>", lambda _e: self._clear())


def run_gui() -> None:
    """Create the main window and start the event loop."""
    root = tk.Tk()
    CalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
