from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import ast
from .errors import CodegenError
from .tokens import Token, TokenType


NUMERIC_TYPES = {"int", "float"}


@dataclass(frozen=True)
class Local:
    name: str
    type_name: str
    offset: int
    token: Token


class CodeGenerator:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.scopes: list[dict[str, Local]] = []
        self.next_offset = 1
        self.label_count = 0
        self.return_label = ""
        self.return_offset = -1
        self.current_return_type = "void"
        self.local_count = 0
        self.routine_returns: dict[str, str] = {}
        self.routine_params: dict[str, list[str]] = {}
        self.routine_labels: dict[str, str] = {}

    def generate(self, program: ast.Program) -> str:
        self._reset()
        self.routine_returns = {
            declaration.name: declaration.return_type
            if isinstance(declaration, ast.FunctionDecl)
            else "void"
            for declaration in program.declarations
        }
        self.routine_params = {
            declaration.name: [param.type_name for param in declaration.params]
            for declaration in program.declarations
        }
        self.routine_labels = {
            declaration.name: f"rotina_{declaration.name}"
            for declaration in program.declarations
        }

        main = self._find_main(program)
        if main.params:
            raise CodegenError("geracao direta exige main sem parametros", main.token)

        self._emit("// codigo SaM gerado pelo compilador")
        self._emit("// endereco 0 guarda o valor de retorno exibido pelo STOP")
        self._emit("ADDSP 1")
        self._emit("LINK")
        self._emit(f"JSR {self.routine_labels['main']}")
        self._emit("UNLINK")
        self._emit("STOP")

        for declaration in program.declarations:
            self._routine(declaration)

        return "\n".join(self.lines) + "\n"

    def _reset(self) -> None:
        self.lines = []
        self.scopes = []
        self.next_offset = 1
        self.label_count = 0
        self.return_label = ""
        self.return_offset = -1
        self.current_return_type = "void"
        self.local_count = 0
        self.routine_returns = {}
        self.routine_params = {}
        self.routine_labels = {}

    def _find_main(self, program: ast.Program) -> ast.FunctionDecl | ast.ProcedureDecl:
        for declaration in program.declarations:
            if declaration.name == "main":
                return declaration
        raise CodegenError("programa deve possuir main", program.declarations[0].token)

    def _routine(self, declaration: ast.Declaration) -> None:
        self._emit_label(self.routine_labels[declaration.name])
        self._begin_scope()

        param_count = len(declaration.params)
        self.next_offset = 2
        self.local_count = 0
        self.return_offset = -(param_count + 1)
        self.return_label = self._label(f"fim_{declaration.name}")
        self.current_return_type = (
            declaration.return_type if isinstance(declaration, ast.FunctionDecl) else "void"
        )

        for index, param in enumerate(declaration.params):
            self._define(
                Local(
                    param.name,
                    param.type_name,
                    -param_count + index,
                    param.token,
                )
            )

        self._block(declaration.body)
        self._emit_default_return()
        self._emit_label(self.return_label)
        if self.local_count:
            self._emit(f"ADDSP -{self.local_count}")
        self._emit("JUMPIND")
        self._end_scope()

    def _block(self, block: ast.Block, create_scope: bool = True) -> None:
        if create_scope:
            self._begin_scope()
        for statement in block.statements:
            self._statement(statement)
        if create_scope:
            self._end_scope()

    def _statement(self, statement: ast.Statement) -> None:
        if isinstance(statement, ast.Block):
            self._block(statement)
        elif isinstance(statement, ast.VarDecl):
            self._var_decl(statement)
        elif isinstance(statement, ast.Assignment):
            self._assignment(statement)
        elif isinstance(statement, ast.CallStmt):
            self._call_stmt(statement)
        elif isinstance(statement, ast.IfStmt):
            self._if_stmt(statement)
        elif isinstance(statement, ast.WhileStmt):
            self._while_stmt(statement)
        elif isinstance(statement, ast.ReturnStmt):
            self._return_stmt(statement)
        else:
            raise AssertionError(f"statement desconhecido: {statement!r}")

    def _var_decl(self, statement: ast.VarDecl) -> None:
        offset = self.next_offset
        self.next_offset += 1
        self.local_count += 1
        self._define(Local(statement.name, statement.type_name, offset, statement.token))
        self._emit_default_value(statement.type_name)
        if statement.initializer is not None:
            self._expr(statement.initializer, expected_type=statement.type_name)
            self._emit(f"STOREOFF {offset}")

    def _assignment(self, statement: ast.Assignment) -> None:
        local = self._resolve(statement.name, statement.token)
        self._expr(statement.value, expected_type=local.type_name)
        self._emit(f"STOREOFF {local.offset}")

    def _call_stmt(self, statement: ast.CallStmt) -> None:
        self._call_common(
            statement.name,
            statement.arguments,
            statement.token,
            allow_void=True,
        )
        self._emit("ADDSP -1")

    def _if_stmt(self, statement: ast.IfStmt) -> None:
        else_label = self._label("if_senao")
        end_label = self._label("fim_if")

        self._expr(statement.condition, expected_type="bool")
        self._emit("NOT")
        self._emit(f"JUMPC {else_label}")
        self._block(statement.then_branch)
        self._emit(f"JUMP {end_label}")
        self._emit_label(else_label)
        if statement.else_branch is not None:
            self._block(statement.else_branch)
        self._emit_label(end_label)

    def _while_stmt(self, statement: ast.WhileStmt) -> None:
        start_label = self._label("inicio_while")
        end_label = self._label("fim_while")

        self._emit_label(start_label)
        self._expr(statement.condition, expected_type="bool")
        self._emit("NOT")
        self._emit(f"JUMPC {end_label}")
        self._block(statement.body)
        self._emit(f"JUMP {start_label}")
        self._emit_label(end_label)

    def _return_stmt(self, statement: ast.ReturnStmt) -> None:
        if statement.value is None:
            self._emit_default_value("int")
        else:
            expected_type = (
                "int" if self.current_return_type == "void" else self.current_return_type
            )
            self._expr(statement.value, expected_type=expected_type)
        self._emit(f"STOREOFF {self.return_offset}")
        self._emit(f"JUMP {self.return_label}")

    def _emit_default_return(self) -> None:
        self._emit_default_value("int")
        self._emit(f"STOREOFF {self.return_offset}")

    def _expr(self, expression: ast.Expr, expected_type: Optional[str] = None) -> str:
        actual_type = self._emit_expr(expression)
        if expected_type == "float" and actual_type == "int":
            self._emit("ITOF")
            return "float"
        return actual_type

    def _emit_expr(self, expression: ast.Expr) -> str:
        if isinstance(expression, ast.Literal):
            return self._literal(expression)
        if isinstance(expression, ast.Variable):
            local = self._resolve(expression.name, expression.token)
            self._emit(f"PUSHOFF {local.offset}")
            return local.type_name
        if isinstance(expression, ast.Call):
            return self._call(expression)
        if isinstance(expression, ast.Unary):
            return self._unary(expression)
        if isinstance(expression, ast.Binary):
            return self._binary(expression)
        raise AssertionError(f"expressao desconhecida: {expression!r}")

    def _literal(self, expression: ast.Literal) -> str:
        token_type = expression.token.type
        if token_type == TokenType.INT_LITERAL:
            self._emit(f"PUSHIMM {expression.value}")
            return "int"
        if token_type == TokenType.FLOAT_LITERAL:
            self._emit(f"PUSHIMMF {expression.value}")
            return "float"
        if token_type == TokenType.CHAR_LITERAL:
            self._emit(f"PUSHIMMCH {self._char_operand(expression.value)}")
            return "char"
        if token_type in (TokenType.KW_TRUE, TokenType.KW_FALSE):
            self._emit(f"PUSHIMM {1 if expression.value else 0}")
            return "bool"
        raise CodegenError("literal desconhecido", expression.token)

    def _unary(self, expression: ast.Unary) -> str:
        operand_type = self._expr_type(expression.operand)
        if expression.operator.type == TokenType.BANG:
            self._expr(expression.operand, expected_type="bool")
            self._emit("NOT")
            return "bool"
        if expression.operator.type == TokenType.MINUS:
            if operand_type == "float":
                self._emit("PUSHIMMF 0.0")
                self._expr(expression.operand, expected_type="float")
                self._emit("SUBF")
                return "float"
            self._emit("PUSHIMM 0")
            self._expr(expression.operand, expected_type="int")
            self._emit("SUB")
            return "int"
        raise CodegenError("operador unario invalido", expression.operator)

    def _call(self, expression: ast.Call) -> str:
        return self._call_common(
            expression.name,
            expression.arguments,
            expression.token,
            allow_void=False,
        )

    def _call_common(
        self,
        name: str,
        arguments: list[ast.Expr],
        token: Token,
        allow_void: bool,
    ) -> str:
        return_type = self.routine_returns.get(name)
        if return_type is None:
            raise CodegenError(f"rotina '{name}' nao declarada", token)
        if return_type == "void" and not allow_void:
            raise CodegenError(
                f"procedimento '{name}' nao pode ser usado como expressao",
                token,
            )

        param_types = self.routine_params[name]
        self._emit("ADDSP 1")
        for argument, expected_type in zip(arguments, param_types):
            self._expr(argument, expected_type=expected_type)
        self._emit("LINK")
        self._emit(f"JSR {self.routine_labels[name]}")
        self._emit("UNLINK")
        if arguments:
            self._emit(f"ADDSP -{len(arguments)}")
        return return_type

    def _binary(self, expression: ast.Binary) -> str:
        operator_type = expression.operator.type

        if operator_type in (TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH):
            return self._arithmetic(expression)
        if operator_type == TokenType.PERCENT:
            self._expr(expression.left, expected_type="int")
            self._expr(expression.right, expected_type="int")
            self._emit("MOD")
            return "int"
        if operator_type in (
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            return self._relational(expression)
        if operator_type in (TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            return self._equality(expression)
        if operator_type in (TokenType.AND_AND, TokenType.OR_OR):
            self._expr(expression.left, expected_type="bool")
            self._expr(expression.right, expected_type="bool")
            self._emit("AND" if operator_type == TokenType.AND_AND else "OR")
            return "bool"
        raise CodegenError("operador binario invalido", expression.operator)

    def _arithmetic(self, expression: ast.Binary) -> str:
        left_type = self._expr_type(expression.left)
        right_type = self._expr_type(expression.right)
        result_type = "float" if "float" in (left_type, right_type) else "int"

        self._expr(expression.left, expected_type=result_type)
        self._expr(expression.right, expected_type=result_type)

        integer_ops = {
            TokenType.PLUS: "ADD",
            TokenType.MINUS: "SUB",
            TokenType.STAR: "TIMES",
            TokenType.SLASH: "DIV",
        }
        float_ops = {
            TokenType.PLUS: "ADDF",
            TokenType.MINUS: "SUBF",
            TokenType.STAR: "TIMESF",
            TokenType.SLASH: "DIVF",
        }
        self._emit((float_ops if result_type == "float" else integer_ops)[expression.operator.type])
        return result_type

    def _relational(self, expression: ast.Binary) -> str:
        left_type = self._expr_type(expression.left)
        right_type = self._expr_type(expression.right)
        compare_type = "float" if "float" in (left_type, right_type) else "int"

        self._expr(expression.left, expected_type=compare_type)
        self._expr(expression.right, expected_type=compare_type)

        if compare_type == "float":
            self._emit("CMPF")
            if expression.operator.type == TokenType.GREATER:
                self._emit("PUSHIMM -1")
                self._emit("EQUAL")
            elif expression.operator.type == TokenType.LESS:
                self._emit("PUSHIMM 1")
                self._emit("EQUAL")
            elif expression.operator.type == TokenType.GREATER_EQUAL:
                self._emit("PUSHIMM 1")
                self._emit("EQUAL")
                self._emit("NOT")
            else:
                self._emit("PUSHIMM -1")
                self._emit("EQUAL")
                self._emit("NOT")
            return "bool"

        if expression.operator.type == TokenType.GREATER:
            self._emit("GREATER")
        elif expression.operator.type == TokenType.LESS:
            self._emit("LESS")
        elif expression.operator.type == TokenType.GREATER_EQUAL:
            self._emit("LESS")
            self._emit("NOT")
        else:
            self._emit("GREATER")
            self._emit("NOT")
        return "bool"

    def _equality(self, expression: ast.Binary) -> str:
        left_type = self._expr_type(expression.left)
        right_type = self._expr_type(expression.right)
        compare_type = "float" if "float" in (left_type, right_type) else left_type

        self._expr(expression.left, expected_type=compare_type)
        self._expr(expression.right, expected_type=compare_type)

        if compare_type == "float":
            self._emit("CMPF")
            self._emit("PUSHIMM 0")
            self._emit("EQUAL")
        else:
            self._emit("EQUAL")
        if expression.operator.type == TokenType.BANG_EQUAL:
            self._emit("NOT")
        return "bool"

    def _expr_type(self, expression: ast.Expr) -> str:
        if isinstance(expression, ast.Literal):
            if expression.token.type == TokenType.INT_LITERAL:
                return "int"
            if expression.token.type == TokenType.FLOAT_LITERAL:
                return "float"
            if expression.token.type == TokenType.CHAR_LITERAL:
                return "char"
            if expression.token.type in (TokenType.KW_TRUE, TokenType.KW_FALSE):
                return "bool"
        if isinstance(expression, ast.Variable):
            return self._resolve(expression.name, expression.token).type_name
        if isinstance(expression, ast.Call):
            return_type = self.routine_returns.get(expression.name)
            if return_type is None:
                raise CodegenError(f"rotina '{expression.name}' nao declarada", expression.token)
            return return_type
        if isinstance(expression, ast.Unary):
            if expression.operator.type == TokenType.BANG:
                return "bool"
            return self._expr_type(expression.operand)
        if isinstance(expression, ast.Binary):
            operator_type = expression.operator.type
            if operator_type in (
                TokenType.GREATER,
                TokenType.GREATER_EQUAL,
                TokenType.LESS,
                TokenType.LESS_EQUAL,
                TokenType.EQUAL_EQUAL,
                TokenType.BANG_EQUAL,
                TokenType.AND_AND,
                TokenType.OR_OR,
            ):
                return "bool"
            if operator_type == TokenType.PERCENT:
                return "int"
            left_type = self._expr_type(expression.left)
            right_type = self._expr_type(expression.right)
            if left_type in NUMERIC_TYPES and right_type in NUMERIC_TYPES:
                return "float" if "float" in (left_type, right_type) else "int"
        raise CodegenError("nao foi possivel inferir tipo da expressao", self._expr_token(expression))

    def _expr_token(self, expression: ast.Expr) -> Token:
        if isinstance(expression, ast.Binary):
            return expression.operator
        if isinstance(expression, ast.Unary):
            return expression.operator
        return expression.token

    def _emit_default_value(self, type_name: str) -> None:
        if type_name == "float":
            self._emit("PUSHIMMF 0.0")
        elif type_name == "char":
            self._emit("PUSHIMMCH '\\0'")
        else:
            self._emit("PUSHIMM 0")

    def _char_operand(self, value: str) -> str:
        escapes = {
            "\n": "\\n",
            "\t": "\\t",
            "\r": "\\r",
            "\0": "\\0",
            "'": "\\'",
            "\\": "\\\\",
        }
        return f"'{escapes.get(value, value)}'"

    def _begin_scope(self) -> None:
        self.scopes.append({})

    def _end_scope(self) -> None:
        self.scopes.pop()

    def _define(self, local: Local) -> None:
        self.scopes[-1][local.name] = local

    def _resolve(self, name: str, token: Token) -> Local:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise CodegenError(f"variavel '{name}' nao encontrada na geracao", token)

    def _label(self, prefix: str) -> str:
        self.label_count += 1
        return f"{prefix}_{self.label_count}"

    def _emit_label(self, label: str) -> None:
        self.lines.append(f"{label}:")

    def _emit(self, instruction: str) -> None:
        self.lines.append(instruction)
