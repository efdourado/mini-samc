import unittest
from pathlib import Path

from compilador import ast
from compilador.errors import ParserError
from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.tokens import TokenType


def parse(source):
    return Parser(Lexer(source).scan_tokens()).parse()


class ParserTest(unittest.TestCase):
    def test_parses_minimal_program(self):
        source = Path("examples/programa_minimo.lang").read_text(encoding="utf-8")
        program = parse(source)

        self.assertEqual(len(program.declarations), 1)
        function = program.declarations[0]
        self.assertIsInstance(function, ast.FunctionDecl)
        self.assertEqual(function.name, "main")
        self.assertEqual(function.return_type, "int")
        self.assertEqual(len(function.params), 0)
        self.assertGreaterEqual(len(function.body.statements), 5)
        self.assertIsInstance(function.body.statements[0], ast.VarDecl)
        self.assertIsInstance(function.body.statements[2], ast.IfStmt)
        self.assertIsInstance(function.body.statements[3], ast.WhileStmt)
        self.assertIsInstance(function.body.statements[-1], ast.ReturnStmt)

    def test_parses_function_parameters_and_initializer(self):
        program = parse(
            """
            fn soma(int a, int b) -> int {
              int total = a + b;
              return total;
            }
            """
        )

        function = program.declarations[0]
        self.assertEqual(function.name, "soma")
        self.assertEqual([param.name for param in function.params], ["a", "b"])
        self.assertEqual([param.type_name for param in function.params], ["int", "int"])
        var_decl = function.body.statements[0]
        self.assertIsInstance(var_decl, ast.VarDecl)
        self.assertIsInstance(var_decl.initializer, ast.Binary)

    def test_parses_procedure(self):
        program = parse(
            """
            proc mostra(int valor, char letra) {
              valor = valor + 1;
            }
            """
        )

        procedure = program.declarations[0]
        self.assertIsInstance(procedure, ast.ProcedureDecl)
        self.assertEqual(procedure.name, "mostra")
        self.assertEqual(len(procedure.params), 2)

    def test_parses_call_statement(self):
        program = parse(
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

        main = program.declarations[1]
        self.assertIsInstance(main.body.statements[0], ast.CallStmt)
        self.assertEqual(main.body.statements[0].name, "mostra")

    def test_operator_precedence(self):
        program = parse(
            """
            fn main() -> int {
              return 1 + 2 * 3;
            }
            """
        )

        return_stmt = program.declarations[0].body.statements[0]
        expression = return_stmt.value
        self.assertIsInstance(expression, ast.Binary)
        self.assertEqual(expression.operator.type, TokenType.PLUS)
        self.assertIsInstance(expression.right, ast.Binary)
        self.assertEqual(expression.right.operator.type, TokenType.STAR)

    def test_logical_precedence(self):
        program = parse(
            """
            fn main() -> bool {
              return true || false && !false;
            }
            """
        )

        return_stmt = program.declarations[0].body.statements[0]
        expression = return_stmt.value
        self.assertIsInstance(expression, ast.Binary)
        self.assertEqual(expression.operator.type, TokenType.OR_OR)
        self.assertIsInstance(expression.right, ast.Binary)
        self.assertEqual(expression.right.operator.type, TokenType.AND_AND)

    def test_parses_call_expression(self):
        program = parse(
            """
            fn main() -> int {
              return soma(1, 2);
            }
            """
        )

        return_stmt = program.declarations[0].body.statements[0]
        call = return_stmt.value
        self.assertIsInstance(call, ast.Call)
        self.assertEqual(call.name, "soma")
        self.assertEqual(len(call.arguments), 2)

    def test_rejects_missing_semicolon(self):
        with self.assertRaisesRegex(ParserError, "esperado ';'"):
            parse(
                """
                fn main() -> int {
                  int x
                  return x;
                }
                """
            )

    def test_rejects_void_variable(self):
        with self.assertRaisesRegex(ParserError, "esperado comando"):
            parse(
                """
                fn main() -> int {
                  void x;
                  return 0;
                }
                """
            )


if __name__ == "__main__":
    unittest.main()
