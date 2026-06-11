from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional


class TokenType(Enum):
    EOF = auto()

    IDENTIFIER = auto()
    INT_LITERAL = auto()
    FLOAT_LITERAL = auto()
    CHAR_LITERAL = auto()

    KW_FN = auto()
    KW_PROC = auto()
    KW_RETURN = auto()
    KW_IF = auto()
    KW_ELSE = auto()
    KW_WHILE = auto()
    KW_INT = auto()
    KW_FLOAT = auto()
    KW_CHAR = auto()
    KW_BOOL = auto()
    KW_TRUE = auto()
    KW_FALSE = auto()
    KW_VOID = auto()

    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    SEMICOLON = auto()
    ARROW = auto()

    ASSIGN = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    BANG = auto()

    EQUAL_EQUAL = auto()
    BANG_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    AND_AND = auto()
    OR_OR = auto()


KEYWORDS = {
    "fn": TokenType.KW_FN,
    "proc": TokenType.KW_PROC,
    "return": TokenType.KW_RETURN,
    "if": TokenType.KW_IF,
    "else": TokenType.KW_ELSE,
    "while": TokenType.KW_WHILE,
    "int": TokenType.KW_INT,
    "float": TokenType.KW_FLOAT,
    "char": TokenType.KW_CHAR,
    "bool": TokenType.KW_BOOL,
    "true": TokenType.KW_TRUE,
    "false": TokenType.KW_FALSE,
    "void": TokenType.KW_VOID,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    literal: Optional[Any]
    line: int
    column: int

    def __str__(self) -> str:
        location = f"{self.line}:{self.column}"
        if self.literal is None:
            return f"{location} {self.type.name} {self.lexeme!r}"
        return f"{location} {self.type.name} {self.lexeme!r} -> {self.literal!r}"
