from __future__ import annotations

from . import ast
from .errors import SemanticError
from .symbols import RoutineSymbol, Scope, VariableSymbol
from .tokens import Token, TokenType


NUMERIC_TYPES = {"int", "float"}


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.routines: dict[str, RoutineSymbol] = {}
        self.current_return_type = "void"
        self.in_procedure = False

    def analyze(self, program: ast.Program) -> ast.Program:
        self._declare_routines(program.declarations)
        self._require_main()
        for declaration in program.declarations:
            self._declaration(declaration)
        return program

    def _declare_routines(self, declarations: list[ast.Declaration]) -> None:
        for declaration in declarations:
            if declaration.name in self.routines:
                raise SemanticError(f"rotina '{declaration.name}' ja declarada", declaration.token)

            if isinstance(declaration, ast.FunctionDecl):
                param_types = [param.type_name for param in declaration.params]
                symbol = RoutineSymbol(
                    declaration.name,
                    param_types,
                    declaration.return_type,
                    declaration.token,
                    is_procedure=False,
                )
            else:
                param_types = [param.type_name for param in declaration.params]
                symbol = RoutineSymbol(
                    declaration.name,
                    param_types,
                    "void",
                    declaration.token,
                    is_procedure=True,
                )
            self.routines[declaration.name] = symbol

    def _require_main(self) -> None:
        main = self.routines.get("main")
        if main is None:
            token = next(iter(self.routines.values())).token
            raise SemanticError("programa deve declarar uma funcao ou procedimento 'main'", token)

    def _declaration(self, declaration: ast.Declaration) -> None:
        scope = Scope()
        for param in declaration.params:
            self._define_variable(scope, param.name, param.type_name, param.token)

        previous_return_type = self.current_return_type
        previous_in_procedure = self.in_procedure

        if isinstance(declaration, ast.FunctionDecl):
            self.current_return_type = declaration.return_type
            self.in_procedure = False
        else:
            self.current_return_type = "void"
            self.in_procedure = True

        self._block(declaration.body, scope)

        self.current_return_type = previous_return_type
        self.in_procedure = previous_in_procedure

    def _block(self, block: ast.Block, parent_scope: Scope) -> None:
        scope = Scope(parent_scope)
        for statement in block.statements:
            self._statement(statement, scope)

    def _statement(self, statement: ast.Statement, scope: Scope) -> None:
        if isinstance(statement, ast.Block):
            self._block(statement, scope)
        elif isinstance(statement, ast.VarDecl):
            self._var_decl(statement, scope)
        elif isinstance(statement, ast.Assignment):
            self._assignment(statement, scope)
        elif isinstance(statement, ast.CallStmt):
            self._call_stmt(statement, scope)
        elif isinstance(statement, ast.IfStmt):
            self._if_stmt(statement, scope)
        elif isinstance(statement, ast.WhileStmt):
            self._while_stmt(statement, scope)
        elif isinstance(statement, ast.ReturnStmt):
            self._return_stmt(statement, scope)
        else:
            raise AssertionError(f"statement desconhecido: {statement!r}")

    def _var_decl(self, statement: ast.VarDecl, scope: Scope) -> None:
        if statement.initializer is not None:
            initializer_type = self._expr(statement.initializer, scope)
            self._require_assignable(
                statement.type_name,
                initializer_type,
                statement.token,
                "tipo incompativel na inicializacao",
            )
        self._define_variable(scope, statement.name, statement.type_name, statement.token)

    def _assignment(self, statement: ast.Assignment, scope: Scope) -> None:
        symbol = self._resolve_variable(scope, statement.name, statement.token)
        value_type = self._expr(statement.value, scope)
        self._require_assignable(
            symbol.type_name,
            value_type,
            statement.token,
            f"tipo incompativel na atribuicao de '{statement.name}'",
        )

    def _call_stmt(self, statement: ast.CallStmt, scope: Scope) -> None:
        self._validate_call(
            statement.name,
            statement.arguments,
            statement.token,
            scope,
            allow_procedure=True,
        )

    def _if_stmt(self, statement: ast.IfStmt, scope: Scope) -> None:
        condition_type = self._expr(statement.condition, scope)
        self._require_type(condition_type, "bool", statement.token, "condicao do if deve ser bool")
        self._block(statement.then_branch, scope)
        if statement.else_branch is not None:
            self._block(statement.else_branch, scope)

    def _while_stmt(self, statement: ast.WhileStmt, scope: Scope) -> None:
        condition_type = self._expr(statement.condition, scope)
        self._require_type(
            condition_type,
            "bool",
            statement.token,
            "condicao do while deve ser bool",
        )
        self._block(statement.body, scope)

    def _return_stmt(self, statement: ast.ReturnStmt, scope: Scope) -> None:
        if self.in_procedure:
            if statement.value is not None:
                raise SemanticError("procedimento nao deve retornar valor", statement.token)
            return

        if self.current_return_type == "void":
            if statement.value is not None:
                raise SemanticError("funcao void nao deve retornar valor", statement.token)
            return

        if statement.value is None:
            raise SemanticError("funcao deve retornar valor", statement.token)

        value_type = self._expr(statement.value, scope)
        self._require_assignable(
            self.current_return_type,
            value_type,
            statement.token,
            "tipo de retorno incompativel",
        )

    def _expr(self, expression: ast.Expr, scope: Scope) -> str:
        if isinstance(expression, ast.Literal):
            return self._literal_type(expression)
        if isinstance(expression, ast.Variable):
            return self._resolve_variable(scope, expression.name, expression.token).type_name
        if isinstance(expression, ast.Call):
            return self._call(expression, scope)
        if isinstance(expression, ast.Unary):
            return self._unary(expression, scope)
        if isinstance(expression, ast.Binary):
            return self._binary(expression, scope)
        raise AssertionError(f"expressao desconhecida: {expression!r}")

    def _literal_type(self, expression: ast.Literal) -> str:
        token_type = expression.token.type
        if token_type == TokenType.INT_LITERAL:
            return "int"
        if token_type == TokenType.FLOAT_LITERAL:
            return "float"
        if token_type == TokenType.CHAR_LITERAL:
            return "char"
        if token_type in (TokenType.KW_TRUE, TokenType.KW_FALSE):
            return "bool"
        raise SemanticError("literal desconhecido", expression.token)

    def _call(self, expression: ast.Call, scope: Scope) -> str:
        return self._validate_call(
            expression.name,
            expression.arguments,
            expression.token,
            scope,
            allow_procedure=False,
        )

    def _validate_call(
        self,
        name: str,
        arguments: list[ast.Expr],
        token: Token,
        scope: Scope,
        allow_procedure: bool,
    ) -> str:
        routine = self.routines.get(name)
        if routine is None:
            raise SemanticError(f"rotina '{name}' nao declarada", token)
        if routine.is_procedure and not allow_procedure:
            raise SemanticError(
                f"procedimento '{name}' nao pode ser usado como expressao",
                token,
            )
        if len(arguments) != len(routine.param_types):
            raise SemanticError(
                f"rotina '{name}' esperava {len(routine.param_types)} argumento(s), "
                f"mas recebeu {len(arguments)}",
                token,
            )

        for index, (argument, expected_type) in enumerate(
            zip(arguments, routine.param_types),
            start=1,
        ):
            actual_type = self._expr(argument, scope)
            self._require_assignable(
                expected_type,
                actual_type,
                token,
                f"tipo incompativel no argumento {index} de '{name}'",
            )
        return routine.return_type

    def _unary(self, expression: ast.Unary, scope: Scope) -> str:
        operand_type = self._expr(expression.operand, scope)
        if expression.operator.type == TokenType.MINUS:
            self._require_numeric(operand_type, expression.operator, "operador '-' exige numero")
            return operand_type
        if expression.operator.type == TokenType.BANG:
            self._require_type(operand_type, "bool", expression.operator, "operador '!' exige bool")
            return "bool"
        raise SemanticError("operador unario invalido", expression.operator)

    def _binary(self, expression: ast.Binary, scope: Scope) -> str:
        left_type = self._expr(expression.left, scope)
        right_type = self._expr(expression.right, scope)
        operator_type = expression.operator.type

        if operator_type in (TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH):
            self._require_numeric(left_type, expression.operator, "operador aritmetico exige numero")
            self._require_numeric(right_type, expression.operator, "operador aritmetico exige numero")
            if left_type == "float" or right_type == "float":
                return "float"
            return "int"

        if operator_type == TokenType.PERCENT:
            self._require_type(left_type, "int", expression.operator, "operador '%' exige int")
            self._require_type(right_type, "int", expression.operator, "operador '%' exige int")
            return "int"

        if operator_type in (
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            self._require_numeric(left_type, expression.operator, "operador relacional exige numero")
            self._require_numeric(right_type, expression.operator, "operador relacional exige numero")
            return "bool"

        if operator_type in (TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            if not self._compatible_equality(left_type, right_type):
                raise SemanticError("operador de igualdade exige tipos compativeis", expression.operator)
            return "bool"

        if operator_type in (TokenType.AND_AND, TokenType.OR_OR):
            self._require_type(left_type, "bool", expression.operator, "operador logico exige bool")
            self._require_type(right_type, "bool", expression.operator, "operador logico exige bool")
            return "bool"

        raise SemanticError("operador binario invalido", expression.operator)

    def _define_variable(self, scope: Scope, name: str, type_name: str, token: Token) -> None:
        if type_name == "void":
            raise SemanticError("variavel nao pode ter tipo void", token)
        if not scope.define(VariableSymbol(name, type_name, token)):
            raise SemanticError(f"variavel '{name}' ja declarada neste escopo", token)

    def _resolve_variable(self, scope: Scope, name: str, token: Token) -> VariableSymbol:
        symbol = scope.resolve(name)
        if symbol is None:
            raise SemanticError(f"variavel '{name}' nao declarada", token)
        return symbol

    def _require_numeric(self, actual_type: str, token: Token, message: str) -> None:
        if actual_type not in NUMERIC_TYPES:
            raise SemanticError(f"{message}; recebido {actual_type}", token)

    def _require_type(
        self,
        actual_type: str,
        expected_type: str,
        token: Token,
        message: str,
    ) -> None:
        if actual_type != expected_type:
            raise SemanticError(f"{message}; recebido {actual_type}", token)

    def _require_assignable(
        self,
        expected_type: str,
        actual_type: str,
        token: Token,
        message: str,
    ) -> None:
        if not self._assignable(expected_type, actual_type):
            raise SemanticError(
                f"{message}; esperado {expected_type}, recebido {actual_type}",
                token,
            )

    def _assignable(self, expected_type: str, actual_type: str) -> bool:
        return expected_type == actual_type or (
            expected_type == "float" and actual_type == "int"
        )

    def _compatible_equality(self, left_type: str, right_type: str) -> bool:
        return self._assignable(left_type, right_type) or self._assignable(
            right_type,
            left_type,
        )
