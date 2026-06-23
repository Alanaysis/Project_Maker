# Simple Compiler

A simple compiler implementation in Rust, built for learning compiler construction principles.

## Overview

This project implements a complete compiler for a simple programming language, covering the fundamental phases of compilation:

1. **Lexical Analysis** (Tokenization)
2. **Syntax Analysis** (Parsing)
3. **Code Generation** (Bytecode)
4. **Execution** (Virtual Machine)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Simple Compiler                          │
│                                                             │
│  Source Code (.sl)                                          │
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

## Project Structure

```
simple-compiler/
├── Cargo.toml              # Project configuration
├── README.md               # This file
├── LEARNING_NOTES.md       # Learning notes
├── docs/                   # Documentation
│   ├── 01-RESEARCH.md      # Research notes
│   ├── 02-DESIGN.md        # Design decisions
│   ├── 03-IMPLEMENTATION.md # Implementation details
│   ├── 04-TESTING.md        # Testing strategy
│   └── 05-DEVELOPMENT.md    # Development guide
├── src/                    # Source code
│   ├── lib.rs              # Module declarations
│   ├── main.rs             # CLI entry point
│   ├── lexer.rs            # Lexer (tokenization)
│   ├── parser.rs           # Parser (AST construction)
│   ├── ast.rs              # AST node definitions
│   ├── codegen.rs          # Code generator (bytecode)
│   └── vm.rs               # Virtual machine (execution)
├── examples/               # Example programs
│   ├── hello.sl            # Hello World
│   ├── arithmetic.sl       # Arithmetic operations
│   ├── variables.sl        # Variable operations
│   ├── loops.sl            # While loops
│   ├── functions.sl        # Function definitions
│   ├── factorial.sl        # Recursive factorial
│   ├── fibonacci.sl        # Fibonacci sequence
│   ├── fizzbuzz.sl         # FizzBuzz game
│   └── primes.sl           # Prime number finder
└── tests/                  # Integration tests
```

## Quick Start

### Prerequisites

- Rust 1.70 or later

### Build and Run

```bash
# Build the project
cargo build

# Run the REPL
cargo run

# Run an example program
cargo run -- run examples/hello.sl

# Run all tests
cargo test
```

### Using the REPL

```bash
$ cargo run
Simple Compiler REPL
Type 'exit' or 'quit' to exit, 'help' for help

> print("Hello, World!");
Hello, World!

> let x = 10;
> let y = 20;
> print(x + y);
30

> fn factorial(n) {
>     if n <= 1 {
>         return 1;
>     }
>     return n * factorial(n - 1);
> }
> print(factorial(10));
3628800

> exit
Goodbye!
```

### Running Example Programs

```bash
# Hello World
cargo run -- run examples/hello.sl

# Fibonacci sequence
cargo run -- run examples/fibonacci.sl

# Prime numbers
cargo run -- run examples/primes.sl
```

### Showing Compilation Details

```bash
# Show tokens, AST, and bytecode
cargo run -- compile examples/arithmetic.sl
```

## Language Syntax

### Variables

```
let x = 42;
let name = "World";
let pi = 3.14;
let is_valid = true;

x = x + 1;  // Reassignment
```

### Arithmetic

```
let result = (a + b) * c - d / e % f;
```

### Comparison

```
if x == 42 { ... }
if x != 0 { ... }
if x < 100 { ... }
if x <= 50 { ... }
if x > 0 { ... }
if x >= 10 { ... }
```

### Logical Operators

```
if x > 0 && x < 100 { ... }
if x == 0 || y == 0 { ... }
if !is_empty { ... }
```

### Control Flow

```
// If/else
if x > 0 {
    print("positive");
} else if x < 0 {
    print("negative");
} else {
    print("zero");
}

// While loop
let i = 0;
while i < 10 {
    print(i);
    i = i + 1;
}
```

### Functions

```
// Function definition
fn add(x, y) {
    return x + y;
}

// Function call
let sum = add(3, 4);
print(sum);  // 7

// Recursive function
fn factorial(n) {
    if n <= 1 {
        return 1;
    }
    return n * factorial(n - 1);
}
```

### Print Statement

```
print("Hello");
print(x);
print("x =", x);
print(a, b, c);  // Multiple values
```

### Comments

```
// This is a line comment

/* This is
   a block comment */
```

## Command Line Interface

```
USAGE:
  sc                 Start the REPL (interactive mode)
  sc repl            Start the REPL
  sc run <file>      Compile and run a file
  sc compile <file>  Compile a file and show bytecode
  sc help            Show help message
```

## Key Concepts

### 1. Lexical Analysis (Tokenization)

The lexer converts source code into tokens:

```
Source:  let x = 42 + y;
Tokens: [LET] [IDENTIFIER("x")] [EQUAL] [INTEGER(42)] [PLUS] [IDENTIFIER("y")] [SEMICOLON]
```

### 2. Syntax Analysis (Parsing)

The parser builds an Abstract Syntax Tree (AST):

```
Statement::Let {
    name: "x",
    value: Expression::BinaryOp {
        op: Add,
        left: IntegerLiteral(42),
        right: Identifier("y"),
    }
}
```

### 3. Code Generation

The code generator produces stack-based bytecode:

```
PushInt(42)
LoadLocal("y")
Add
StoreLocal("x")
```

### 4. Virtual Machine Execution

The VM executes bytecode using a stack:

```
Stack: []         → PushInt(42)    → [42]
Stack: [42]       → LoadLocal("y") → [42, y_value]
Stack: [42, y]    → Add            → [42 + y]
Stack: [result]   → StoreLocal("x")→ []  (x = result)
```

## Testing

```bash
# Run all tests
cargo test

# Run with output
cargo test -- --nocapture

# Run specific test
cargo test test_fibonacci
```

## Example Programs

| File | Description |
|------|-------------|
| `hello.sl` | Hello World |
| `arithmetic.sl` | Basic math operations |
| `variables.sl` | Variable declaration and assignment |
| `loops.sl` | While loops |
| `functions.sl` | Function definitions and calls |
| `factorial.sl` | Recursive factorial |
| `fibonacci.sl` | Fibonacci sequence |
| `fizzbuzz.sl` | FizzBuzz game |
| `primes.sl` | Prime number finder |

## Learning Resources

- [Crafting Interpreters](https://craftinginterpreters.com/) - Excellent book on building interpreters
- [Writing An Interpreter In Go](https://interpreterbook.com/) - Practical interpreter implementation
- [LLVM Tutorial](https://llvm.org/docs/tutorial/) - Building a compiler with LLVM
- [Rust Book](https://doc.rust-lang.org/book/) - Learn Rust

## License

This project is for educational purposes.

---

[返回主目录](../../README.md)
