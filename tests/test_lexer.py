import unittest
from pathlib import Path

from compilador.errors import LexerError
from compilador.lexer import Lexer
from compilador.tokens import TokenType


def token_types(source):
    return [token.type for token in Lexer(source).scan_tokens()]


class LexerTest(unittest.TestCase):
    def test_tokenizes_minimal_program(self):
        source = Path("examples/programa_minimo.lang").read_text(encoding="utf-8")
        types = token_types(source)

        self.assertEqual(types[0], TokenType.KW_FN)
        self.assertIn(TokenType.KW_IF, types)
        self.assertIn(TokenType.KW_ELSE, types)
        self.assertIn(TokenType.KW_WHILE, types)
        self.assertIn(TokenType.KW_RETURN, types)
        self.assertEqual(types[-1], TokenType.EOF)

    def test_tokenizes_literals(self):
        tokens = Lexer("123 45.67 'a' '\\n' true false").scan_tokens()

        self.assertEqual(tokens[0].type, TokenType.INT_LITERAL)
        self.assertEqual(tokens[0].literal, 123)
        self.assertEqual(tokens[1].type, TokenType.FLOAT_LITERAL)
        self.assertEqual(tokens[1].literal, 45.67)
        self.assertEqual(tokens[2].type, TokenType.CHAR_LITERAL)
        self.assertEqual(tokens[2].literal, "a")
        self.assertEqual(tokens[3].type, TokenType.CHAR_LITERAL)
        self.assertEqual(tokens[3].literal, "\n")
        self.assertEqual(tokens[4].literal, True)
        self.assertEqual(tokens[5].literal, False)

    def test_skips_comments(self):
        source = "// linha\nint x; /* bloco */ x = 1;"

        self.assertEqual(
            token_types(source),
            [
                TokenType.KW_INT,
                TokenType.IDENTIFIER,
                TokenType.SEMICOLON,
                TokenType.IDENTIFIER,
                TokenType.ASSIGN,
                TokenType.INT_LITERAL,
                TokenType.SEMICOLON,
                TokenType.EOF,
            ],
        )

    def test_tracks_line_and_column(self):
        tokens = Lexer("\n  int x;").scan_tokens()

        self.assertEqual(tokens[0].line, 2)
        self.assertEqual(tokens[0].column, 3)

    def test_rejects_unknown_character(self):
        with self.assertRaisesRegex(LexerError, "caractere inesperado"):
            Lexer("@").scan_tokens()

    def test_rejects_unterminated_block_comment(self):
        with self.assertRaisesRegex(LexerError, "comentario de bloco nao terminado"):
            Lexer("/* aberto").scan_tokens()

    def test_rejects_invalid_char_literal(self):
        with self.assertRaisesRegex(LexerError, "unico caractere"):
            Lexer("'ab'").scan_tokens()


if __name__ == "__main__":
    unittest.main()
