from __future__ import annotations

from . import ast
from .errors import ParserError
from .tokens import Token, TokenType


TYPE_TOKENS = {
    TokenType.KW_INT,
    TokenType.KW_FLOAT,
    TokenType.KW_CHAR,
    TokenType.KW_BOOL,
    TokenType.KW_VOID,
}

VALUE_TYPE_TOKENS = TYPE_TOKENS - {TokenType.KW_VOID}


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0

    def parse(self) -> ast.Program:
        declarations: list[ast.Declaration] = []
        while not self._is_at_end():
            declarations.append(self._declaration())
        return ast.Program(declarations)

    def _declaration(self) -> ast.Declaration:
        if self._match(TokenType.KW_FN):
            return self._function_decl(self._previous())
        if self._match(TokenType.KW_PROC):
            return self._procedure_decl(self._previous())
        raise self._error(self._peek(), "esperado declaracao de funcao ou procedimento")

    def _function_decl(self, token: Token) -> ast.FunctionDecl:
        name = self._consume(TokenType.IDENTIFIER, "esperado nome da funcao")
        self._consume(TokenType.LEFT_PAREN, "esperado '(' apos nome da funcao")
        params = self._parameters()
        self._consume(TokenType.RIGHT_PAREN, "esperado ')' apos parametros")
        self._consume(TokenType.ARROW, "esperado '->' antes do tipo de retorno")
        return_type = self._type(allow_void=True)
        body = self._block()
        return ast.FunctionDecl(name.lexeme, params, return_type, body, token)

    def _procedure_decl(self, token: Token) -> ast.ProcedureDecl:
        name = self._consume(TokenType.IDENTIFIER, "esperado nome do procedimento")
        self._consume(TokenType.LEFT_PAREN, "esperado '(' apos nome do procedimento")
        params = self._parameters()
        self._consume(TokenType.RIGHT_PAREN, "esperado ')' apos parametros")
        body = self._block()
        return ast.ProcedureDecl(name.lexeme, params, body, token)

    def _parameters(self) -> list[ast.Parameter]:
        if self._check(TokenType.RIGHT_PAREN):
            return []

        params = [self._parameter()]
        while self._match(TokenType.COMMA):
            params.append(self._parameter())
        return params

    def _parameter(self) -> ast.Parameter:
        type_name = self._type(allow_void=False)
        name = self._consume(TokenType.IDENTIFIER, "esperado nome do parametro")
        return ast.Parameter(type_name, name.lexeme, name)

    def _block(self) -> ast.Block:
        token = self._consume(TokenType.LEFT_BRACE, "esperado '{' para iniciar bloco")
        statements: list[ast.Statement] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            statements.append(self._statement())
        self._consume(TokenType.RIGHT_BRACE, "esperado '}' para fechar bloco")
        return ast.Block(statements, token)

    def _statement(self) -> ast.Statement:
        if self._check_any(VALUE_TYPE_TOKENS):
            return self._var_decl()
        if self._match(TokenType.KW_IF):
            return self._if_stmt(self._previous())
        if self._match(TokenType.KW_WHILE):
            return self._while_stmt(self._previous())
        if self._match(TokenType.KW_RETURN):
            return self._return_stmt(self._previous())
        if self._check(TokenType.LEFT_BRACE):
            return self._block()
        if self._check(TokenType.IDENTIFIER):
            return self._identifier_stmt()
        raise self._error(self._peek(), "esperado comando")

    def _var_decl(self) -> ast.VarDecl:
        type_token = self._advance()
        name = self._consume(TokenType.IDENTIFIER, "esperado nome da variavel")
        initializer = None
        if self._match(TokenType.ASSIGN):
            initializer = self._expression()
        self._consume(TokenType.SEMICOLON, "esperado ';' apos declaracao de variavel")
        return ast.VarDecl(type_token.lexeme, name.lexeme, initializer, type_token)

    def _identifier_stmt(self) -> ast.Assignment | ast.CallStmt:
        name = self._consume(TokenType.IDENTIFIER, "esperado nome da variavel")
        if self._match(TokenType.ASSIGN):
            value = self._expression()
            self._consume(TokenType.SEMICOLON, "esperado ';' apos atribuicao")
            return ast.Assignment(name.lexeme, value, name)
        if self._match(TokenType.LEFT_PAREN):
            call = self._finish_call(name)
            self._consume(TokenType.SEMICOLON, "esperado ';' apos chamada")
            return ast.CallStmt(call.name, call.arguments, call.token)
        raise self._error(self._peek(), "esperado '=' ou '(' apos identificador")

    def _if_stmt(self, token: Token) -> ast.IfStmt:
        self._consume(TokenType.LEFT_PAREN, "esperado '(' apos 'if'")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "esperado ')' apos condicao")
        then_branch = self._block()
        else_branch = None
        if self._match(TokenType.KW_ELSE):
            else_branch = self._block()
        return ast.IfStmt(condition, then_branch, else_branch, token)

    def _while_stmt(self, token: Token) -> ast.WhileStmt:
        self._consume(TokenType.LEFT_PAREN, "esperado '(' apos 'while'")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "esperado ')' apos condicao")
        body = self._block()
        return ast.WhileStmt(condition, body, token)

    def _return_stmt(self, token: Token) -> ast.ReturnStmt:
        if self._check(TokenType.SEMICOLON):
            value = None
        else:
            value = self._expression()
        self._consume(TokenType.SEMICOLON, "esperado ';' apos retorno")
        return ast.ReturnStmt(value, token)

    def _expression(self) -> ast.Expr:
        return self._logic_or()

    def _logic_or(self) -> ast.Expr:
        return self._left_associative(self._logic_and, TokenType.OR_OR)

    def _logic_and(self) -> ast.Expr:
        return self._left_associative(self._equality, TokenType.AND_AND)

    def _equality(self) -> ast.Expr:
        return self._left_associative(
            self._comparison,
            TokenType.EQUAL_EQUAL,
            TokenType.BANG_EQUAL,
        )

    def _comparison(self) -> ast.Expr:
        return self._left_associative(
            self._term,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        )

    def _term(self) -> ast.Expr:
        return self._left_associative(self._factor, TokenType.PLUS, TokenType.MINUS)

    def _factor(self) -> ast.Expr:
        return self._left_associative(
            self._unary,
            TokenType.STAR,
            TokenType.SLASH,
            TokenType.PERCENT,
        )

    def _unary(self) -> ast.Expr:
        if self._match(TokenType.BANG, TokenType.MINUS):
            operator = self._previous()
            return ast.Unary(operator, self._unary())
        return self._primary()

    def _primary(self) -> ast.Expr:
        if self._match(TokenType.INT_LITERAL, TokenType.FLOAT_LITERAL, TokenType.CHAR_LITERAL):
            token = self._previous()
            return ast.Literal(token.literal, token)
        if self._match(TokenType.KW_TRUE, TokenType.KW_FALSE):
            token = self._previous()
            return ast.Literal(token.literal, token)
        if self._match(TokenType.IDENTIFIER):
            token = self._previous()
            if self._match(TokenType.LEFT_PAREN):
                return self._finish_call(token)
            return ast.Variable(token.lexeme, token)
        if self._match(TokenType.LEFT_PAREN):
            expression = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "esperado ')' apos expressao")
            return expression
        raise self._error(self._peek(), "esperado expressao")

    def _finish_call(self, name: Token) -> ast.Call:
        arguments: list[ast.Expr] = []
        if not self._check(TokenType.RIGHT_PAREN):
            arguments.append(self._expression())
            while self._match(TokenType.COMMA):
                arguments.append(self._expression())
        self._consume(TokenType.RIGHT_PAREN, "esperado ')' apos argumentos")
        return ast.Call(name.lexeme, arguments, name)

    def _left_associative(self, operand_parser, *operators: TokenType) -> ast.Expr:
        expr = operand_parser()
        while self._match(*operators):
            operator = self._previous()
            right = operand_parser()
            expr = ast.Binary(expr, operator, right)
        return expr

    def _type(self, allow_void: bool) -> str:
        allowed = TYPE_TOKENS if allow_void else VALUE_TYPE_TOKENS
        if self._check_any(allowed):
            return self._advance().lexeme
        if allow_void:
            raise self._error(self._peek(), "esperado tipo")
        raise self._error(self._peek(), "esperado tipo nao-void")

    def _match(self, *types: TokenType) -> bool:
        for token_type in types:
            if self._check(token_type):
                self._advance()
                return True
        return False

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise self._error(self._peek(), message)

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return token_type == TokenType.EOF
        return self._peek().type == token_type

    def _check_any(self, token_types: set[TokenType]) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type in token_types

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _error(self, token: Token, message: str) -> ParserError:
        return ParserError(message, token)
