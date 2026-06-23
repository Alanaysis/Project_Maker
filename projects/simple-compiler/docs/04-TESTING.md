# Testing - Simple Compiler

## Testing Strategy

The Simple Compiler uses a multi-layered testing approach:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test the complete compilation pipeline
3. **Example Programs**: Verify real-world program execution

## Running Tests

```bash
# Run all tests
cargo test

# Run tests with output
cargo test -- --nocapture

# Run specific test module
cargo test lexer::tests

# Run a single test
cargo test test_let_statement
```

## Unit Tests

### Lexer Tests (src/lexer.rs)

The lexer tests verify tokenization of all token types:

**Token Types:**
- Single-character operators: `+`, `-`, `*`, `/`, `%`, `=`
- Two-character operators: `==`, `!=`, `<=`, `>=`, `&&`, `||`, `->`
- Literals: integers, floats, strings
- Keywords: `let`, `if`, `else`, `while`, `fn`, `return`, `print`, `true`, `false`
- Identifiers: `foo`, `bar_baz`, `x1`
- Delimiters: `(`, `)`, `{`, `}`, `,`, `;`, `:`

**Edge Cases:**
- Empty source
- Comments (line and block)
- String escapes (`\n`, `\t`, `\\`, `\"`)
- Unterminated strings
- Invalid characters
- Line/column tracking

**Example Test:**
```rust
#[test]
fn test_let_statement() {
    let mut lexer = Lexer::new("let x = 42;");
    let tokens = lexer.tokenize().unwrap();
    assert_eq!(tokens[0].kind, TokenKind::Let);
    assert_eq!(tokens[1].kind, TokenKind::Identifier("x".to_string()));
    assert_eq!(tokens[2].kind, TokenKind::Equal);
    assert_eq!(tokens[3].kind, TokenKind::Integer(42));
    assert_eq!(tokens[4].kind, TokenKind::Semicolon);
}
```

### Parser Tests (src/parser.rs)

The parser tests verify AST construction:

**Statement Types:**
- Let statements
- Assignment statements
- Print statements
- If/else statements
- While loops
- Function definitions
- Return statements
- Expression statements

**Expression Parsing:**
- Operator precedence
- Parenthesized expressions
- Unary operators
- Function calls
- Nested expressions

**Example Test:**
```rust
#[test]
fn test_binary_expression() {
    let program = parse("let x = 1 + 2 * 3;");
    match &program.statements[0] {
        Statement::Let { value, .. } => {
            // Should parse as 1 + (2 * 3)
            match value {
                Expression::BinaryOp { op: BinaryOp::Add, left, right } => {
                    assert_eq!(**left, Expression::IntegerLiteral(1));
                    match right.as_ref() {
                        Expression::BinaryOp { op: BinaryOp::Mul, .. } => {}
                        _ => panic!("Expected Mul"),
                    }
                }
                _ => panic!("Expected Add"),
            }
        }
        _ => panic!("Expected Let"),
    }
}
```

### Code Generator Tests (src/codegen.rs)

The code generator tests verify bytecode emission:

**Coverage:**
- Simple assignments
- Arithmetic expressions
- Operator precedence
- Print statements
- If/else control flow
- While loops
- Function definitions
- Function calls
- Comparison operators
- Unary operators
- Short-circuit evaluation
- Disassembler output

**Example Test:**
```rust
#[test]
fn test_if_else() {
    let instructions = compile("if true { print(1); } else { print(2); }");
    assert_eq!(instructions[0], Instruction::PushBool(true));
    assert_eq!(instructions[1], Instruction::JumpIfFalse(5));
    assert_eq!(instructions[2], Instruction::PushInt(1));
    assert_eq!(instructions[3], Instruction::Print(1));
    assert_eq!(instructions[4], Instruction::Jump(7));
    assert_eq!(instructions[5], Instruction::PushInt(2));
    assert_eq!(instructions[6], Instruction::Print(1));
}
```

### VM Tests (src/vm.rs)

The VM tests verify bytecode execution:

**Coverage:**
- Basic I/O (print)
- Arithmetic operations
- Variables (declaration, assignment, access)
- Control flow (if/else, while)
- Functions (definition, calls, recursion)
- String operations
- Comparison operators
- Logical operators
- Error conditions (division by zero, undefined variables)

**Example Test:**
```rust
#[test]
fn test_fibonacci() {
    let output = run_program(
        r#"
        fn fib(n) {
            if n <= 1 {
                return n;
            }
            return fib(n - 1) + fib(n - 2);
        }
        print(fib(10));
        "#,
    );
    assert_eq!(output, vec!["55"]);
}
```

## Integration Tests

Integration tests verify the complete pipeline from source to output:

```rust
#[test]
fn test_compile_and_run() {
    let output = compile_and_run("print(42);").unwrap();
    assert_eq!(output, vec!["42"]);
}
```

## Example Programs

The `examples/` directory contains programs that serve as both documentation and integration tests:

| File | Description | Expected Output |
|------|-------------|-----------------|
| `hello.sl` | Hello World | "Hello, World!" |
| `arithmetic.sl` | Basic math | Various calculations |
| `variables.sl` | Variable operations | Variable values |
| `loops.sl` | While loops | Counted output |
| `functions.sl` | Function definitions | Function results |
| `factorial.sl` | Recursive factorial | 0! through 10! |
| `fibonacci.sl` | Fibonacci sequence | fib(0) through fib(9) |
| `fizzbuzz.sl` | FizzBuzz game | FizzBuzz output |
| `primes.sl` | Prime numbers | Primes up to 50 |

## Test Helpers

### compile() Function

Compiles source code to bytecode (for code generator tests):

```rust
fn compile(source: &str) -> Vec<Instruction> {
    let mut lexer = Lexer::new(source);
    let tokens = lexer.tokenize().unwrap();
    let mut parser = Parser::new(tokens);
    let program = parser.parse().unwrap();
    let mut codegen = CodeGenerator::new();
    codegen.generate(&program).unwrap()
}
```

### run_program() Function

Compiles and executes source code (for VM tests):

```rust
fn run_program(source: &str) -> Vec<String> {
    let mut lexer = Lexer::new(source);
    let tokens = lexer.tokenize().unwrap();
    let mut parser = Parser::new(tokens);
    let program = parser.parse().unwrap();
    let mut codegen = CodeGenerator::new();
    let instructions = codegen.generate(&program).unwrap();
    let functions = codegen.get_functions().to_vec();
    let mut vm = VM::new(instructions, functions);
    vm.run().unwrap()
}
```

## Coverage Areas

### What's Well Covered
- All token types
- All statement types
- All expression types
- Operator precedence
- Control flow (if/else, while)
- Functions and recursion
- Error conditions

### Areas for Improvement
- More edge cases in error recovery
- Stress tests for deep recursion
- Performance benchmarks
- Fuzzing for parser robustness

## Adding New Tests

When adding new features:

1. Add lexer tests for new tokens
2. Add parser tests for new syntax
3. Add code generator tests for new instructions
4. Add VM tests for new runtime behavior
5. Add an example program demonstrating the feature

## Continuous Integration

For CI, run:
```bash
cargo test --all
cargo clippy -- -D warnings
cargo fmt -- --check
```
