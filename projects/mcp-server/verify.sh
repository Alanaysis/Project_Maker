#!/bin/bash

# MCP Server Verification Script

echo "=== MCP Server Project Verification ==="
echo ""

# Check if Rust is installed
echo "1. Checking Rust installation..."
if command -v rustc &> /dev/null; then
    echo "   ✓ Rust is installed: $(rustc --version)"
else
    echo "   ✗ Rust is not installed"
    echo "   Please install Rust: https://rustup.rs"
    exit 1
fi

if command -v cargo &> /dev/null; then
    echo "   ✓ Cargo is installed: $(cargo --version)"
else
    echo "   ✗ Cargo is not installed"
    exit 1
fi

echo ""
echo "2. Checking project structure..."

# Check required files
required_files=(
    "Cargo.toml"
    "src/lib.rs"
    "src/main.rs"
    "src/error.rs"
    "src/jsonrpc.rs"
    "src/mcp.rs"
    "src/tool.rs"
    "README.md"
    "LEARNING_NOTES.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file (missing)"
    fi
done

echo ""
echo "3. Checking documentation..."

docs=(
    "docs/01-RESEARCH.md"
    "docs/02-REQUIREMENTS.md"
    "docs/03-DESIGN.md"
    "docs/04-PRODUCT.md"
    "docs/05-DEVELOPMENT.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "   ✓ $doc"
    else
        echo "   ✗ $doc (missing)"
    fi
done

echo ""
echo "4. Checking examples..."

examples=(
    "examples/simple_server.rs"
    "examples/calculator_tool.rs"
    "examples/client_example.rs"
    "examples/builtin_tools.rs"
)

for example in "${examples[@]}"; do
    if [ -f "$example" ]; then
        echo "   ✓ $example"
    else
        echo "   ✗ $example (missing)"
    fi
done

echo ""
echo "5. Checking tests..."

tests=(
    "tests/mcp_test.rs"
    "tests/tools_test.rs"
)

for test in "${tests[@]}"; do
    if [ -f "$test" ]; then
        echo "   ✓ $test"
    else
        echo "   ✗ $test (missing)"
    fi
done

echo ""
echo "6. Attempting to build project..."
if cargo build 2>&1; then
    echo "   ✓ Build successful"
else
    echo "   ✗ Build failed"
    exit 1
fi

echo ""
echo "7. Running tests..."
if cargo test 2>&1; then
    echo "   ✓ Tests passed"
else
    echo "   ✗ Tests failed"
    exit 1
fi

echo ""
echo "=== Verification Complete ==="
echo ""
echo "Project is ready! You can:"
echo "  - Run the server: cargo run"
echo "  - Run examples: cargo run --example simple_server"
echo "  - View documentation: cargo doc --open"
echo ""
