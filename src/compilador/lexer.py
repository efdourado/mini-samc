from __future__ import annotations

from .errors import LexerError
from .tokens import KEYWORDS, Token, TokenType


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1

    def scan_tokens(self) -> list[Token]:
        tokens: list[Token] = []

        while True:
            self._skip_ignored()
            if self._is_at_end():
                break

            self.start = self.current
            start_line = self.line
            start_column = self.column
            tokens.append(self._scan_token(start_line, start_column))

        tokens.append(Token(TokenType.EOF, "", None, self.line, self.column))
        return tokens

    def _scan_token(self, line: int, column: int) -> Token:
        char = self._advance()

        if char.isalpha() or char == "_":
            return self._identifier(line, column)
        if char.isdigit():
            return self._number(line, column)

        if char == "'":
            return self._char_literal(line, column)
        if char == "(":
            return self._token(TokenType.LEFT_PAREN, line, column)
        if char == ")":
            return self._token(TokenType.RIGHT_PAREN, line, column)
        if char == "{":
            return self._token(TokenType.LEFT_BRACE, line, column)
        if char == "}":
            return self._token(TokenType.RIGHT_BRACE, line, column)
        if char == ",":
            return self._token(TokenType.COMMA, line, column)
        if char == ";":
            return self._token(TokenType.SEMICOLON, line, column)
        if char == "+":
            return self._token(TokenType.PLUS, line, column)
        if char == "-":
            if self._match(">"):
                return self._token(TokenType.ARROW, line, column)
            return self._token(TokenType.MINUS, line, column)
        if char == "*":
            return self._token(TokenType.STAR, line, column)
        if char == "/":
            return self._token(TokenType.SLASH, line, column)
        if char == "%":
            return self._token(TokenType.PERCENT, line, column)
        if char == "!":
            if self._match("="):
                return self._token(TokenType.BANG_EQUAL, line, column)
            return self._token(TokenType.BANG, line, column)
        if char == "=":
            if self._match("="):
                return self._token(TokenType.EQUAL_EQUAL, line, column)
            return self._token(TokenType.ASSIGN, line, column)
        if char == ">":
            if self._match("="):
                return self._token(TokenType.GREATER_EQUAL, line, column)
            return self._token(TokenType.GREATER, line, column)
        if char == "<":
            if self._match("="):
                return self._token(TokenType.LESS_EQUAL, line, column)
            return self._token(TokenType.LESS, line, column)
        if char == "&":
            if self._match("&"):
                return self._token(TokenType.AND_AND, line, column)
            raise LexerError("esperado '&' apos '&'", line, column)
        if char == "|":
            if self._match("|"):
                return self._token(TokenType.OR_OR, line, column)
            raise LexerError("esperado '|' apos '|'", line, column)

        raise LexerError(f"caractere inesperado {char!r}", line, column)

    def _identifier(self, line: int, column: int) -> Token:
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()

        lexeme = self.source[self.start : self.current]
        token_type = KEYWORDS.get(lexeme, TokenType.IDENTIFIER)
        literal = None
        if token_type == TokenType.KW_TRUE:
            literal = True
        elif token_type == TokenType.KW_FALSE:
            literal = False
        return Token(token_type, lexeme, literal, line, column)

    def _number(self, line: int, column: int) -> Token:
        while self._peek().isdigit():
            self._advance()

        is_float = False
        if self._peek() == "." and self._peek_next().isdigit():
            is_float = True
            self._advance()
            while self._peek().isdigit():
                self._advance()

        lexeme = self.source[self.start : self.current]
        if is_float:
            return Token(TokenType.FLOAT_LITERAL, lexeme, float(lexeme), line, column)
        return Token(TokenType.INT_LITERAL, lexeme, int(lexeme), line, column)

    def _char_literal(self, line: int, column: int) -> Token:
        if self._is_at_end() or self._peek() == "\n":
            raise LexerError("literal de char nao terminado", line, column)

        if self._match("\\"):
            value = self._escape_sequence(line, column)
        else:
            value = self._advance()

        if not self._match("'"):
            raise LexerError("literal de char deve conter um unico caractere", line, column)

        return Token(
            TokenType.CHAR_LITERAL,
            self.source[self.start : self.current],
            value,
            line,
            column,
        )

    def _escape_sequence(self, line: int, column: int) -> str:
        if self._is_at_end():
            raise LexerError("sequencia de escape nao terminada", line, column)

        char = self._advance()
        escapes = {
            "n": "\n",
            "t": "\t",
            "r": "\r",
            "0": "\0",
            "'": "'",
            '"': '"',
            "\\": "\\",
        }
        if char not in escapes:
            raise LexerError(f"sequencia de escape invalida '\\{char}'", line, column)
        return escapes[char]

    def _skip_ignored(self) -> None:
        while not self._is_at_end():
            char = self._peek()

            if char in (" ", "\r", "\t"):
                self._advance()
                continue
            if char == "\n":
                self._advance()
                continue
            if char == "/" and self._peek_next() == "/":
                self._skip_line_comment()
                continue
            if char == "/" and self._peek_next() == "*":
                self._skip_block_comment()
                continue

            break

    def _skip_line_comment(self) -> None:
        while not self._is_at_end() and self._peek() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        line = self.line
        column = self.column
        self._advance()
        self._advance()

        while not self._is_at_end():
            if self._peek() == "*" and self._peek_next() == "/":
                self._advance()
                self._advance()
                return
            self._advance()

        raise LexerError("comentario de bloco nao terminado", line, column)

    def _token(self, token_type: TokenType, line: int, column: int) -> Token:
        return Token(token_type, self.source[self.start : self.current], None, line, column)

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self.source[self.current] != expected:
            return False
        self._advance()
        return True

    def _advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)
