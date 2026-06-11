import math
import unittest
from pathlib import Path

from compilador.codegen import CodeGenerator
from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.semantic import SemanticAnalyzer


def compile_source(source):
    program = Parser(Lexer(source).scan_tokens()).parse()
    SemanticAnalyzer().analyze(program)
    return CodeGenerator().generate(program)


def run_sam_subset(code):
    labels = {}
    instructions = []
    for raw_line in code.splitlines():
        line = raw_line.split("//", 1)[0].strip()
        if not line:
            continue
        if ":" in line:
            label, rest = line.split(":", 1)
            labels[label.strip()] = len(instructions)
            line = rest.strip()
            if not line:
                continue
        instructions.append(line)

    stack = []
    fbr = 0
    pc = 0

    def push(value):
        stack.append(value)

    def pop():
        return stack.pop()

    while pc < len(instructions):
        instruction = instructions[pc]
        parts = instruction.split(maxsplit=1)
        opcode = parts[0]
        operand = parts[1] if len(parts) == 2 else None
        pc += 1

        if opcode == "PUSHIMM":
            push(int(operand))
        elif opcode == "PUSHIMMF":
            push(float(operand))
        elif opcode == "PUSHIMMCH":
            push(parse_char_operand(operand))
        elif opcode == "ITOF":
            push(float(pop()))
        elif opcode == "ADDSP":
            amount = int(operand)
            if amount >= 0:
                stack.extend([0] * amount)
            else:
                del stack[amount:]
        elif opcode == "LINK":
            push(fbr)
            fbr = len(stack) - 1
        elif opcode == "UNLINK":
            fbr = pop()
        elif opcode == "PUSHOFF":
            push(stack[fbr + int(operand)])
        elif opcode == "STOREOFF":
            stack[fbr + int(operand)] = pop()
        elif opcode == "ADD":
            right, left = pop(), pop()
            push(left + right)
        elif opcode == "SUB":
            right, left = pop(), pop()
            push(left - right)
        elif opcode == "TIMES":
            right, left = pop(), pop()
            push(left * right)
        elif opcode == "DIV":
            right, left = pop(), pop()
            push(math.trunc(left / right))
        elif opcode == "MOD":
            right, left = pop(), pop()
            push(left % right)
        elif opcode == "ADDF":
            right, left = pop(), pop()
            push(left + right)
        elif opcode == "SUBF":
            right, left = pop(), pop()
            push(left - right)
        elif opcode == "TIMESF":
            right, left = pop(), pop()
            push(left * right)
        elif opcode == "DIVF":
            right, left = pop(), pop()
            push(left / right)
        elif opcode == "GREATER":
            right, left = pop(), pop()
            push(1 if left > right else 0)
        elif opcode == "LESS":
            right, left = pop(), pop()
            push(1 if left < right else 0)
        elif opcode == "EQUAL":
            right, left = pop(), pop()
            push(1 if left == right else 0)
        elif opcode == "CMPF":
            right, left = pop(), pop()
            if right > left:
                push(1)
            elif right < left:
                push(-1)
            else:
                push(0)
        elif opcode == "NOT":
            push(0 if pop() else 1)
        elif opcode == "AND":
            right, left = pop(), pop()
            push(1 if left and right else 0)
        elif opcode == "OR":
            right, left = pop(), pop()
            push(1 if left or right else 0)
        elif opcode == "JUMP":
            pc = labels[operand]
        elif opcode == "JUMPC":
            condition = pop()
            if condition:
                pc = labels[operand]
        elif opcode == "JSR":
            push(pc)
            pc = labels[operand]
        elif opcode == "JUMPIND":
            pc = pop()
        elif opcode == "STOP":
            return stack[0]
        else:
            raise AssertionError(f"instrucao nao suportada no teste: {instruction}")

    raise AssertionError("programa SaM terminou sem STOP")


def parse_char_operand(operand):
    inner = operand[1:-1]
    escapes = {
        "\\n": "\n",
        "\\t": "\t",
        "\\r": "\r",
        "\\0": "\0",
        "\\'": "'",
        "\\\\": "\\",
    }
    return escapes.get(inner, inner)


class CodeGeneratorTest(unittest.TestCase):
    def test_compiles_minimal_program(self):
        source = Path("examples/programa_minimo.lang").read_text(encoding="utf-8")
        code = compile_source(source)

        self.assertIn("LINK", code)
        self.assertIn("JSR rotina_main", code)
        self.assertIn("STOREOFF 2", code)
        self.assertIn("GREATER", code)
        self.assertIn("LESS", code)
        self.assertIn("STOP", code)
        self.assertEqual(run_sam_subset(code), 21)

    def test_compiles_integer_arithmetic(self):
        code = compile_source(
            """
            fn main() -> int {
              return 1 + 2 * 3 - 4 / 2 + 10 % 4;
            }
            """
        )

        self.assertIn("TIMES", code)
        self.assertIn("DIV", code)
        self.assertIn("MOD", code)
        self.assertEqual(run_sam_subset(code), 7)

    def test_compiles_logic_and_char_equality(self):
        code = compile_source(
            """
            fn main() -> int {
              bool b = true && !false;
              char c = 'a';

              if (b || c != 'b') {
                return 7;
              }

              return 0;
            }
            """
        )

        self.assertIn("PUSHIMMCH 'a'", code)
        self.assertIn("AND", code)
        self.assertIn("OR", code)
        self.assertEqual(run_sam_subset(code), 7)

    def test_compiles_float_arithmetic_and_comparison(self):
        code = compile_source(
            """
            fn main() -> float {
              float x = 1;
              x = x + 2.5;

              if (x >= 3.5) {
                return x;
              }

              return 0.0;
            }
            """
        )

        self.assertIn("ITOF", code)
        self.assertIn("ADDF", code)
        self.assertIn("CMPF", code)
        self.assertAlmostEqual(run_sam_subset(code), 3.5)

    def test_compiles_function_call(self):
        code = compile_source(
            """
            fn soma(int a, int b) -> int {
              return a + b;
            }

            fn main() -> int {
              return soma(1, 2) * 3;
            }
            """
        )

        self.assertIn("rotina_soma:", code)
        self.assertIn("JSR rotina_soma", code)
        self.assertEqual(run_sam_subset(code), 9)

    def test_compiles_procedure_call_statement(self):
        code = compile_source(
            """
            proc mostra(int valor) {
              valor = valor + 1;
              return;
            }

            fn main() -> int {
              mostra(1);
              return 5;
            }
            """
        )

        self.assertIn("rotina_mostra:", code)
        self.assertIn("JSR rotina_mostra", code)
        self.assertEqual(run_sam_subset(code), 5)


if __name__ == "__main__":
    unittest.main()
