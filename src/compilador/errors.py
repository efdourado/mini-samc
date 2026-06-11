from __future__ import annotations

from .tokens import Token


class CompilerError(Exception):
    """Erro base do compilador."""


class LexerError(CompilerError):
    """Erro encontrado durante a analise lexica."""

    def __init__(self, message: str, line: int, column: int) -> None:
        super().__init__(f"erro lexico em linha {line}, coluna {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class ParserError(CompilerError):
    """Erro encontrado durante a analise sintatica."""

    def __init__(self, message: str, token: Token) -> None:
        super().__init__(
            f"erro sintatico em linha {token.line}, coluna {token.column}: {message}"
        )
        self.message = message
        self.token = token


class SemanticError(CompilerError):
    """Erro encontrado durante a analise semantica."""

    def __init__(self, message: str, token: Token) -> None:
        super().__init__(
            f"erro semantico em linha {token.line}, coluna {token.column}: {message}"
        )
        self.message = message
        self.token = token


class CodegenError(CompilerError):
    """Erro encontrado durante a geracao de codigo."""

    def __init__(self, message: str, token: Token) -> None:
        super().__init__(
            f"erro de geracao em linha {token.line}, coluna {token.column}: {message}"
        )
        self.message = message
        self.token = token
