# Design - Simple Compiler

## Design Goals

1. **Educational**: Clear, understandable code that teaches compiler concepts
2. **Functional**: A working compiler that can execute real programs
3. **Extensible**: Easy to add new features and language constructs
4. **Minimal**: Focus on core concepts without unnecessary complexity

## Language Design

### Simple Language (SL) Features

The Simple Language supports:
- Variable declarations and assignments
- Arithmetic operations (+, -, *, /, %)
- Comparison operators (==, !=, <, <=, >, >=)
- Logical operators (&&, ||, !)
- Control flow (if/else, while loops)
- Functions with recursion
- Print statements
- Integer, float, boolean, and string types

### Syntax Examples

```
// Variable declaration
let x = 42;
let name = "World";

// Arithmetic
let result = (a + b) * c;

// Control flow
if x > 0 {
    print("positive");
} else if x < 0 {
    print("negative");
} else {
    print("zero");
}

// Loops
let i = 0;
while i < 10 {
    print(i);
    i = i + 1;
}

// Functions
fn factorial(n) {
    if n <= 1 {
        return 1;
    }
    return n * factorial(n - 1);
}
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Simple Compiler                          │
│                                                             │
│  Source Code                                                │
│      │                                                      │
│      ▼                                                      │
│  ┌──────────┐     ┌──────────┐     ┌──────────────────┐   │
│  │  Lexer   │────▶│  Parser  │────▶│  Code Generator  │   │
│  │          │     │          │     │                  │   │
│  │ Source → │     │ Tokens → │     │ AST → Bytecode   │   │
│  │ Tokens   │     │ AST      │     │                  │   │
│  └──────────┘     └──────────┘     └────────┬─────────┘   │
│                                              │              │
│                                              ▼              │
│                                      ┌──────────────────┐  │
│                                      │   Virtual Machine │  │
│                                      │                  │  │
│                                      │ Execute bytecode │  │
│                                      └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. Lexer (src/lexer.rs)

**Responsibility**: Convert source code into tokens

**Design Decisions:**
- Hand-written scanner (faster, more control than regex)
- Single-pass, no lookahead beyond 1 character
- Line and column tracking for error messages
- Support for comments (line and block)

**Token Types:**
```
Literals:   Integer, Float, String, Bool
Keywords:   let, if, else, while, fn, return, print, true, false
Operators:  +, -, *, /, %, =, ==, !=, <, <=, >, >=, !, &&, ||, ->
Delimiters: (, ), {, }, ,, ;, :
Special:    Eof (end of file)
```

**Key Implementation:**
```rust
pub struct Lexer {
    source: Vec<char>,
    pos: usize,
    line: usize,
    column: usize,
}
```

### 2. Parser (src/parser.rs)

**Responsibility**: Convert tokens into an Abstract Syntax Tree

**Design Decisions:**
- Recursive descent parsing (intuitive, easy to understand)
- Operator precedence climbing for expressions
- Good error messages with line/column information

**Grammar:**
```
program     → statement*
statement   → let_stmt | assign_stmt | print_stmt | if_stmt
            | while_stmt | fn_def | return_stmt | expr_stmt

let_stmt    → "let" IDENT "=" expr ";"
assign_stmt → IDENT "=" expr ";"
print_stmt  → "print" "(" expr ("," expr)* ")" ";"
if_stmt     → "if" expr block ("else" block)?
while_stmt  → "while" expr block
fn_def      → "fn" IDENT "(" params? ")" ("->" type)? block
return_stmt → "return" expr? ";"
block       → "{" statement* "}"

expr        → or_expr
or_expr     → and_expr ("||" and_expr)*
and_expr    → equality ("&&" equality)*
equality    → comparison (("==" | "!=") comparison)*
comparison  → addition (("<" | "<=" | ">" | ">=") addition)*
addition    → multiplication (("+" | "-") multiplication)*
multiplication → unary (("*" | "/" | "%") unary)*
unary       → ("-" | "!") unary | call
call        → primary ("(" args? ")")?
primary     → INTEGER | FLOAT | STRING | "true" | "false" | IDENT | "(" expr ")"
```

### 3. AST (src/ast.rs)

**Responsibility**: Define the tree structure representing the program

**Design Decisions:**
- Enum-based nodes (Rust's pattern matching is perfect for this)
- Clear separation between statements and expressions
- Include source location information (for future error reporting)

**Node Types:**
```rust
enum Statement {
    Let { name, value },
    Assign { name, value },
    Print { args },
    If { condition, then_block, else_block },
    While { condition, body },
    FunctionDef { name, params, return_type, body },
    Return { value },
    Expression { expr },
}

enum Expression {
    IntegerLiteral(i64),
    FloatLiteral(f64),
    StringLiteral(String),
    BoolLiteral(bool),
    Identifier(String),
    BinaryOp { op, left, right },
    UnaryOp { op, operand },
    Call { name, args },
}
```

### 4. Code Generator (src/codegen.rs)

**Responsibility**: Translate AST into bytecode instructions

**Design Decisions:**
- Stack-based bytecode (simpler than register-based)
- Backpatching for control flow (jump addresses filled in after generation)
- Short-circuit evaluation for logical operators
- Function code embedded in main instruction stream

**Bytecode Instructions:**
```
Stack:      PushInt, PushFloat, PushBool, PushStr, Pop, Dup
Variables:  LoadLocal, StoreLocal
Arithmetic: Add, Sub, Mul, Div, Mod, Neg
Comparison: Eq, NotEq, Lt, LtEq, Gt, GtEq
Logical:    And, Or, Not
Control:    Jump, JumpIfFalse, JumpIfTrue
Functions:  Call, Return
I/O:        Print
```

### 5. Virtual Machine (src/vm.rs)

**Responsibility**: Execute bytecode instructions

**Design Decisions:**
- Stack-based execution
- Call stack for function calls with local variable frames
- Dynamic type checking at runtime
- String output collection (for testing)

**Runtime Value Types:**
```rust
enum Value {
    Int(i64),
    Float(f64),
    Bool(bool),
    Str(String),
}
```

## Data Flow

```
"let x = 1 + 2;"

Lexer Output:
  [Let, Identifier("x"), Equal, Integer(1), Plus, Integer(2), Semicolon]

Parser Output:
  Statement::Let {
      name: "x",
      value: Expression::BinaryOp {
          op: Add,
          left: IntegerLiteral(1),
          right: IntegerLiteral(2),
      }
  }

Code Generator Output:
  [
      PushInt(1),
      PushInt(2),
      Add,
      StoreLocal("x"),
  ]

VM Execution:
  Stack: []         → PushInt(1) → [1]
  Stack: [1]        → PushInt(2) → [1, 2]
  Stack: [1, 2]     → Add        → [3]
  Stack: [3]        → StoreLocal → []  (x = 3)
```

## Error Handling Strategy

### Lexer Errors
- Invalid characters
- Unterminated strings
- Invalid number formats

### Parser Errors
- Unexpected tokens
- Missing semicolons
- Invalid expressions

### Runtime Errors
- Undefined variables
- Type mismatches
- Division by zero
- Stack underflow

## Testing Strategy

### Unit Tests
- Each component tested independently
- Edge cases covered
- Error conditions tested

### Integration Tests
- End-to-end compilation and execution
- Example programs verified
- Error recovery tested

## Future Extensions

Potential additions to the language:
1. Arrays and indexing
2. Structs/records
3. Pattern matching
4. Closures
5. Module system
6. Standard library
7. Garbage collection
8. JIT compilation
