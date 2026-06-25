"""
Event system for ERC20 token.

Events are used to log important state changes on the blockchain.
In Solidity, events are indexed and can be filtered by frontend applications.
This Python implementation provides a similar mechanism for testing and simulation.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class TransferEvent:
    """
    Emitted when tokens are transferred.

    Equivalent to Solidity's Transfer event:
        event Transfer(address indexed from, address indexed to, uint256 value)

    Attributes:
        from_address: The address sending tokens (0x0 for mint)
        to_address: The address receiving tokens (0x0 for burn)
        value: The amount of tokens transferred
        timestamp: When the transfer occurred
        block_number: Simulated block number
    """

    from_address: str
    to_address: str
    value: int
    timestamp: datetime
    block_number: int

    def __str__(self) -> str:
        return (
            f"Transfer(from={self.from_address}, to={self.to_address}, "
            f"value={self.value}, block={self.block_number})"
        )


@dataclass(frozen=True)
class ApprovalEvent:
    """
    Emitted when an approval is set.

    Equivalent to Solidity's Approval event:
        event Approval(address indexed owner, address indexed spender, uint256 value)

    Attributes:
        owner: The address that owns the tokens
        spender: The address approved to spend
        value: The approved amount
        timestamp: When the approval occurred
        block_number: Simulated block number
    """

    owner: str
    spender: str
    value: int
    timestamp: datetime
    block_number: int

    def __str__(self) -> str:
        return (
            f"Approval(owner={self.owner}, spender={self.spender}, "
            f"value={self.value}, block={self.block_number})"
        )


class EventLog:
    """
    Event log for collecting and querying ERC20 events.

    This class simulates the event logging mechanism of Ethereum,
    allowing us to track all state changes for testing and debugging.
    """

    def __init__(self):
        """Initialize an empty event log."""
        self._events: list = []
        self._block_number: int = 0

    def advance_block(self) -> int:
        """
        Advance the simulated block number.

        Returns:
            The new block number
        """
        self._block_number += 1
        return self._block_number

    @property
    def current_block(self) -> int:
        """Get the current block number."""
        return self._block_number

    def emit_transfer(self, from_address: str, to_address: str, value: int) -> TransferEvent:
        """
        Emit a Transfer event.

        Args:
            from_address: Sender address (0x0 for mint)
            to_address: Receiver address (0x0 for burn)
            value: Amount transferred

        Returns:
            The created TransferEvent
        """
        event = TransferEvent(
            from_address=from_address,
            to_address=to_address,
            value=value,
            timestamp=datetime.now(),
            block_number=self._block_number,
        )
        self._events.append(event)
        return event

    def emit_approval(self, owner: str, spender: str, value: int) -> ApprovalEvent:
        """
        Emit an Approval event.

        Args:
            owner: Token owner address
            spender: Approved spender address
            value: Approved amount

        Returns:
            The created ApprovalEvent
        """
        event = ApprovalEvent(
            owner=owner,
            spender=spender,
            value=value,
            timestamp=datetime.now(),
            block_number=self._block_number,
        )
        self._events.append(event)
        return event

    def get_transfer_events(
        self,
        from_address: Optional[str] = None,
        to_address: Optional[str] = None,
    ) -> list[TransferEvent]:
        """
        Query Transfer events with optional filters.

        Args:
            from_address: Filter by sender (None = any)
            to_address: Filter by receiver (None = any)

        Returns:
            List of matching TransferEvents
        """
        results = []
        for event in self._events:
            if isinstance(event, TransferEvent):
                if from_address is not None and event.from_address != from_address:
                    continue
                if to_address is not None and event.to_address != to_address:
                    continue
                results.append(event)
        return results

    def get_approval_events(
        self,
        owner: Optional[str] = None,
        spender: Optional[str] = None,
    ) -> list[ApprovalEvent]:
        """
        Query Approval events with optional filters.

        Args:
            owner: Filter by owner (None = any)
            spender: Filter by spender (None = any)

        Returns:
            List of matching ApprovalEvents
        """
        results = []
        for event in self._events:
            if isinstance(event, ApprovalEvent):
                if owner is not None and event.owner != owner:
                    continue
                if spender is not None and event.spender != spender:
                    continue
                results.append(event)
        return results

    def get_all_events(self) -> list:
        """
        Get all events in chronological order.

        Returns:
            List of all events
        """
        return list(self._events)

    def clear(self) -> None:
        """Clear all events."""
        self._events.clear()
        self._block_number = 0

    def __len__(self) -> int:
        """Get the total number of events."""
        return len(self._events)
