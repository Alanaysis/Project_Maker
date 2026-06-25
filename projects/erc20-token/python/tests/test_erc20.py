"""
Comprehensive tests for ERC20 token implementation.

This test suite covers:
1. ERC20 standard functions (totalSupply, balanceOf, transfer, approve, transferFrom, allowance)
2. Events (Transfer, Approval)
3. Extensions (Mint, Burn, Pause)
4. Security (overflow protection, access control)
5. Edge cases and error handling
"""

import pytest
from src.erc20 import ERC20Token
from src.exceptions import (
    BurnExceedsBalanceError,
    ContractPausedError,
    InsufficientAllowanceError,
    InsufficientBalanceError,
    MintOverflowError,
    UnauthorizedError,
    ZeroAddressError,
)


# ============================================================
#                      FIXTURES
# ============================================================


@pytest.fixture
def owner():
    """Owner address fixture."""
    return "0xOwner"


@pytest.fixture
def alice():
    """Alice address fixture."""
    return "0xAlice"


@pytest.fixture
def bob():
    """Bob address fixture."""
    return "0xBob"


@pytest.fixture
def charlie():
    """Charlie address fixture."""
    return "0xCharlie"


@pytest.fixture
def token(owner):
    """Create a fresh token for each test."""
    return ERC20Token(
        name="Test Token",
        symbol="TST",
        decimals=18,
        owner=owner,
    )


@pytest.fixture
def token_with_supply(owner):
    """Create a token with initial supply."""
    t = ERC20Token(
        name="Test Token",
        symbol="TST",
        decimals=18,
        owner=owner,
    )
    t.mint(owner, 1_000_000 * 10**18)
    return t


@pytest.fixture
def capped_token(owner):
    """Create a token with max supply cap."""
    return ERC20Token(
        name="Capped Token",
        symbol="CAP",
        decimals=18,
        owner=owner,
        max_supply=10_000_000 * 10**18,
    )


# ============================================================
#                      TEST: Basic Properties
# ============================================================


class TestTokenProperties:
    """Test basic token properties."""

    def test_token_name(self, token):
        assert token.name == "Test Token"

    def test_token_symbol(self, token):
        assert token.symbol == "TST"

    def test_token_decimals(self, token):
        assert token.decimals == 18

    def test_token_owner(self, token, owner):
        assert token.owner == owner

    def test_initial_total_supply(self, token):
        assert token.total_supply == 0

    def test_initial_balance(self, token, owner):
        assert token.balance_of(owner) == 0


# ============================================================
#                      TEST: Mint Function
# ============================================================


class TestMint:
    """Test mint (铸造) functionality."""

    def test_mint_basic(self, token, owner):
        """Test basic minting."""
        amount = 1000 * 10**18
        token.mint(owner, amount)

        assert token.total_supply == amount
        assert token.balance_of(owner) == amount

    def test_mint_to_different_address(self, token, owner, alice):
        """Test minting to a different address."""
        amount = 500 * 10**18
        token.mint(alice, amount)

        assert token.total_supply == amount
        assert token.balance_of(alice) == amount
        assert token.balance_of(owner) == 0

    def test_mint_multiple_times(self, token, owner):
        """Test minting multiple times."""
        token.mint(owner, 1000 * 10**18)
        token.mint(owner, 2000 * 10**18)

        assert token.total_supply == 3000 * 10**18
        assert token.balance_of(owner) == 3000 * 10**18

    def test_mint_emits_transfer_event(self, token, owner):
        """Test that minting emits Transfer event from 0x0."""
        token.mint(owner, 1000 * 10**18)

        events = token.event_log.get_transfer_events(from_address="0x0")
        assert len(events) == 1
        assert events[0].from_address == "0x0"
        assert events[0].to_address == owner
        assert events[0].value == 1000 * 10**18

    def test_mint_to_zero_address_fails(self, token):
        """Test that minting to zero address fails."""
        with pytest.raises(ZeroAddressError):
            token.mint("0x0", 1000)

    def test_mint_exceeds_max_supply_fails(self, capped_token, owner):
        """Test that minting beyond max supply fails."""
        max_supply = 10_000_000 * 10**18

        # Mint up to max should work
        capped_token.mint(owner, max_supply)
        assert capped_token.total_supply == max_supply

        # Minting more should fail
        with pytest.raises(MintOverflowError):
            capped_token.mint(owner, 1)


# ============================================================
#                      TEST: Transfer Function
# ============================================================


class TestTransfer:
    """Test transfer functionality."""

    def test_transfer_basic(self, token_with_supply, owner, alice):
        """Test basic transfer."""
        amount = 100 * 10**18
        token_with_supply.transfer(owner, alice, amount)

        assert token_with_supply.balance_of(owner) == 1_000_000 * 10**18 - amount
        assert token_with_supply.balance_of(alice) == amount

    def test_transfer_full_balance(self, token_with_supply, owner, alice):
        """Test transferring full balance."""
        balance = token_with_supply.balance_of(owner)
        token_with_supply.transfer(owner, alice, balance)

        assert token_with_supply.balance_of(owner) == 0
        assert token_with_supply.balance_of(alice) == balance

    def test_transfer_zero_amount(self, token_with_supply, owner, alice):
        """Test transferring zero amount."""
        token_with_supply.transfer(owner, alice, 0)

        assert token_with_supply.balance_of(owner) == 1_000_000 * 10**18
        assert token_with_supply.balance_of(alice) == 0

    def test_transfer_emits_event(self, token_with_supply, owner, alice):
        """Test that transfer emits Transfer event."""
        amount = 100 * 10**18
        token_with_supply.transfer(owner, alice, amount)

        events = token_with_supply.event_log.get_transfer_events(
            from_address=owner, to_address=alice
        )
        assert len(events) == 1
        assert events[0].value == amount

    def test_transfer_to_zero_address_fails(self, token_with_supply, owner):
        """Test that transfer to zero address fails."""
        with pytest.raises(ZeroAddressError):
            token_with_supply.transfer(owner, "0x0", 100)

    def test_transfer_insufficient_balance_fails(self, token_with_supply, owner, alice):
        """Test that transfer with insufficient balance fails."""
        balance = token_with_supply.balance_of(owner)
        with pytest.raises(InsufficientBalanceError):
            token_with_supply.transfer(owner, alice, balance + 1)

    def test_transfer_chain(self, token_with_supply, owner, alice, bob, charlie):
        """Test chained transfers."""
        # Owner -> Alice -> Bob -> Charlie
        token_with_supply.transfer(owner, alice, 1000 * 10**18)
        token_with_supply.transfer(alice, bob, 500 * 10**18)
        token_with_supply.transfer(bob, charlie, 200 * 10**18)

        assert token_with_supply.balance_of(alice) == 500 * 10**18
        assert token_with_supply.balance_of(bob) == 300 * 10**18
        assert token_with_supply.balance_of(charlie) == 200 * 10**18

    def test_transfer_total_supply_unchanged(self, token_with_supply, owner, alice):
        """Test that total supply doesn't change on transfer."""
        initial_supply = token_with_supply.total_supply
        token_with_supply.transfer(owner, alice, 100 * 10**18)
        assert token_with_supply.total_supply == initial_supply


# ============================================================
#                      TEST: Approve & Allowance
# ============================================================


class TestApproveAllowance:
    """Test approve and allowance functionality."""

    def test_approve_basic(self, token, owner, alice):
        """Test basic approval."""
        token.approve(owner, alice, 1000 * 10**18)

        assert token.allowance(owner, alice) == 1000 * 10**18

    def test_approve_overwrites_previous(self, token, owner, alice):
        """Test that approve overwrites previous allowance."""
        token.approve(owner, alice, 1000 * 10**18)
        token.approve(owner, alice, 2000 * 10**18)

        assert token.allowance(owner, alice) == 2000 * 10**18

    def test_approve_zero(self, token, owner, alice):
        """Test approving zero amount."""
        token.approve(owner, alice, 1000 * 10**18)
        token.approve(owner, alice, 0)

        assert token.allowance(owner, alice) == 0

    def test_approve_emits_event(self, token, owner, alice):
        """Test that approve emits Approval event."""
        token.approve(owner, alice, 1000 * 10**18)

        events = token.event_log.get_approval_events(owner=owner, spender=alice)
        assert len(events) == 1
        assert events[0].value == 1000 * 10**18

    def test_approve_to_zero_address_fails(self, token, owner):
        """Test that approving zero address fails."""
        with pytest.raises(ZeroAddressError):
            token.approve(owner, "0x0", 1000)

    def test_allowance_default_zero(self, token, owner, alice):
        """Test that default allowance is zero."""
        assert token.allowance(owner, alice) == 0

    def test_allowance_multiple_spenders(self, token, owner, alice, bob):
        """Test allowances for multiple spenders."""
        token.approve(owner, alice, 1000 * 10**18)
        token.approve(owner, bob, 2000 * 10**18)

        assert token.allowance(owner, alice) == 1000 * 10**18
        assert token.allowance(owner, bob) == 2000 * 10**18


# ============================================================
#                      TEST: TransferFrom
# ============================================================


class TestTransferFrom:
    """Test transferFrom functionality."""

    def test_transfer_from_basic(self, token_with_supply, owner, alice, bob):
        """Test basic transferFrom."""
        amount = 100 * 10**18

        # Owner approves Alice
        token_with_supply.approve(owner, alice, amount)

        # Alice transfers from Owner to Bob
        token_with_supply.transfer_from(alice, owner, bob, amount)

        assert token_with_supply.balance_of(owner) == 1_000_000 * 10**18 - amount
        assert token_with_supply.balance_of(bob) == amount
        assert token_with_supply.allowance(owner, alice) == 0

    def test_transfer_from_partial(self, token_with_supply, owner, alice, bob):
        """Test partial transferFrom."""
        # Owner approves Alice for 1000
        token_with_supply.approve(owner, alice, 1000 * 10**18)

        # Alice transfers 500
        token_with_supply.transfer_from(alice, owner, bob, 500 * 10**18)

        assert token_with_supply.allowance(owner, alice) == 500 * 10**18

    def test_transfer_from_self(self, token_with_supply, owner, alice):
        """Test transferFrom when spender is the owner (no allowance needed)."""
        amount = 100 * 10**18

        # Owner transfers from themselves (no approval needed)
        token_with_supply.transfer_from(owner, owner, alice, amount)

        assert token_with_supply.balance_of(alice) == amount

    def test_transfer_from_insufficient_allowance_fails(
        self, token_with_supply, owner, alice, bob
    ):
        """Test that transferFrom fails with insufficient allowance."""
        token_with_supply.approve(owner, alice, 100 * 10**18)

        with pytest.raises(InsufficientAllowanceError):
            token_with_supply.transfer_from(alice, owner, bob, 101 * 10**18)

    def test_transfer_from_insufficient_balance_fails(
        self, token_with_supply, owner, alice, bob
    ):
        """Test that transferFrom fails with insufficient balance."""
        # Approve more than balance
        token_with_supply.approve(owner, alice, 2_000_000 * 10**18)

        with pytest.raises(InsufficientBalanceError):
            token_with_supply.transfer_from(
                alice, owner, bob, 1_000_001 * 10**18
            )

    def test_transfer_from_to_zero_address_fails(self, token_with_supply, owner, alice):
        """Test that transferFrom to zero address fails."""
        token_with_supply.approve(owner, alice, 100 * 10**18)

        with pytest.raises(ZeroAddressError):
            token_with_supply.transfer_from(alice, owner, "0x0", 100 * 10**18)


# ============================================================
#                      TEST: Increase/Decrease Allowance
# ============================================================


class TestAllowanceManagement:
    """Test increase_allowance and decrease_allowance."""

    def test_increase_allowance(self, token, owner, alice):
        """Test increasing allowance."""
        token.approve(owner, alice, 1000 * 10**18)
        token.increase_allowance(owner, alice, 500 * 10**18)

        assert token.allowance(owner, alice) == 1500 * 10**18

    def test_increase_allowance_from_zero(self, token, owner, alice):
        """Test increasing allowance from zero."""
        token.increase_allowance(owner, alice, 500 * 10**18)

        assert token.allowance(owner, alice) == 500 * 10**18

    def test_decrease_allowance(self, token, owner, alice):
        """Test decreasing allowance."""
        token.approve(owner, alice, 1000 * 10**18)
        token.decrease_allowance(owner, alice, 300 * 10**18)

        assert token.allowance(owner, alice) == 700 * 10**18

    def test_decrease_allowance_to_zero(self, token, owner, alice):
        """Test decreasing allowance to zero."""
        token.approve(owner, alice, 1000 * 10**18)
        token.decrease_allowance(owner, alice, 1000 * 10**18)

        assert token.allowance(owner, alice) == 0

    def test_decrease_allowance_below_zero_fails(self, token, owner, alice):
        """Test that decreasing allowance below zero fails."""
        token.approve(owner, alice, 100 * 10**18)

        with pytest.raises(InsufficientAllowanceError):
            token.decrease_allowance(owner, alice, 101 * 10**18)


# ============================================================
#                      TEST: Burn Function
# ============================================================


class TestBurn:
    """Test burn (销毁) functionality."""

    def test_burn_basic(self, token_with_supply, owner):
        """Test basic burning."""
        initial_supply = token_with_supply.total_supply
        initial_balance = token_with_supply.balance_of(owner)

        burn_amount = 100 * 10**18
        token_with_supply.burn(owner, burn_amount)

        assert token_with_supply.total_supply == initial_supply - burn_amount
        assert token_with_supply.balance_of(owner) == initial_balance - burn_amount

    def test_burn_full_balance(self, token_with_supply, owner):
        """Test burning full balance."""
        balance = token_with_supply.balance_of(owner)
        token_with_supply.burn(owner, balance)

        assert token_with_supply.total_supply == 0
        assert token_with_supply.balance_of(owner) == 0

    def test_burn_emits_event(self, token_with_supply, owner):
        """Test that burning emits Transfer event to 0x0."""
        burn_amount = 100 * 10**18
        token_with_supply.burn(owner, burn_amount)

        events = token_with_supply.event_log.get_transfer_events(to_address="0x0")
        assert len(events) == 1
        assert events[0].from_address == owner
        assert events[0].to_address == "0x0"
        assert events[0].value == burn_amount

    def test_burn_exceeds_balance_fails(self, token_with_supply, owner):
        """Test that burning more than balance fails."""
        balance = token_with_supply.balance_of(owner)

        with pytest.raises(BurnExceedsBalanceError):
            token_with_supply.burn(owner, balance + 1)


# ============================================================
#                      TEST: Pause Function
# ============================================================


class TestPause:
    """Test pause (暂停) functionality."""

    def test_pause(self, token, owner):
        """Test pausing the contract."""
        token.pause(owner)

        assert token.is_paused is True

    def test_unpause(self, token, owner):
        """Test unpausing the contract."""
        token.pause(owner)
        token.unpause(owner)

        assert token.is_paused is False

    def test_transfer_when_paused_fails(self, token_with_supply, owner, alice):
        """Test that transfer fails when paused."""
        token_with_supply.pause(owner)

        with pytest.raises(ContractPausedError):
            token_with_supply.transfer(owner, alice, 100 * 10**18)

    def test_transfer_from_when_paused_fails(self, token_with_supply, owner, alice, bob):
        """Test that transferFrom fails when paused."""
        token_with_supply.approve(owner, alice, 100 * 10**18)
        token_with_supply.pause(owner)

        with pytest.raises(ContractPausedError):
            token_with_supply.transfer_from(alice, owner, bob, 100 * 10**18)

    def test_mint_when_paused_works(self, token, owner):
        """Test that minting still works when paused."""
        token.pause(owner)
        token.mint(owner, 1000 * 10**18)

        assert token.balance_of(owner) == 1000 * 10**18

    def test_burn_when_paused_works(self, token_with_supply, owner):
        """Test that burning still works when paused."""
        token_with_supply.pause(owner)
        token_with_supply.burn(owner, 100 * 10**18)

        assert token_with_supply.balance_of(owner) == 999_900 * 10**18

    def test_pause_by_non_owner_fails(self, token, alice):
        """Test that only owner can pause."""
        with pytest.raises(UnauthorizedError):
            token.pause(alice)

    def test_unpause_by_non_owner_fails(self, token, owner, alice):
        """Test that only owner can unpause."""
        token.pause(owner)

        with pytest.raises(UnauthorizedError):
            token.unpause(alice)


# ============================================================
#                      TEST: Security
# ============================================================


class TestSecurity:
    """Test security features."""

    def test_overflow_protection_on_mint(self, capped_token, owner):
        """Test that minting respects max supply."""
        max_supply = 10_000_000 * 10**18
        capped_token.mint(owner, max_supply)

        with pytest.raises(MintOverflowError):
            capped_token.mint(owner, 1)

    def test_underflow_protection_on_transfer(self, token_with_supply, owner, alice):
        """Test that transfer prevents underflow."""
        balance = token_with_supply.balance_of(owner)

        with pytest.raises(InsufficientBalanceError):
            token_with_supply.transfer(owner, alice, balance + 1)

    def test_underflow_protection_on_burn(self, token_with_supply, owner):
        """Test that burn prevents underflow."""
        balance = token_with_supply.balance_of(owner)

        with pytest.raises(BurnExceedsBalanceError):
            token_with_supply.burn(owner, balance + 1)

    def test_underflow_protection_on_allowance(self, token, owner, alice):
        """Test that allowance decrease prevents underflow."""
        token.approve(owner, alice, 100 * 10**18)

        with pytest.raises(InsufficientAllowanceError):
            token.decrease_allowance(owner, alice, 101 * 10**18)

    def test_zero_address_checks(self, token, owner):
        """Test that zero address is rejected in all relevant functions."""
        with pytest.raises(ZeroAddressError):
            token.mint("0x0", 100)

        with pytest.raises(ZeroAddressError):
            token.transfer(owner, "0x0", 100)

        with pytest.raises(ZeroAddressError):
            token.approve(owner, "0x0", 100)

    def test_access_control_on_pause(self, token, alice):
        """Test that only owner can pause/unpause."""
        with pytest.raises(UnauthorizedError):
            token.pause(alice)

        with pytest.raises(UnauthorizedError):
            token.unpause(alice)


# ============================================================
#                      TEST: Events
# ============================================================


class TestEvents:
    """Test event logging."""

    def test_transfer_event_count(self, token_with_supply, owner, alice, bob):
        """Test that correct number of Transfer events are emitted."""
        token_with_supply.transfer(owner, alice, 100 * 10**18)
        token_with_supply.transfer(alice, bob, 50 * 10**18)

        # 1 mint event (from fixture) + 2 transfer events = 3 total
        events = token_with_supply.event_log.get_transfer_events()
        assert len(events) == 3

        # Filter to only non-mint transfers
        non_mint_events = token_with_supply.event_log.get_transfer_events(
            from_address=owner
        )
        assert len(non_mint_events) == 1

    def test_approval_event_count(self, token, owner, alice, bob):
        """Test that correct number of Approval events are emitted."""
        token.approve(owner, alice, 1000 * 10**18)
        token.approve(owner, bob, 2000 * 10**18)

        events = token.event_log.get_approval_events()
        assert len(events) == 2

    def test_mint_emits_transfer_from_zero(self, token, owner):
        """Test that mint emits Transfer from 0x0."""
        token.mint(owner, 1000 * 10**18)

        events = token.event_log.get_transfer_events(from_address="0x0")
        assert len(events) == 1
        assert events[0].to_address == owner

    def test_burn_emits_transfer_to_zero(self, token_with_supply, owner):
        """Test that burn emits Transfer to 0x0."""
        token_with_supply.burn(owner, 100 * 10**18)

        events = token_with_supply.event_log.get_transfer_events(to_address="0x0")
        assert len(events) == 1
        assert events[0].from_address == owner

    def test_event_block_numbers(self, token, owner, alice):
        """Test that events have sequential block numbers."""
        token.mint(owner, 1000 * 10**18)
        token.transfer(owner, alice, 100 * 10**18)
        token.approve(owner, alice, 50 * 10**18)

        events = token.event_log.get_all_events()
        assert len(events) == 3
        assert events[0].block_number < events[1].block_number < events[2].block_number


# ============================================================
#                      TEST: Utility Functions
# ============================================================


class TestUtility:
    """Test utility functions."""

    def test_get_all_holders(self, token_with_supply, owner, alice, bob):
        """Test getting all token holders."""
        token_with_supply.transfer(owner, alice, 100 * 10**18)
        token_with_supply.transfer(owner, bob, 200 * 10**18)

        holders = token_with_supply.get_all_holders()
        assert owner in holders
        assert alice in holders
        assert bob in holders

    def test_to_dict(self, token, owner):
        """Test dictionary representation."""
        token.mint(owner, 1000 * 10**18)

        data = token.to_dict()
        assert data["name"] == "Test Token"
        assert data["symbol"] == "TST"
        assert data["decimals"] == 18
        assert data["owner"] == owner
        assert data["total_supply"] == 1000 * 10**18
        assert data["paused"] is False
        assert data["holders_count"] == 1


# ============================================================
#                      TEST: Integration
# ============================================================


class TestIntegration:
    """Integration tests combining multiple operations."""

    def test_token_issuance_workflow(self, token, owner, alice, bob):
        """Test complete token issuance workflow."""
        # 1. Mint initial supply to owner
        token.mint(owner, 1_000_000 * 10**18)
        assert token.total_supply == 1_000_000 * 10**18

        # 2. Owner distributes to team
        token.transfer(owner, alice, 100_000 * 10**18)
        token.transfer(owner, bob, 50_000 * 10**18)

        # 3. Check balances
        assert token.balance_of(owner) == 850_000 * 10**18
        assert token.balance_of(alice) == 100_000 * 10**18
        assert token.balance_of(bob) == 50_000 * 10**18

    def test_allowance_workflow(self, token_with_supply, owner, alice, bob):
        """Test complete allowance workflow (DEX pattern)."""
        # 1. Owner approves Alice (DEX) to spend
        token_with_supply.approve(owner, alice, 1000 * 10**18)

        # 2. Alice transfers from Owner to Bob (swap)
        token_with_supply.transfer_from(alice, owner, bob, 500 * 10**18)

        # 3. Check remaining allowance
        assert token_with_supply.allowance(owner, alice) == 500 * 10**18

        # 4. Check balances
        assert token_with_supply.balance_of(bob) == 500 * 10**18

    def test_deflationary_token(self, token, owner, alice):
        """Test deflationary token with burn on transfer."""
        # Mint tokens
        token.mint(owner, 1_000_000 * 10**18)

        # Transfer and burn 1%
        transfer_amount = 1000 * 10**18
        burn_amount = transfer_amount // 100  # 1%

        token.transfer(owner, alice, transfer_amount)
        token.burn(alice, burn_amount)

        # Check results
        assert token.balance_of(alice) == transfer_amount - burn_amount
        assert token.total_supply == 1_000_000 * 10**18 - burn_amount

    def test_emergency_pause_scenario(self, token_with_supply, owner, alice):
        """Test emergency pause scenario."""
        # Normal operation
        token_with_supply.transfer(owner, alice, 100 * 10**18)
        assert token_with_supply.balance_of(alice) == 100 * 10**18

        # Emergency pause
        token_with_supply.pause(owner)
        assert token_with_supply.is_paused is True

        # Transfers blocked
        with pytest.raises(ContractPausedError):
            token_with_supply.transfer(alice, owner, 50 * 10**18)

        # But mint/burn still work
        token_with_supply.mint(owner, 1000 * 10**18)
        token_with_supply.burn(owner, 500 * 10**18)

        # Resume operations
        token_with_supply.unpause(owner)
        token_with_supply.transfer(alice, owner, 50 * 10**18)
        assert token_with_supply.balance_of(alice) == 50 * 10**18


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
