import unittest
from pathlib import Path

from compilador.errors import SemanticError
from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.semantic import SemanticAnalyzer


def analyze(source):
    program = Parser(Lexer(source).scan_tokens()).parse()
    return SemanticAnalyzer().analyze(program)


class SemanticAnalyzerTest(unittest.TestCase):
    def test_accepts_minimal_program(self):
        source = Path("examples/programa_minimo.lang").read_text(encoding="utf-8")

        program = analyze(source)

        self.assertEqual(program.declarations[0].name, "main")

    def test_accepts_function_call(self):
        analyze(
            """
            fn soma(int a, int b) -> int {
              return a + b;
            }

            fn main() -> int {
              return soma(1, 2);
            }
            """
        )

    def test_accepts_procedure_call_statement(self):
        analyze(
            """
            proc mostra(int valor) {
              return;
            }

            fn main() -> int {
              mostra(1);
              return 0;
            }
            """
        )

    def test_accepts_int_to_float_assignment(self):
        analyze(
            """
            fn main() -> float {
              float x = 1;
              return x;
            }
            """
        )

    def test_rejects_missing_main(self):
        with self.assertRaisesRegex(SemanticError, "main"):
            analyze(
                """
                fn soma(int a, int b) -> int {
                  return a + b;
                }
                """
            )

    def test_rejects_undeclared_variable(self):
        with self.assertRaisesRegex(SemanticError, "nao declarada"):
            analyze(
                """
                fn main() -> int {
                  x = 1;
                  return x;
                }
                """
            )

    def test_rejects_duplicate_variable_in_same_scope(self):
        with self.assertRaisesRegex(SemanticError, "ja declarada"):
            analyze(
                """
                fn main() -> int {
                  int x;
                  int x;
                  return 0;
                }
                """
            )

    def test_rejects_incompatible_assignment(self):
        with self.assertRaisesRegex(SemanticError, "tipo incompativel"):
            analyze(
                """
                fn main() -> int {
                  int x;
                  x = 'a';
                  return x;
                }
                """
            )

    def test_rejects_non_bool_if_condition(self):
        with self.assertRaisesRegex(SemanticError, "condicao do if deve ser bool"):
            analyze(
                """
                fn main() -> int {
                  if (1) {
                    return 1;
                  }
                  return 0;
                }
                """
            )

    def test_rejects_wrong_return_type(self):
        with self.assertRaisesRegex(SemanticError, "tipo de retorno incompativel"):
            analyze(
                """
                fn main() -> int {
                  return 1.5;
                }
                """
            )

    def test_rejects_wrong_argument_count(self):
        with self.assertRaisesRegex(SemanticError, "esperava 2 argumento"):
            analyze(
                """
                fn soma(int a, int b) -> int {
                  return a + b;
                }

                fn main() -> int {
                  return soma(1);
                }
                """
            )

    def test_rejects_wrong_argument_type(self):
        with self.assertRaisesRegex(SemanticError, "argumento 2"):
            analyze(
                """
                fn soma(int a, int b) -> int {
                  return a + b;
                }

                fn main() -> int {
                  return soma(1, 'b');
                }
                """
            )

    def test_rejects_procedure_call_argument_type(self):
        with self.assertRaisesRegex(SemanticError, "argumento 1"):
            analyze(
                """
                proc mostra(int valor) {
                  return;
                }

                fn main() -> int {
                  mostra('x');
                  return 0;
                }
                """
            )

    def test_rejects_procedure_returning_value(self):
        with self.assertRaisesRegex(SemanticError, "procedimento nao deve retornar valor"):
            analyze(
                """
                proc escreve() {
                  return 1;
                }

                fn main() -> int {
                  return 0;
                }
                """
            )


if __name__ == "__main__":
    unittest.main()
