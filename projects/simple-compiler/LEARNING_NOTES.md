# Learning Notes - Simple Compiler

## What I Learned

### 1. The Compilation Pipeline

A compiler transforms source code through multiple phases, each with a specific responsibility:

```
Source Code → Lexer → Parser → Code Generator → VM
```

**Key Takeaway**: Separating compilation into phases makes each phase simpler and more testable. The lexer doesn't need to understand syntax, the parser doesn't need to know about bytecode, etc.

### 2. Lexical Analysis (Tokenization)

The lexer reads characters and groups them into tokens. It's essentially a state machine that recognizes patterns.

**Key Concepts:**
- **Token**: A categorized unit (e.g., `INTEGER`, `IDENTIFIER`, `PLUS`)
- **Lexeme**: The actual text (e.g., `42`, `x`, `+`)
- **Lookahead**: Sometimes need to peek at the next character to decide token type

**Example:**
```
Source:  let x = 42;
Tokens: [LET] [IDENTIFIER("x")] [EQUAL] [INTEGER(42)] [SEMICOLON]
```

**Key Takeaway**: Hand-written lexers are surprisingly simple and give full control over error messages. Regular expressions work too but are less flexible.

### 3. Syntax Analysis (Parsing)

The parser builds a tree representation (AST) from the token stream. Recursive descent parsing is intuitive: each grammar rule becomes a function.

**Key Concepts:**
- **Grammar**: Rules defining valid syntax
- **Precedence**: Which operators bind tighter (`*` before `+`)
- **Associativity**: Direction of evaluation (`1-2-3` = `(1-2)-3`)

**Operator Precedence (lowest to highest):**
1. `||` (logical or)
2. `&&` (logical and)
3. `==`, `!=` (equality)
4. `<`, `<=`, `>`, `>=` (comparison)
5. `+`, `-` (addition/subtraction)
6. `*`, `/`, `%` (multiplication/division)
7. `-x`, `!x` (unary)

**Key Takeaway**: Precedence climbing (nested function calls) is an elegant way to handle operator precedence. Each precedence level has its own parsing function.

### 4. Abstract Syntax Tree (AST)

The AST is a tree representation of the program structure. Each node represents a language construct.

**Example:**
```
let x = 1 + 2 * 3;

Statement::Let {
    name: "x",
    value: Expression::BinaryOp {
        op: Add,
        left: IntegerLiteral(1),
        right: BinaryOp {
            op: Mul,
            left: IntegerLiteral(2),
            right: IntegerLiteral(3),
        }
    }
}
```

**Key Takeaway**: Rust's enums with data are perfect for AST nodes. Pattern matching makes tree traversal clean and exhaustive.

### 5. Code Generation

The code generator translates the AST into bytecode instructions for a stack-based virtual machine.

**Key Concepts:**
- **Stack-based**: Values are pushed onto a stack; operations pop operands and push results
- **Backpatching**: Jump addresses are filled in after we know where to jump
- **Short-circuit**: `&&` and `||` don't always evaluate both sides

**Example:**
```
Expression: 1 + 2 * 3

Bytecode:
  PushInt(1)      // Push 1
  PushInt(2)      // Push 2
  PushInt(3)      // Push 3
  Mul             // Pop 2,3; push 6
  Add             // Pop 1,6; push 7
```

**Key Takeaway**: Stack-based bytecode is simple to generate and execute. The stack naturally handles expression evaluation order.

### 6. Virtual Machine Execution

The VM executes bytecode instructions sequentially, maintaining a stack and call frames.

**Key Concepts:**
- **Program Counter (PC)**: Points to the current instruction
- **Stack**: Stores values for expression evaluation
- **Call Stack**: Stores function call frames with local variables
- **Backpatching**: Jump addresses filled in during code generation

**Key Takeaway**: A stack-based VM is much simpler than a register-based one. The stack automatically handles expression evaluation order.

### 7. Control Flow Implementation

If/else and while loops use conditional jumps:

**If/else:**
```
PushBool(condition)
JumpIfFalse(else_addr)  // Jump to else if false
// then block
Jump(end_addr)          // Skip else block
// else block (at else_addr)
// end (at end_addr)
```

**While loop:**
```
loop_start:
  PushBool(condition)
  JumpIfFalse(loop_end)
  // body
  Jump(loop_start)
loop_end:
```

**Key Takeaway**: Backpatching is essential. We emit jumps with placeholder addresses, then patch them later when we know the target.

### 8. Function Implementation

Functions require:
1. A jump over the function body (so it's not executed at definition time)
2. Local variable storage per call
3. A call stack to save/restore state

**Key Takeaway**: Function calls are essentially jumps with state saving. The call stack stores the return address and local variables.

### 9. Recursion

Recursion works naturally with the call stack:

```
fn factorial(n) {
    if n <= 1 { return 1; }
    return n * factorial(n - 1);
}
```

Each recursive call creates a new stack frame with its own `n` value. When the base case is reached, the return values propagate back up the call stack.

**Key Takeaway**: Recursion is just repeated function calls. The call stack handles all the bookkeeping.

### 10. Error Handling

Good error messages are crucial for a usable compiler:

- **Lexer errors**: Invalid characters, unterminated strings
- **Parser errors**: Unexpected tokens, missing semicolons
- **Runtime errors**: Undefined variables, type mismatches, division by zero

**Key Takeaway**: Include line and column numbers in error messages. It makes debugging much easier.

## Challenges Faced

### 1. Operator Precedence

Getting operator precedence right was tricky. The solution was precedence climbing - each precedence level has its own parsing function that calls the next higher precedence level.

**Solution**: Use nested functions where each level handles one precedence level.

### 2. Control Flow Jumps

For if/else and while loops, we need to jump to addresses that aren't known yet (forward jumps).

**Solution**: Emit jumps with placeholder addresses (0), then patch them later when we know the target address.

### 3. Short-Circuit Evaluation

Logical `&&` and `||` should not always evaluate both operands.

**Solution**: Use conditional jumps. For `a && b`, if `a` is false, skip `b`. For `a || b`, if `a` is true, skip `b`.

### 4. Function Calls

Implementing function calls required:
- Storing function metadata (name, parameters, start address)
- Creating a new stack frame for each call
- Saving/restoring the program counter

**Solution**: Maintain a call stack with frames containing local variables and return addresses.

### 5. Variable Scoping

Variables need to be accessible in the correct scope (local vs global).

**Solution**: Check locals first (in the current frame), then globals.

## Design Decisions

### 1. Hand-Written Lexer

**Decision**: Write the lexer by hand instead of using regex or a lexer generator.

**Rationale**: More control over error messages, easier to debug, and educational (understanding how lexers work).

### 2. Recursive Descent Parser

**Decision**: Use recursive descent parsing.

**Rationale**: Intuitive (each grammar rule = one function), easy to understand, and good error messages.

### 3. Stack-Based Bytecode

**Decision**: Use stack-based bytecode instead of register-based.

**Rationale**: Simpler to generate (no register allocation), simpler to execute (just push/pop), and educational.

### 4. Dynamic Typing

**Decision**: Types are checked at runtime, not compile time.

**Rationale**: Simpler implementation (no type checker needed), but trades performance for simplicity.

### 5. Rust Implementation

**Decision**: Implement in Rust.

**Rationale**: Strong type system catches bugs at compile time, pattern matching is perfect for AST/bytecode handling, and good performance.

## What I Would Do Differently

1. **Add Type Checking**: Currently types are only checked at runtime. A type checker would catch errors earlier and enable optimizations.

2. **Implement Garbage Collection**: Currently, strings are cloned on every operation. A GC would be more efficient.

3. **Add Tail Call Optimization**: Recursive functions like factorial could be optimized to use constant stack space.

4. **Better Error Recovery**: Currently, the parser stops at the first error. It could skip to the next statement and continue parsing.

5. **Add More Data Types**: Arrays, maps, and structs would make the language more useful.

6. **Implement Closures**: Functions that capture variables from their enclosing scope.

7. **Add a Standard Library**: Common functions like string manipulation, math, and I/O.

## Next Steps

To extend this project:

1. **Add Type System**: Static type checking before execution
2. **Add Arrays**: `[1, 2, 3]` syntax with indexing
3. **Add Structs**: `struct Point { x: int, y: int }`
4. **Add Closures**: `let add = |x, y| x + y;`
5. **Add Modules**: `import math; math.sqrt(4);`
6. **Optimize Bytecode**: Constant folding, dead code elimination
7. **Add JIT Compilation**: Compile hot paths to native code
8. **Add Debugging**: Step-through execution, breakpoints

## Resources That Helped

1. **Crafting Interpreters** by Robert Nystrom
   - Excellent book on building interpreters
   - https://craftinginterpreters.com/

2. **Writing An Interpreter In Go** by Thorsten Ball
   - Practical, hands-on approach
   - https://interpreterbook.com/

3. **Rust Documentation**
   - Pattern matching, enums, error handling
   - https://doc.rust-lang.org/

4. **LLVM Tutorial**
   - Building a compiler with LLVM
   - https://llvm.org/docs/tutorial/

5. **Wikipedia: Compiler**
   - Overview of compilation phases
   - https://en.wikipedia.org/wiki/Compiler
