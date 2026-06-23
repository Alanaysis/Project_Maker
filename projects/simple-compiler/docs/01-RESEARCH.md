# Research - Simple Compiler

## What is a Compiler?

A compiler is a program that translates source code written in a high-level programming language into a lower-level language (typically machine code, bytecode, or another programming language). The compilation process consists of several phases, each transforming the program representation closer to the target language.

## Compiler Architecture

### Traditional Pipeline

```
Source Code
    │
    ▼
┌─────────────────┐
│ Lexical Analysis │  (Scanner/Lexer)
│ "Tokenization"  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Syntax Analysis  │  (Parser)
│ "Parsing"       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Semantic Analysis │
│ "Type Checking" │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Intermediate     │
│ Code Generation  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Code Optimization│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Target Code      │
│ Generation       │
└─────────────────┘
```

### Phase 1: Lexical Analysis (Scanning)

The lexer reads the source code character by character and groups them into **tokens**. Each token represents a meaningful unit: keywords, identifiers, literals, operators, etc.

**Key Concepts:**
- **Token**: A categorized group of characters (e.g., `INTEGER`, `IDENTIFIER`, `PLUS`)
- **Lexeme**: The actual text of a token (e.g., `42`, `x`, `+`)
- **Pattern**: The rule that matches a lexeme for a token type

**Example:**
```
Source:  let x = 42 + y;
Tokens: [LET] [IDENTIFIER("x")] [EQUAL] [INTEGER(42)] [PLUS] [IDENTIFIER("y")] [SEMICOLON]
```

**Techniques:**
- Regular expressions for pattern matching
- State machines (Deterministic Finite Automata)
- Hand-written scanners (often faster than regex-based)

### Phase 2: Syntax Analysis (Parsing)

The parser takes the token stream and builds an **Abstract Syntax Tree (AST)**. The AST represents the grammatical structure of the program.

**Key Concepts:**
- **Grammar**: A set of rules defining valid syntax (usually context-free grammar)
- **Parse Tree**: A concrete representation of the grammar rules applied
- **Abstract Syntax Tree (AST)**: A simplified tree that omits unnecessary details

**Parsing Techniques:**
- **Recursive Descent**: Simple, intuitive, top-down parsing. Each grammar rule maps to a function.
- **LL Parsing**: Left-to-right, Leftmost derivation. Table-driven.
- **LR Parsing**: Left-to-right, Rightmost derivation. More powerful, handles more grammars.
- **Operator Precedence**: Specialized for expressions. Uses precedence climbing.

**Example Grammar:**
```
program     → statement*
statement   → "let" IDENT "=" expr ";"
expr        → term (("+" | "-") term)*
term        → factor (("*" | "/") factor)*
factor      → INTEGER | IDENT | "(" expr ")"
```

### Phase 3: Semantic Analysis

Checks the program for meaning-related errors that syntax analysis cannot catch:
- Type checking
- Scope resolution
- Variable declaration before use
- Function argument count matching

### Phase 4: Intermediate Code Generation

Translates the AST into an intermediate representation (IR). Common IRs:
- **Three-Address Code**: Each instruction has at most three operands
- **Bytecode**: Stack-based or register-based virtual machine instructions
- **SSA (Static Single Assignment)**: Each variable is assigned exactly once

### Phase 5: Code Optimization

Transforms the IR to make it more efficient:
- Constant folding: `3 + 4` → `7`
- Dead code elimination
- Loop optimizations
- Register allocation

### Phase 6: Target Code Generation

Translates the optimized IR into the target language:
- Machine code (native execution)
- Bytecode (virtual machine execution)
- Another programming language (transpilation)

## Key Data Structures

### Tokens
```rust
enum Token {
    Integer(i64),       // 42
    Identifier(String), // x, foo
    Plus,               // +
    Equal,              // =
    Let,                // let (keyword)
    Eof,                // end of file
}
```

### Abstract Syntax Tree
```rust
enum Expression {
    IntegerLiteral(i64),
    Identifier(String),
    BinaryOp {
        op: Operator,
        left: Box<Expression>,
        right: Box<Expression>,
    },
}
```

### Bytecode Instructions
```rust
enum Instruction {
    PushInt(i64),      // Push integer onto stack
    Add,               // Pop two, push sum
    StoreLocal(String), // Pop and store in variable
    JumpIfFalse(usize), // Conditional jump
}
```

## Parsing Techniques Deep Dive

### Recursive Descent Parsing

The most intuitive parsing technique. Each grammar rule becomes a function.

**Advantages:**
- Easy to understand and implement
- Good error messages
- Easy to debug

**Disadvantages:**
- Cannot handle left recursion directly
- May be slower than table-driven parsers

**Example:**
```rust
fn parse_expression(&mut self) -> Result<Expression, String> {
    let left = self.parse_term()?;
    if self.check(Token::Plus) {
        self.advance();
        let right = self.parse_term()?;
        Ok(Expression::Add(Box::new(left), Box::new(right)))
    } else {
        Ok(left)
    }
}
```

### Operator Precedence Climbing

A technique for parsing expressions with correct operator precedence.

**Precedence Table:**
| Precedence | Operators |
|------------|-----------|
| 1 (lowest) | `||` |
| 2 | `&&` |
| 3 | `==`, `!=` |
| 4 | `<`, `<=`, `>`, `>=` |
| 5 | `+`, `-` |
| 6 | `*`, `/`, `%` |
| 7 (highest) | `-x`, `!x` (unary) |

**Example:**
```
1 + 2 * 3
Parsed as: 1 + (2 * 3)  // * has higher precedence
```

## Stack-Based Virtual Machines

### Concept

A stack-based VM uses a stack data structure for computation:
- Values are pushed onto the stack
- Operations pop values and push results
- No registers needed (simpler design)

**Example:**
```
Code:   1 + 2 * 3

Stack operations:
  PushInt(1)      Stack: [1]
  PushInt(2)      Stack: [1, 2]
  PushInt(3)      Stack: [1, 2, 3]
  Mul             Stack: [1, 6]      // 2 * 3 = 6
  Add             Stack: [7]         // 1 + 6 = 7
```

### Advantages
- Simple instruction set
- Easy to implement
- Portable (runs on any platform with the VM)

### Disadvantages
- More instructions than register-based
- Stack manipulation overhead

## Real-World Compilers

### GCC (GNU Compiler Collection)
- Multi-stage compilation
- Supports many languages (C, C++, Go, etc.)
- Complex optimization passes

### LLVM
- Modular compiler infrastructure
- Intermediate representation (LLVM IR)
- Used by Rust, Swift, Clang

### V8 (JavaScript)
- JIT (Just-In-Time) compilation
- Multiple optimization tiers
- Hot code detection

### Rust Compiler
- Self-hosting (written in Rust)
- Uses LLVM backend
- Strong type system with borrow checker

## Learning Resources

1. **"Crafting Interpreters" by Robert Nystrom**
   - Excellent free online book
   - Builds two complete interpreters
   - https://craftinginterpreters.com/

2. **"Compilers: Principles, Techniques, and Tools" (Dragon Book)**
   - The classic compiler textbook
   - Comprehensive but dense

3. **"Writing An Interpreter In Go" by Thorsten Ball**
   - Practical, hands-on approach
   - Builds a working interpreter

4. **LLVM Tutorial**
   - Building a compiler with LLVM
   - https://llvm.org/docs/tutorial/

5. **Rust Compiler Source**
   - Real-world compiler implementation
   - https://github.com/rust-lang/rust
