"""Expression parsing and safe stack-based evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable


class ParserError(Exception):
    """Base exception for expression parsing and evaluation failures."""


class InvalidTokenError(ParserError, ValueError):
    """Raised when the expression contains an unrecognized token."""


class InvalidExpressionError(ParserError, ValueError):
    """Raised when the expression structure is invalid."""


class DivisionByZeroError(ParserError, ZeroDivisionError):
    """Raised when evaluation encounters division by zero."""


class TokenKind(Enum):
    NUMBER = auto()
    OPERATOR = auto()
    LPAREN = auto()
    RPAREN = auto()


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    value: str | float


PRECEDENCE = {
    "+": 1,
    "-": 1,
    "*": 2,
    "/": 2,
}


def _is_digit(char: str) -> bool:
    return char.isdigit()


def _is_number_start(expression: str, index: int) -> bool:
    char = expression[index]
    if _is_digit(char) or char == ".":
        return True
    if char != "-" or not _is_unary_minus(expression, index):
        return False

    next_index = index + 1
    while next_index < len(expression) and expression[next_index].isspace():
        next_index += 1

    if next_index >= len(expression):
        return False

    return _is_digit(expression[next_index]) or expression[next_index] == "."


def _is_unary_minus(expression: str, index: int) -> bool:
    if expression[index] != "-":
        return False

    previous = index - 1
    while previous >= 0 and expression[previous].isspace():
        previous -= 1

    if previous < 0:
        return True

    return expression[previous] in "(+-*/"


def _read_number(expression: str, start: int) -> tuple[float, int]:
    index = start
    if expression[index] == "-":
        index += 1

    if index >= len(expression):
        raise InvalidTokenError(f"Invalid number at position {start + 1}")

    if expression[index] == ".":
        index += 1
        if index >= len(expression) or not _is_digit(expression[index]):
            raise InvalidTokenError(f"Invalid number at position {start + 1}")
        while index < len(expression) and _is_digit(expression[index]):
            index += 1
    else:
        while index < len(expression) and _is_digit(expression[index]):
            index += 1
        if index < len(expression) and expression[index] == ".":
            index += 1
            while index < len(expression) and _is_digit(expression[index]):
                index += 1

    number_text = expression[start:index]
    try:
        return float(number_text), index
    except ValueError as exc:
        raise InvalidTokenError(f"Invalid number '{number_text}'") from exc


def tokenize(expression: str) -> list[Token]:
    """Convert an infix expression string into a token list."""
    if not expression or not expression.strip():
        raise InvalidExpressionError("Expression cannot be empty")

    tokens: list[Token] = []
    index = 0
    length = len(expression)
    expect_operand = True

    while index < length:
        char = expression[index]

        if char.isspace():
            index += 1
            continue

        if _is_number_start(expression, index):
            number, index = _read_number(expression, index)
            tokens.append(Token(TokenKind.NUMBER, number))
            expect_operand = False
            continue

        if char == "(":
            tokens.append(Token(TokenKind.LPAREN, "("))
            index += 1
            expect_operand = True
            continue

        if char == ")":
            tokens.append(Token(TokenKind.RPAREN, ")"))
            index += 1
            expect_operand = False
            continue

        if char in PRECEDENCE:
            if char == "-" and expect_operand:
                next_index = index + 1
                while next_index < length and expression[next_index].isspace():
                    next_index += 1

                if next_index < length and expression[next_index] == "(":
                    tokens.append(Token(TokenKind.NUMBER, 0.0))
                    tokens.append(Token(TokenKind.OPERATOR, "-"))
                    index += 1
                    expect_operand = True
                    continue

                number, index = _read_number(expression, index)
                tokens.append(Token(TokenKind.NUMBER, number))
                expect_operand = False
                continue

            if expect_operand:
                raise InvalidExpressionError(
                    f"Operator '{char}' found where an operand was expected"
                )

            tokens.append(Token(TokenKind.OPERATOR, char))
            index += 1
            expect_operand = True
            continue

        raise InvalidTokenError(f"Invalid character '{char}' at position {index + 1}")

    if expect_operand and tokens:
        raise InvalidExpressionError("Expression ends with an operator")

    return tokens


def infix_to_postfix(tokens: Iterable[Token]) -> list[Token]:
    """Convert infix tokens to postfix notation using the shunting-yard algorithm."""
    output: list[Token] = []
    operators: list[Token] = []

    for token in tokens:
        if token.kind == TokenKind.NUMBER:
            output.append(token)

        elif token.kind == TokenKind.OPERATOR:
            while (
                operators
                and operators[-1].kind == TokenKind.OPERATOR
                and PRECEDENCE[operators[-1].value] >= PRECEDENCE[token.value]
            ):
                output.append(operators.pop())
            operators.append(token)

        elif token.kind == TokenKind.LPAREN:
            operators.append(token)

        elif token.kind == TokenKind.RPAREN:
            while operators and operators[-1].kind != TokenKind.LPAREN:
                output.append(operators.pop())

            if not operators:
                raise InvalidExpressionError("Mismatched parentheses")

            operators.pop()

            if operators and operators[-1].kind == TokenKind.LPAREN:
                raise InvalidExpressionError("Mismatched parentheses")

        else:
            raise InvalidTokenError(f"Unexpected token: {token.value}")

    while operators:
        top = operators.pop()
        if top.kind in (TokenKind.LPAREN, TokenKind.RPAREN):
            raise InvalidExpressionError("Mismatched parentheses")
        output.append(top)

    return output


def evaluate_postfix(tokens: Iterable[Token]) -> float:
    """Evaluate a postfix token list using a stack."""
    stack: list[float] = []

    for token in tokens:
        if token.kind == TokenKind.NUMBER:
            stack.append(float(token.value))
            continue

        if token.kind != TokenKind.OPERATOR:
            raise InvalidExpressionError("Postfix expression contains invalid tokens")

        if len(stack) < 2:
            raise InvalidExpressionError("Invalid expression")

        right = stack.pop()
        left = stack.pop()

        if token.value == "+":
            stack.append(left + right)
        elif token.value == "-":
            stack.append(left - right)
        elif token.value == "*":
            stack.append(left * right)
        elif token.value == "/":
            if right == 0:
                raise DivisionByZeroError("Cannot divide by zero")
            stack.append(left / right)
        else:
            raise InvalidTokenError(f"Unknown operator '{token.value}'")

    if len(stack) != 1:
        raise InvalidExpressionError("Invalid expression")

    return stack[0]


def parse_and_evaluate(expression: str) -> float:
    """Parse an infix expression and evaluate it safely."""
    tokens = tokenize(expression)
    postfix = infix_to_postfix(tokens)
    return evaluate_postfix(postfix)


def expression_parser(expression: str) -> float:
    """Parse and evaluate an infix arithmetic expression."""
    return parse_and_evaluate(expression)


def evaluate_expression(expression: str) -> float:
    """Alias for expression_parser; kept for CLI/GUI parity."""
    return parse_and_evaluate(expression)
