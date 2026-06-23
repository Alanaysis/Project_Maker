#!/bin/bash
# run_tests.sh - Run sandbox tests with proper setup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/build"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== Sandbox Test Runner ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Warning: Tests require root privileges for seccomp.${NC}"
    echo "Re-running with sudo..."
    exec sudo "$0" "$@"
fi

# Build if needed
if [ ! -f "$BUILD_DIR/test_sandbox" ]; then
    echo "Building tests..."
    cd "$PROJECT_DIR"
    make test
    exit $?
fi

# Run tests
echo "Running test suite..."
echo "===================="
"$BUILD_DIR/test_sandbox"
exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${RED}Some tests failed!${NC}"
fi

exit $exit_code
