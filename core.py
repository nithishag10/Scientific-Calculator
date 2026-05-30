"""Core mathematical operations for the scientific calculator."""

from __future__ import annotations

import math
from typing import Sequence


class CalculatorError(Exception):
    """Base exception for calculator operation failures."""


class EmptySequenceError(CalculatorError, ValueError):
    """Raised when an operation requires a non-empty sequence."""


class DivisionByZeroError(CalculatorError, ZeroDivisionError):
    """Raised when division by zero is attempted."""


class InvalidDomainError(CalculatorError, ValueError):
    """Raised when a value is outside a function's valid domain."""


def _require_non_empty(numbers: Sequence[float], operation: str) -> None:
    if not numbers:
        raise EmptySequenceError(f"{operation} requires at least one number")


def _require_integer(value: float, operation: str) -> int:
    if value != int(value):
        raise InvalidDomainError(f"{operation} requires an integer value")
    return int(value)


def _require_positive(value: float, operation: str = "Logarithm") -> None:
    if value <= 0:
        raise InvalidDomainError(f"{operation} is not defined for non-positive numbers")


def add(numbers: Sequence[float]) -> float:
    """Return the sum of all numbers in the sequence."""
    return float(sum(numbers))


def sub(numbers: Sequence[float]) -> float:
    """Return the cumulative difference of numbers (first minus the rest)."""
    _require_non_empty(numbers, "Subtraction")
    result = float(numbers[0])
    for value in numbers[1:]:
        result -= value
    return result


def mul(numbers: Sequence[float]) -> float:
    """Return the product of all numbers in the sequence."""
    result = 1.0
    for value in numbers:
        result *= value
    return result


def div(numbers: Sequence[float]) -> float:
    """Return the cumulative quotient of numbers (first divided by the rest)."""
    _require_non_empty(numbers, "Division")
    result = float(numbers[0])
    for value in numbers[1:]:
        if value == 0:
            raise DivisionByZeroError("Cannot divide by zero")
        result /= value
    return result


def power(x: float, y: float) -> float:
    """Return x raised to the power of y."""
    return math.pow(x, y)


def square_root(x: float) -> float:
    """Return the non-negative square root of x."""
    if x < 0:
        raise InvalidDomainError("Square root is not defined for negative numbers")
    return math.sqrt(x)


def absolute(x: float) -> float:
    """Return the absolute value of x."""
    return abs(x)


def factorial_value(x: float) -> int:
    """Return the factorial of a non-negative integer."""
    if x < 0:
        raise InvalidDomainError("Factorial is not defined for negative numbers")
    n = _require_integer(x, "Factorial")
    return math.factorial(n)


def gcd_value(a: float, b: float) -> int:
    """Return the greatest common divisor of two integers."""
    return math.gcd(_require_integer(a, "GCD"), _require_integer(b, "GCD"))


def sine(x: float) -> float:
    """Return the sine of x, where x is in degrees."""
    return math.sin(math.radians(x))


def cosine(x: float) -> float:
    """Return the cosine of x, where x is in degrees."""
    return math.cos(math.radians(x))


def tangent(x: float) -> float:
    """Return the tangent of x, where x is in degrees."""
    return math.tan(math.radians(x))


def arcsine(x: float) -> float:
    """Return the arc sine of x in degrees."""
    if x < -1 or x > 1:
        raise InvalidDomainError("Arc sine input must be between -1 and 1")
    return math.degrees(math.asin(x))


def arccosine(x: float) -> float:
    """Return the arc cosine of x in degrees."""
    if x < -1 or x > 1:
        raise InvalidDomainError("Arc cosine input must be between -1 and 1")
    return math.degrees(math.acos(x))


def arctangent(x: float) -> float:
    """Return the arc tangent of x in degrees."""
    return math.degrees(math.atan(x))


def natural_log(x: float) -> float:
    """Return the natural logarithm of x."""
    _require_positive(x)
    return math.log(x)


def log_base10(x: float) -> float:
    """Return the base-10 logarithm of x."""
    _require_positive(x)
    return math.log10(x)


def exponential(x: float) -> float:
    """Return e raised to the power of x."""
    return math.exp(x)


def degree_conversion(x: float) -> float:
    """Convert radians to degrees."""
    return math.degrees(x)


def radian_conversion(x: float) -> float:
    """Convert degrees to radians."""
    return math.radians(x)


def floor_value(x: float) -> int:
    """Return the largest integer less than or equal to x."""
    return math.floor(x)


def ceil_value(x: float) -> int:
    """Return the smallest integer greater than or equal to x."""
    return math.ceil(x)


def trunc_value(x: float) -> int:
    """Return the integer part of x by truncating toward zero."""
    return math.trunc(x)
