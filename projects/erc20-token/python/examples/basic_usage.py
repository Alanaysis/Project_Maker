#!/usr/bin/env python3
"""
ERC20 Token Basic Usage Example

This example demonstrates how to use the ERC20 token implementation
for common operations like:
- Creating a token
- Minting tokens
- Transferring tokens
- Approving and using transferFrom
- Burning tokens
- Pausing/unpausing the contract

Run this example:
    python examples/basic_usage.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.erc20 import ERC20Token


def main():
    print("=" * 60)
    print("ERC20 Token Basic Usage Example")
    print("=" * 60)
    print()

    # ============================================================
    # 1. Create Token
    # ============================================================
    print("1. Creating Token...")
    print("-" * 40)

    owner = "0xOwner"
    token = ERC20Token(
        name="My Token",
        symbol="MTK",
        decimals=18,
        owner=owner,
    )

    print(f"   Token Name: {token.name}")
    print(f"   Symbol: {token.symbol}")
    print(f"   Decimals: {token.decimals}")
    print(f"   Owner: {token.owner}")
    print(f"   Total Supply: {token.total_supply}")
    print()

    # ============================================================
    # 2. Mint Tokens
    # ============================================================
    print("2. Minting Tokens...")
    print("-" * 40)

    # Mint 1 million tokens to owner
    mint_amount = 1_000_000 * 10**18
    token.mint(owner, mint_amount)

    print(f"   Minted {mint_amount / 10**18:,.0f} tokens to {owner}")
    print(f"   Owner Balance: {token.balance_of(owner) / 10**18:,.0f} tokens")
    print(f"   Total Supply: {token.total_supply / 10**18:,.0f} tokens")
    print()

    # ============================================================
    # 3. Transfer Tokens
    # ============================================================
    print("3. Transferring Tokens...")
    print("-" * 40)

    alice = "0xAlice"
    bob = "0xBob"

    # Transfer to Alice
    token.transfer(owner, alice, 100_000 * 10**18)
    print(f"   Transferred 100,000 tokens from Owner to Alice")

    # Transfer to Bob
    token.transfer(owner, bob, 50_000 * 10**18)
    print(f"   Transferred 50,000 tokens from Owner to Bob")

    print()
    print(f"   Owner Balance: {token.balance_of(owner) / 10**18:,.0f} tokens")
    print(f"   Alice Balance: {token.balance_of(alice) / 10**18:,.0f} tokens")
    print(f"   Bob Balance: {token.balance_of(bob) / 10**18:,.0f} tokens")
    print()

    # ============================================================
    # 4. Approve and TransferFrom (DEX Pattern)
    # ============================================================
    print("4. Approve and TransferFrom (DEX Pattern)...")
    print("-" * 40)

    dex = "0xDEX"

    # Alice approves DEX to spend 10,000 tokens
    token.approve(alice, dex, 10_000 * 10**18)
    print(f"   Alice approved DEX to spend 10,000 tokens")
    print(f"   DEX Allowance: {token.allowance(alice, dex) / 10**18:,.0f} tokens")

    # DEX transfers from Alice to Bob (simulating a swap)
    token.transfer_from(dex, alice, bob, 5_000 * 10**18)
    print(f"   DEX transferred 5,000 tokens from Alice to Bob")

    print()
    print(f"   Alice Balance: {token.balance_of(alice) / 10**18:,.0f} tokens")
    print(f"   Bob Balance: {token.balance_of(bob) / 10**18:,.0f} tokens")
    print(f"   Remaining Allowance: {token.allowance(alice, dex) / 10**18:,.0f} tokens")
    print()

    # ============================================================
    # 5. Burn Tokens
    # ============================================================
    print("5. Burning Tokens...")
    print("-" * 40)

    burn_amount = 10_000 * 10**18
    token.burn(owner, burn_amount)
    print(f"   Burned {burn_amount / 10**18:,.0f} tokens from Owner")

    print()
    print(f"   Owner Balance: {token.balance_of(owner) / 10**18:,.0f} tokens")
    print(f"   Total Supply: {token.total_supply / 10**18:,.0f} tokens")
    print()

    # ============================================================
    # 6. Pause/Unpause
    # ============================================================
    print("6. Pause/Unpause Contract...")
    print("-" * 40)

    # Pause the contract
    token.pause(owner)
    print(f"   Contract Paused: {token.is_paused}")

    try:
        token.transfer(alice, bob, 1_000 * 10**18)
    except Exception as e:
        print(f"   Transfer failed (expected): {e}")

    # Unpause the contract
    token.unpause(owner)
    print(f"   Contract Paused: {token.is_paused}")

    # Now transfer works again
    token.transfer(alice, bob, 1_000 * 10**18)
    print(f"   Transfer succeeded after unpause")
    print()

    # ============================================================
    # 7. View Events
    # ============================================================
    print("7. Event Log...")
    print("-" * 40)

    events = token.event_log.get_all_events()
    print(f"   Total Events: {len(events)}")

    transfer_events = token.event_log.get_transfer_events()
    print(f"   Transfer Events: {len(transfer_events)}")

    approval_events = token.event_log.get_approval_events()
    print(f"   Approval Events: {len(approval_events)}")
    print()

    # ============================================================
    # 8. Token Summary
    # ============================================================
    print("8. Token Summary...")
    print("-" * 40)

    data = token.to_dict()
    print(f"   Name: {data['name']}")
    print(f"   Symbol: {data['symbol']}")
    print(f"   Total Supply: {data['total_supply'] / 10**18:,.0f} tokens")
    print(f"   Holders: {data['holders_count']}")
    print(f"   Paused: {data['paused']}")

    print()
    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
