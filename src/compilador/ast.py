from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .tokens import Token


@dataclass(frozen=True)
class Program:
    declarations: list[Declaration]


@dataclass(frozen=True)
class Parameter:
    type_name: str
    name: str
    token: Token


@dataclass(frozen=True)
class FunctionDecl:
    name: str
    params: list[Parameter]
    return_type: str
    body: Block
    token: Token


@dataclass(frozen=True)
class ProcedureDecl:
    name: str
    params: list[Parameter]
    body: Block
    token: Token


Declaration = FunctionDecl | ProcedureDecl


@dataclass(frozen=True)
class Block:
    statements: list[Statement]
    token: Token


@dataclass(frozen=True)
class VarDecl:
    type_name: str
    name: str
    initializer: Optional[Expr]
    token: Token


@dataclass(frozen=True)
class Assignment:
    name: str
    value: Expr
    token: Token


@dataclass(frozen=True)
class CallStmt:
    name: str
    arguments: list[Expr]
    token: Token


@dataclass(frozen=True)
class IfStmt:
    condition: Expr
    then_branch: Block
    else_branch: Optional[Block]
    token: Token


@dataclass(frozen=True)
class WhileStmt:
    condition: Expr
    body: Block
    token: Token


@dataclass(frozen=True)
class ReturnStmt:
    value: Optional[Expr]
    token: Token


Statement = Block | VarDecl | Assignment | CallStmt | IfStmt | WhileStmt | ReturnStmt


@dataclass(frozen=True)
class Binary:
    left: Expr
    operator: Token
    right: Expr


@dataclass(frozen=True)
class Unary:
    operator: Token
    operand: Expr


@dataclass(frozen=True)
class Literal:
    value: Any
    token: Token


@dataclass(frozen=True)
class Variable:
    name: str
    token: Token


@dataclass(frozen=True)
class Call:
    name: str
    arguments: list[Expr]
    token: Token


Expr = Binary | Unary | Literal | Variable | Call
