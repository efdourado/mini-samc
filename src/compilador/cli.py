from __future__ import annotations

import argparse
from pathlib import Path
from pprint import pprint
from typing import Sequence

from .codegen import CodeGenerator
from .lexer import Lexer
from .parser import Parser
from .semantic import SemanticAnalyzer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="compilador",
        description="Tradutor da linguagem do projeto para assembly SaM.",
    )
    parser.add_argument("source", help="arquivo fonte da linguagem")
    parser.add_argument(
        "--tokens",
        action="store_true",
        help="imprime os tokens gerados pelo lexer",
    )
    parser.add_argument(
        "--ast",
        action="store_true",
        help="imprime a AST gerada pelo parser",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="arquivo de saida para o assembly SaM gerado",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    source_path = Path(args.source)
    source = source_path.read_text(encoding="utf-8")
    tokens = Lexer(source).scan_tokens()

    if args.tokens:
        for token in tokens:
            print(token)
        return 0

    program = Parser(tokens).parse()
    if args.ast:
        pprint(program)
        return 0

    SemanticAnalyzer().analyze(program)
    sam_code = CodeGenerator().generate(program)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(sam_code, encoding="utf-8")
        print(f"Assembly SaM gerado em {output_path}")
        return 0

    print(sam_code, end="")
    return 0
