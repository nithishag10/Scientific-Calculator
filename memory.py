"""Calculator memory state (MC, MR, M+, M-)."""

from __future__ import annotations


class CalculatorMemory:
    """Stores one numeric value for recall and accumulate operations."""

    def __init__(self) -> None:
        self._value = 0.0

    def clear(self) -> None:
        """Reset memory to zero (MC)."""
        self._value = 0.0

    def recall(self) -> float:
        """Return the stored value (MR)."""
        return self._value

    def add(self, amount: float) -> None:
        """Add amount to memory (M+)."""
        self._value += amount

    def subtract(self, amount: float) -> None:
        """Subtract amount from memory (M-)."""
        self._value -= amount

    @property
    def value(self) -> float:
        """Current memory contents."""
        return self._value
