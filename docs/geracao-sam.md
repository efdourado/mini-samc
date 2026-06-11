# Geracao SaM

O gerador em `src/compilador/codegen.py` emite assembly SaM para o nucleo da
linguagem.

## Suporte

- `main` sem parametros.
- Funcoes com parametros e retorno.
- Procedimentos com parametros.
- Variaveis locais de `int`, `float`, `char` e `bool`.
- Declaracao, atribuicao, expressoes, `if/else`, `while` e `return`.

## Convencao

- O programa reserva um slot de retorno e chama `main` com `LINK` e `JSR`.
- O valor final fica no endereco `0`, lido pelo `STOP`.
- O slot de retorno de uma rotina fica em `FBR - (parametros + 1)`.
- Parametros usam deslocamentos negativos.
- Variaveis locais usam deslocamentos a partir de `2`.
- Rotinas retornam com limpeza de locais e `JUMPIND`.

## Mapeamento

| Linguagem | SaM |
| --- | --- |
| `int` | `PUSHIMM` |
| `float` | `PUSHIMMF` |
| `char` | `PUSHIMMCH` |
| `bool` | `PUSHIMM 1` ou `PUSHIMM 0` |
| Variavel | `PUSHOFF n` |
| Atribuicao | expressao + `STOREOFF n` |
| `+`, `-`, `*`, `/`, `%` inteiros | `ADD`, `SUB`, `TIMES`, `DIV`, `MOD` |
| `+`, `-`, `*`, `/` reais | `ADDF`, `SUBF`, `TIMESF`, `DIVF` |
| Conversao `int` para `float` | `ITOF` |
| Comparacoes inteiras | `GREATER`, `LESS`, `EQUAL`, `NOT` |
| Comparacoes reais | `CMPF` + comparacao auxiliar |
| `&&`, <code>&#124;&#124;</code>, `!` | `AND`, `OR`, `NOT` |
| Controle de fluxo | `JUMP`, `JUMPC`, labels |
| Chamada de rotina | `ADDSP`, argumentos, `LINK`, `JSR`, `UNLINK` |

Os operadores logicos `&&` e <code>&#124;&#124;</code> sao emitidos como `AND` e
`OR`; portanto, ambos os operandos sao avaliados antes da instrucao logica.

## Referencias

- SaM ISA Manual: https://www.cs.cornell.edu/courses/cs212/2008sp/Compiler/SaM/doc/SaMDesign-2.6.2/node29.html
- SaM Summary: https://www.cs.cornell.edu/courses/cs212/2004sp/SaMSummary.htm
