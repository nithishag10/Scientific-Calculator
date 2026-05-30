"""In-memory calculation history for the calculator GUI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HistoryEntry:
    """One successful calculation."""

    operation: str
    input_text: str
    result_text: str
    timestamp: datetime

    def format_calculation(self) -> str:
        """Format the calculation body (without timestamp)."""
        if self.operation in ("Expression", "Evaluate"):
            return f"{self.input_text} = {self.result_text}"
        if self.operation == "Constant":
            return f"{self.input_text} = {self.result_text}"
        return f"{self.operation}({self.input_text}) = {self.result_text}"

    def format_line(self) -> str:
        """Format entry for display (e.g. ``12:35:10 | 5 + 3 = 8``)."""
        time_str = self.timestamp.strftime("%H:%M:%S")
        return f"{time_str} | {self.format_calculation()}"


class HistoryManager:
    """Session history stored in memory for the lifetime of the application."""

    def __init__(self) -> None:
        self._entries: list[HistoryEntry] = []

    def record(
        self,
        operation: str,
        input_text: str,
        result_text: str,
        *,
        timestamp: datetime | None = None,
    ) -> HistoryEntry:
        """Append a successful calculation and return the new entry."""
        entry = HistoryEntry(
            operation=operation,
            input_text=input_text,
            result_text=result_text,
            timestamp=timestamp or datetime.now(),
        )
        self._entries.append(entry)
        return entry

    def entries(self) -> tuple[HistoryEntry, ...]:
        """Return all entries in chronological order."""
        return tuple(self._entries)

    def clear(self) -> None:
        """Remove every entry from the session history."""
        self._entries.clear()

    def is_empty(self) -> bool:
        return not self._entries

    def format_all(self) -> str:
        """Return every entry as newline-separated text."""
        return "\n".join(entry.format_line() for entry in self._entries)


# Backward-compatible alias
HistoryStore = HistoryManager
