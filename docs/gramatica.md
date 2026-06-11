# Gramatica Inicial

Esta e a primeira versao da gramatica da linguagem. Ela foi desenhada para ser
simples de analisar com parser descendente recursivo manual.

## Exemplo

```text
fn main() -> int {
  int x;
  x = 10;

  if (x > 0) {
    x = x + 1;
  } else {
    x = 0;
  }

  while (x < 20) {
    x = x + 2;
  }

  return x;
}
```

## Palavras reservadas

```text
fn proc return if else while int float char bool true false void
```

## EBNF

```text
program        ::= declaration* EOF ;

declaration    ::= function_decl
                 | procedure_decl ;

function_decl  ::= "fn" identifier "(" parameters? ")" "->" type block ;
procedure_decl ::= "proc" identifier "(" parameters? ")" block ;

parameters     ::= parameter ("," parameter)* ;
parameter      ::= type identifier ;

type           ::= "int"
                 | "float"
                 | "char"
                 | "bool"
                 | "void" ;

block          ::= "{" statement* "}" ;

statement      ::= var_decl
                 | assignment ";"
                 | call_stmt
                 | if_stmt
                 | while_stmt
                 | return_stmt
                 | block ;

var_decl       ::= type identifier ("=" expression)? ";" ;
assignment     ::= identifier "=" expression ;
call_stmt      ::= call ";" ;

if_stmt        ::= "if" "(" expression ")" block ("else" block)? ;
while_stmt     ::= "while" "(" expression ")" block ;
return_stmt    ::= "return" expression? ";" ;

expression     ::= logic_or ;
logic_or       ::= logic_and ("||" logic_and)* ;
logic_and      ::= equality ("&&" equality)* ;
equality       ::= comparison (("==" | "!=") comparison)* ;
comparison     ::= term ((">" | ">=" | "<" | "<=") term)* ;
term           ::= factor (("+" | "-") factor)* ;
factor         ::= unary (("*" | "/" | "%") unary)* ;
unary          ::= ("!" | "-") unary
                 | primary ;

primary        ::= integer_literal
                 | float_literal
                 | char_literal
                 | "true"
                 | "false"
                 | identifier
                 | call
                 | "(" expression ")" ;

call           ::= identifier "(" arguments? ")" ;
arguments      ::= expression ("," expression)* ;
```

## Precedencia de operadores

Da maior para a menor:

| Nivel | Operadores | Associatividade |
| --- | --- | --- |
| Unario | `!`, `-` | direita |
| Multiplicativo | `*`, `/`, `%` | esquerda |
| Aditivo | `+`, `-` | esquerda |
| Relacional | `>`, `>=`, `<`, `<=` | esquerda |
| Igualdade | `==`, `!=` | esquerda |
| E logico | `&&` | esquerda |
| Ou logico | `||` | esquerda |

## Comentarios

```text
// comentario de linha
/* comentario de bloco */
```

## Observacoes

- `bool` entra como opcional estrategico, pois deixa a analise semantica das
  expressoes logicas mais clara.
- `void` e usado para procedimentos e funcoes sem retorno quando decidirmos
  unificar a sintaxe.
- Vetores e strings ficam fora desta primeira gramatica para manter o nucleo
  estavel.
