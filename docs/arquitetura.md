# Arquitetura

## Pipeline

```text
fonte
  -> lexer
  -> tokens
  -> parser
  -> AST
  -> analise semantica
  -> geracao SaM
```

## Modulos

| Modulo | Papel |
| --- | --- |
| `lexer.py` | Gera tokens com linha e coluna |
| `tokens.py` | Define tokens e palavras reservadas |
| `parser.py` | Parser descendente recursivo |
| `ast.py` | Nos da arvore sintatica |
| `symbols.py` | Escopos e simbolos |
| `semantic.py` | Declaracoes, usos e tipos |
| `codegen.py` | Emite assembly SaM |
| `cli.py` | Interface de linha de comando |

## Decisoes

- Parser descendente recursivo para manter a gramatica simples e explicavel.
- Lexer e parser manuais, conforme restricao do enunciado.
- Tokens guardam linha e coluna para mensagens de erro.
- Analise semantica separada da geracao de codigo.
- Testes acompanham cada etapa do pipeline.

## Erros

Formato padrao:

```text
erro semantico em linha 4, coluna 7: variavel 'x' nao declarada
```
