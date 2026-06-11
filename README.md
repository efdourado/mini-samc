# Compilador SaM

Tradutor de uma linguagem procedural simples para assembly SaM, desenvolvido
para a disciplina de Compiladores.

## Escopo

- Linguagem procedural com funcoes e procedimentos.
- Tipos `int`, `float`, `char` e `bool`.
- Variaveis locais, atribuicao e constantes numericas.
- Operadores aritmeticos, relacionais e logicos.
- `if/else`, `while` e `return`.
- Lexer e parser manuais, sem geradores.
- Analise semantica com escopos, tabela de simbolos e checagem de tipos.
- Geracao de assembly SaM.

Fora do escopo atual: vetores, strings, constantes de strings e operadores
bit-a-bit.

## Uso

Executar o lexer:

```bash
PYTHONPATH=src python3 -m compilador examples/programa_minimo.lang --tokens
```

Imprimir a AST:

```bash
PYTHONPATH=src python3 -m compilador examples/programa_minimo.lang --ast
```

Gerar assembly no terminal:

```bash
PYTHONPATH=src python3 -m compilador examples/programa_minimo.lang
```

Gerar arquivo `.sam`:

```bash
PYTHONPATH=src python3 -m compilador examples/programa_minimo.lang -o build/programa_minimo.sam
```

Rodar testes:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Estrutura

- `src/compilador/`: implementacao do compilador.
- `tests/`: testes de lexer, parser, semantica e codegen.
- `examples/`: programas de exemplo da linguagem.
- `docs/requisitos.md`: requisitos transcritos e checklist.
- `docs/gramatica.md`: gramatica da linguagem.
- `docs/arquitetura.md`: pipeline e modulos.
- `docs/geracao-sam.md`: convencoes de geracao SaM.
- `docs/plano-10.md`: plano final de entrega.
