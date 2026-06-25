#!/bin/bash
#
# Simple Blockchain Demo Script
#
# This script demonstrates the complete workflow of the blockchain:
# 1. Create wallets
# 2. Mine blocks
# 3. Check balances
# 4. Send transactions
# 5. Explore the blockchain
#
# Usage: bash examples/demo.sh
#

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# Build the blockchain binary
echo -e "${BLUE}=== Building Blockchain ===${NC}"
go build -o blockchain .

echo ""
echo -e "${BLUE}=== Simple Blockchain Demo ===${NC}"
echo ""

# Cleanup function
cleanup() {
    rm -f blockchain.dat blockchain.dat.tmp
    rm -rf wallets
    rm -f blockchain
}

# Clean up previous data
cleanup

# Step 1: Create wallets
echo -e "${YELLOW}Step 1: Creating wallets...${NC}"
ALICE_ADDR=$(./blockchain createwallet 2>&1 | grep -oP '[0-9a-f]{40}' | head -1)
BOB_ADDR=$(./blockchain createwallet 2>&1 | grep -oP '[0-9a-f]{40}' | head -1)
MINER_ADDR=$(./blockchain createwallet 2>&1 | grep -oP '[0-9a-f]{40}' | head -1)

echo "  Alice's address:  $ALICE_ADDR"
echo "  Bob's address:    $BOB_ADDR"
echo "  Miner's address:  $MINER_ADDR"

# Step 2: List all wallets
echo ""
echo -e "${YELLOW}Step 2: Listing all wallets...${NC}"
./blockchain listaddresses

# Step 3: Check initial balances
echo ""
echo -e "${YELLOW}Step 3: Checking initial balances...${NC}"
echo "  Miner balance: $(./blockchain getbalance -address "$MINER_ADDR" 2>&1 | grep -oP '[0-9]+\.[0-9]+')"
echo "  Alice balance: $(./blockchain getbalance -address "$ALICE_ADDR" 2>&1 | grep -oP '[0-9]+\.[0-9]+')"
echo "  Bob balance:   $(./blockchain getbalance -address "$BOB_ADDR" 2>&1 | grep -oP '[0-9]+\.[0-9]+')"

# Step 4: Mine blocks
echo ""
echo -e "${YELLOW}Step 4: Mining 3 blocks...${NC}"
for i in 1 2 3; do
    echo "  Mining block $i..."
    OUTPUT=$(./blockchain mine 2>&1)
    echo "  $OUTPUT"
done

# Step 5: Check balances after mining
echo ""
echo -e "${YELLOW}Step 5: Checking balances after mining...${NC}"
echo "  Miner balance: $(./blockchain getbalance -address "$MINER_ADDR" 2>&1 | grep -oP '[0-9]+\.[0-9]+')"
echo "  Alice balance: $(./blockchain getbalance -address "$ALICE_ADDR" 2>&1 | grep -oP '[0-9]+\.[0-9]+')"
echo "  Bob balance:   $(./blockchain getbalance -address "$BOB_ADDR" 2>&1 | grep -oP '[0-9]+\.[0-9]+')"

# Step 6: Send transaction from miner to Alice
echo ""
echo -e "${YELLOW}Step 6: Sending 5.0 coins from Miner to Alice...${NC}"
OUTPUT=$(./blockchain send -from "$MINER_ADDR" -to "$ALICE_ADDR" -amount 5.0 2>&1)
echo "  $OUTPUT"

# Step 7: Send transaction from miner to Bob
echo ""
echo -e "${YELLOW}Step 7: Sending 3.0 coins from Miner to Bob...${NC}"
OUTPUT=$(./blockchain send -from "$MINER_ADDR" -to "$BOB_ADDR" -amount 3.0 2>&1)
echo "  $OUTPUT"

# Step 8: Check final balances
echo ""
echo -e "${YELLOW}Step 8: Checking final balances...${NC}"
echo "  Miner balance: $(./blockchain getbalance -address "$MINER_ADDR" 2>&1 | grep -oP '[0-9]+\.[0-9]+')"
echo "  Alice balance: $(./blockchain getbalance -address "$ALICE_ADDR" 2>&1 | grep -oP '[0-9]+\.[0-9]+')"
echo "  Bob balance:   $(./blockchain getbalance -address "$BOB_ADDR" 2>&1 | grep -oP '[0-9]+\.[0-9]+')"

# Step 9: Print the blockchain
echo ""
echo -e "${YELLOW}Step 9: Printing blockchain...${NC}"
./blockchain printchain

# Cleanup
echo ""
echo -e "${YELLOW}Cleaning up...${NC}"
cleanup

echo ""
echo -e "${GREEN}=== Demo Complete ===${NC}"
