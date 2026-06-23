#!/bin/bash
#
# Integration tests for simple-blockchain
# Tests the full build, unit tests, and CLI workflow.
#
# Usage: bash tests/integration_test.sh
#

set -euo pipefail

# Ensure Go is available
if ! command -v go &>/dev/null; then
    # Common Go installation paths
    for p in /home/siok/go-local/usr/lib/go-1.22/bin /home/siok/go-install/go/bin /usr/local/go/bin; do
        if [ -x "$p/go" ]; then
            export PATH="$p:$PATH"
            break
        fi
    done
fi

if ! command -v go &>/dev/null; then
    echo "ERROR: go command not found" >&2
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

PASS=0
FAIL=0
TOTAL=0

# Colors (disable if not a terminal)
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    NC='\033[0m'
else
    GREEN=''
    RED=''
    NC=''
fi

pass() {
    PASS=$((PASS + 1))
    TOTAL=$((TOTAL + 1))
    echo -e "  ${GREEN}PASS${NC}: $1"
}

fail() {
    FAIL=$((FAIL + 1))
    TOTAL=$((TOTAL + 1))
    echo -e "  ${RED}FAIL${NC}: $1"
}

run_test() {
    local name="$1"
    shift
    if "$@" >/dev/null 2>&1; then
        pass "$name"
    else
        fail "$name"
    fi
}

cleanup() {
    rm -f blockchain.dat blockchain.dat.tmp
    rm -rf wallets
    rm -f "$PROJECT_DIR/_roundtrip_check.go"
}

# ─── Section: Build ──────────────────────────────────────────────────────────

echo "=== Build ==="

run_test "go build succeeds" go build -o /dev/null .

# ─── Section: Unit Tests ─────────────────────────────────────────────────────

echo ""
echo "=== Unit Tests ==="

run_test "go test passes" go test -v -count=1 -timeout 120s ./...

# ─── Section: Module Integrity ───────────────────────────────────────────────

echo ""
echo "=== Module Integrity ==="

run_test "go vet passes" go vet ./...

# ─── Section: CLI Smoke Tests ────────────────────────────────────────────────

echo ""
echo "=== CLI Smoke Tests ==="

# Build a temporary binary for CLI testing
TMPBIN=$(mktemp)
trap "rm -f '$TMPBIN'; cleanup" EXIT

go build -o "$TMPBIN" .

run_test "help command works" "$TMPBIN" help

# createwallet
cleanup
OUTPUT=$("$TMPBIN" createwallet 2>&1)
if echo "$OUTPUT" | grep -q "Your new address"; then
    pass "createwallet produces an address"
else
    fail "createwallet produces an address"
fi

# listaddresses (after creating a wallet)
OUTPUT=$("$TMPBIN" listaddresses 2>&1)
if echo "$OUTPUT" | grep -q "Wallet addresses"; then
    pass "listaddresses shows wallets"
else
    fail "listaddresses shows wallets"
fi

# getbalance (requires a blockchain.dat to exist, created by previous commands)
OUTPUT=$("$TMPBIN" getbalance -address nonexistent 2>&1)
if echo "$OUTPUT" | grep -q "Balance of"; then
    pass "getbalance returns balance info"
else
    fail "getbalance returns balance info"
fi

cleanup

# ─── Section: Serialization Round-Trip (via targeted unit tests) ──────────────

echo ""
echo "=== Serialization Round-Trip ==="

run_test "block serialize/deserialize" go test -run TestBlockSerialization -count=1 .
run_test "transaction serialize/deserialize" go test -run TestTransactionSerialization -count=1 .
run_test "blockchain persistence" go test -run TestBlockchainPersistence -count=1 .
run_test "wallet serialize/deserialize" go test -run TestWalletSerialization -count=1 .

# ─── Section: End-to-End CLI Workflow ────────────────────────────────────────

echo ""
echo "=== End-to-End CLI Workflow ==="

cleanup

# Create two wallets
ADDR1=$("$TMPBIN" createwallet 2>&1 | grep -oP '[0-9a-f]{40}' | head -1)
ADDR2=$("$TMPBIN" createwallet 2>&1 | grep -oP '[0-9a-f]{40}' | head -1)

if [ -n "$ADDR1" ] && [ -n "$ADDR2" ]; then
    pass "created two wallets"
else
    fail "created two wallets"
fi

# Verify both addresses appear in list
ADDR_OUTPUT=$("$TMPBIN" listaddresses 2>&1)
if echo "$ADDR_OUTPUT" | grep -q "$ADDR1" && echo "$ADDR_OUTPUT" | grep -q "$ADDR2"; then
    pass "listaddresses shows both wallets"
else
    fail "listaddresses shows both wallets"
fi

# Check initial balance is zero
BAL_OUTPUT=$("$TMPBIN" getbalance -address "$ADDR1" 2>&1)
if echo "$BAL_OUTPUT" | grep -q "0.00"; then
    pass "initial balance is zero"
else
    fail "initial balance is zero (got: $BAL_OUTPUT)"
fi

cleanup

# ─── Summary ─────────────────────────────────────────────────────────────────

echo ""
echo "==============================="
echo "Results: $PASS passed, $FAIL failed, $TOTAL total"
echo "==============================="

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
