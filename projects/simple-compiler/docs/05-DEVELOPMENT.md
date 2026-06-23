# Development - Simple Compiler

## Development Environment Setup

### Prerequisites

- Rust 1.70 or later
- Cargo (comes with Rust)

### Installation

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Verify installation
rustc --version
cargo --version
```

### Building the Project

```bash
# Build the project
cargo build

# Build in release mode (optimized)
cargo build --release

# Run tests
cargo test

# Run with output
cargo test -- --nocapture
```

## Project Structure

```
simple-compiler/
├── Cargo.toml              # Project configuration
├── README.md               # Project documentation
├── LEARNING_NOTES.md       # Learning notes
├── docs/                   # Documentation
│   ├── 01-RESEARCH.md      # Research notes
│   ├── 02-DESIGN.md        # Design decisions
│   ├── 03-IMPLEMENTATION.md # Implementation details
│   ├── 04-TESTING.md        # Testing strategy
│   └── 05-DEVELOPMENT.md    # This file
├── src/                    # Source code
│   ├── lib.rs              # Module declarations
│   ├── main.rs             # CLI entry point
│   ├── lexer.rs            # Lexer
│   ├── parser.rs           # Parser
│   ├── ast.rs              # AST definitions
│   ├── codegen.rs          # Code generator
│   └── vm.rs               # Virtual machine
├── examples/               # Example programs
│   ├── hello.sl
│   ├── arithmetic.sl
│   ├── fibonacci.sl
│   └── ...
└── tests/                  # Integration tests
```

## Development Workflow

### 1. Making Changes

```bash
# Create a feature branch
git checkout -b feature/my-feature

# Make changes to source code
# ...

# Run tests frequently
cargo test

# Check for warnings
cargo clippy
```

### 2. Testing Changes

```bash
# Run all tests
cargo test

# Run specific test
cargo test test_name

# Run with output
cargo test -- --nocapture

# Run example programs
cargo run -- run examples/hello.sl
cargo run -- run examples/fibonacci.sl
```

### 3. Debugging

```bash
# Show compilation details
cargo run -- compile examples/arithmetic.sl

# Use the REPL for interactive testing
cargo run

# Add debug output
# Use println! or dbg! macros
```

### 4. Submitting Changes

```bash
# Format code
cargo fmt

# Check for warnings
cargo clippy

# Run full test suite
cargo test

# Commit changes
git add .
git commit -m "Description of changes"
```

## Adding New Features

### Adding a New Token

1. Add the token variant to `TokenKind` in `src/lexer.rs`
2. Add lexing logic in `next_token()`
3. Add parser handling in the appropriate `parse_*()` function
4. Add tests for the new token

**Example: Adding the modulo operator `%`**

```rust
// 1. In TokenKind enum
Percent,  // %

// 2. In next_token()
'%' => Ok(Token::new(TokenKind::Percent, line, column)),

// 3. In parse_multiplication()
TokenKind::Percent => BinaryOp::Mod,

// 4. Add test
#[test]
fn test_modulo() {
    let output = run_program("print(10 % 3);");
    assert_eq!(output, vec!["1"]);
}
```

### Adding a New Statement

1. Add the statement variant to `Statement` in `src/ast.rs`
2. Add parsing logic in `src/parser.rs`
3. Add code generation in `src/codegen.rs`
4. Add execution logic in `src/vm.rs`
5. Add tests

### Adding a New Expression

1. Add the expression variant to `Expression` in `src/ast.rs`
2. Add parsing logic in `src/parser.rs`
3. Add code generation in `src/codegen.rs`
4. Add execution logic in `src/vm.rs`
5. Add tests

## Common Development Tasks

### Running Example Programs

```bash
# Run a single example
cargo run -- run examples/hello.sl

# Run all examples
for f in examples/*.sl; do
    echo "=== $f ==="
    cargo run -- run "$f"
done
```

### Debugging the Lexer

```bash
# Show tokens for a file
cargo run -- compile examples/arithmetic.sl
# (shows tokens, AST, and bytecode)
```

### Debugging the Parser

```rust
// Add debug output in parser
println!("Parsing statement: {:?}", self.peek());
```

### Debugging the VM

```rust
// Add instruction trace in VM
println!("PC: {}, Instruction: {:?}", self.pc, inst);
println!("Stack: {:?}", self.stack);
```

## Code Style

### Rust Conventions

- Use `snake_case` for functions and variables
- Use `PascalCase` for types and enums
- Use `SCREAMING_SNAKE_CASE` for constants
- Add documentation comments (`///`) for public items
- Keep functions focused and small

### Formatting

```bash
# Format code
cargo fmt

# Check formatting
cargo fmt -- --check
```

### Linting

```bash
# Run clippy
cargo clippy

# Run clippy with all warnings
cargo clippy -- -W clippy::all
```

## Troubleshooting

### Common Issues

**"cannot find type `TokenKind`"**
- Make sure you've imported the type: `use crate::lexer::TokenKind;`

**"expected `;`, found `}`"**
- Check that all statements end with semicolons

**"stack overflow"**
- Check for infinite recursion in parser or VM
- Add recursion depth limits if needed

**"undefined variable"**
- Make sure variables are declared before use
- Check variable scoping rules

### Getting Help

1. Check the error message carefully
2. Look at the test suite for examples
3. Use `cargo run -- compile` to see compilation details
4. Add `dbg!()` statements for debugging
5. Check the documentation in `docs/`

## Performance Profiling

### Measuring Performance

```bash
# Build optimized
cargo build --release

# Run with timing
time ./target/release/sc run examples/fibonacci.sl

# Use cargo bench (if benchmarks exist)
cargo bench
```

### Common Bottlenecks

- Deep recursion (fibonacci, factorial)
- Many string concatenations
- Large loops with many iterations

### Optimization Ideas

- Tail call optimization
- Constant folding
- String interning
- Register-based VM

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## Resources

- [Rust Book](https://doc.rust-lang.org/book/)
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/)
- [Crafting Interpreters](https://craftinginterpreters.com/)
- [LLVM Tutorial](https://llvm.org/docs/tutorial/)
