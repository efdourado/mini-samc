# Requisitos

Requisitos transcritos e consolidados a partir do enunciado original do projeto.

## Objetivo

Construir um tradutor de uma linguagem de alto nivel para assembly SaM.

## Obrigatorios

| Requisito | Status |
| --- | --- |
| Paradigma procedural | Implementado |
| Variaveis | Implementado |
| Tipos `int`, `float` e `char` | Implementado |
| Constantes numericas | Implementado |
| Atribuicao | Implementado |
| Operadores aritmeticos `+`, `-`, `*`, `/`, `%` | Implementado |
| Operadores relacionais `==`, `!=`, `>`, `<`, `>=`, `<=` | Implementado |
| Operadores logicos `&&`, `||`, `!` | Implementado |
| Decisao `if/else` | Implementado |
| Repeticao `while` | Implementado |
| Lexer e parser sem geradores | Implementado |

## Opcionais implementados

| Opcional | Status |
| --- | --- |
| Tipo booleano | Implementado |
| Funcoes com parametros e retorno | Implementado |
| Procedimentos com parametros | Implementado |

## Opcionais nao implementados

- Vetores.
- Strings.
- Constantes de strings.
- Operadores bit-a-bit.

## Itens avaliados

| Item | Evidencia no projeto |
| --- | --- |
| Projeto da gramatica | `docs/gramatica.md` |
| Analise lexica | `src/compilador/lexer.py`, `tests/test_lexer.py` |
| Analise sintatica | `src/compilador/parser.py`, `src/compilador/ast.py`, `tests/test_parser.py` |
| Analise semantica | `src/compilador/semantic.py`, `src/compilador/symbols.py`, `tests/test_semantic.py` |
| Geracao de codigo | `src/compilador/codegen.py`, `docs/geracao-sam.md`, `tests/test_codegen.py` |
| Testes e documentacao | `tests/`, `docs/`, `README.md` |
