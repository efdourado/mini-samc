from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .tokens import Token


@dataclass(frozen=True)
class VariableSymbol:
    name: str
    type_name: str
    token: Token


@dataclass(frozen=True)
class RoutineSymbol:
    name: str
    param_types: list[str]
    return_type: str
    token: Token
    is_procedure: bool


class Scope:
    def __init__(self, parent: Optional[Scope] = None) -> None:
        self.parent = parent
        self.variables: dict[str, VariableSymbol] = {}

    def define(self, symbol: VariableSymbol) -> bool:
        if symbol.name in self.variables:
            return False
        self.variables[symbol.name] = symbol
        return True

    def resolve(self, name: str) -> Optional[VariableSymbol]:
        if name in self.variables:
            return self.variables[name]
        if self.parent is not None:
            return self.parent.resolve(name)
        return None
