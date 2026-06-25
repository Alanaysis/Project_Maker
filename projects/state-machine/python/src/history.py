"""
History management for state transitions.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional, Sequence

from .event import Event
from .state import State


@dataclass
class HistoryEntry:
    """
    Represents a single state transition in the history.

    Attributes:
        timestamp: When the transition occurred
        from_state: The source state
        to_state: The target state
        event: The triggering event
        success: Whether the transition was successful
        duration: Time spent in the previous state (in seconds)
        context: Optional context data
        error: Optional error if transition failed
    """

    timestamp: datetime
    from_state: State
    to_state: State
    event: Event
    success: bool
    duration: Optional[float] = None
    context: Optional[Dict[str, Any]] = None
    error: Optional[Exception] = None

    def __repr__(self) -> str:
        status = "OK" if self.success else "FAILED"
        return (
            f"HistoryEntry({self.timestamp.isoformat()}, "
            f"{self.from_state} -> {self.to_state} on {self.event}, {status})"
        )

    def __str__(self) -> str:
        status = "✓" if self.success else "✗"
        return (
            f"[{self.timestamp.strftime('%H:%M:%S')}] "
            f"{self.from_state} -> {self.to_state} on {self.event} {status}"
        )


class HistoryState:
    """
    Tracks the last active sub-state for hierarchical states.

    This allows hierarchical states to remember which sub-state
    was active when they were last exited.

    Example:
        >>> history = HistoryState()
        >>> history.save("Active", "Processing")
        >>> history.get("Active")
        'Processing'
    """

    def __init__(self) -> None:
        """Initialize the history state tracker."""
        self._states: Dict[str, str] = {}

    def save(self, parent_state: str, sub_state: str) -> None:
        """
        Save the last active sub-state for a parent state.

        Args:
            parent_state: The parent state name
            sub_state: The last active sub-state name
        """
        self._states[parent_state] = sub_state

    def get(self, parent_state: str) -> Optional[str]:
        """
        Get the last active sub-state for a parent state.

        Args:
            parent_state: The parent state name

        Returns:
            The last active sub-state name, or None
        """
        return self._states.get(parent_state)

    def clear(self, parent_state: Optional[str] = None) -> None:
        """
        Clear history for a specific or all parent states.

        Args:
            parent_state: Optional specific parent state to clear
        """
        if parent_state:
            self._states.pop(parent_state, None)
        else:
            self._states.clear()

    def __repr__(self) -> str:
        return f"HistoryState({self._states})"


class HistoryManager:
    """
    Manages the history of state transitions.

    Provides methods to query and analyze transition history.

    Example:
        >>> manager = HistoryManager(max_entries=100)
        >>> entry = HistoryEntry(
        ...     timestamp=datetime.now(),
        ...     from_state=State("Off"),
        ...     to_state=State("On"),
        ...     event=Event("TurnOn"),
        ...     success=True
        ... )
        >>> manager.push(entry)
        >>> manager.last()
        HistoryEntry(...)
    """

    def __init__(self, max_entries: int = 1000) -> None:
        """
        Initialize the history manager.

        Args:
            max_entries: Maximum number of entries to keep
        """
        self._max_entries = max_entries
        self._entries: Deque[HistoryEntry] = deque(maxlen=max_entries)
        self._last_state_change: Optional[datetime] = None

    @property
    def max_entries(self) -> int:
        """Get the maximum number of entries."""
        return self._max_entries

    def push(self, entry: HistoryEntry) -> None:
        """
        Add an entry to the history.

        Args:
            entry: The history entry to add
        """
        # Calculate duration if we have a previous entry
        if self._entries and self._last_state_change:
            last_entry = self._entries[-1]
            if last_entry.success:
                duration = (entry.timestamp - self._last_state_change).total_seconds()
                last_entry.duration = duration

        self._entries.append(entry)
        if entry.success:
            self._last_state_change = entry.timestamp

    def last(self) -> Optional[HistoryEntry]:
        """
        Get the most recent entry.

        Returns:
            The most recent entry, or None if empty
        """
        if self._entries:
            return self._entries[-1]
        return None

    def first(self) -> Optional[HistoryEntry]:
        """
        Get the oldest entry.

        Returns:
            The oldest entry, or None if empty
        """
        if self._entries:
            return self._entries[0]
        return None

    def len(self) -> int:
        """
        Get the number of entries.

        Returns:
            Number of entries in history
        """
        return len(self._entries)

    def is_empty(self) -> bool:
        """
        Check if history is empty.

        Returns:
            True if no entries exist
        """
        return len(self._entries) == 0

    def entries(self) -> List[HistoryEntry]:
        """
        Get all entries in chronological order.

        Returns:
            List of history entries
        """
        return list(self._entries)

    def entries_reversed(self) -> List[HistoryEntry]:
        """
        Get all entries in reverse chronological order.

        Returns:
            List of history entries, newest first
        """
        return list(reversed(self._entries))

    def entries_for_state(self, state: State) -> List[HistoryEntry]:
        """
        Get entries involving a specific state.

        Args:
            state: The state to filter by

        Returns:
            List of entries where the state was involved
        """
        return [
            entry for entry in self._entries
            if entry.from_state == state or entry.to_state == state
        ]

    def entries_for_event(self, event: Event) -> List[HistoryEntry]:
        """
        Get entries triggered by a specific event.

        Args:
            event: The event to filter by

        Returns:
            List of entries triggered by the event
        """
        return [
            entry for entry in self._entries
            if entry.event == event
        ]

    def successful_entries(self) -> List[HistoryEntry]:
        """
        Get only successful entries.

        Returns:
            List of successful entries
        """
        return [entry for entry in self._entries if entry.success]

    def failed_entries(self) -> List[HistoryEntry]:
        """
        Get only failed entries.

        Returns:
            List of failed entries
        """
        return [entry for entry in self._entries if not entry.success]

    def clear(self) -> None:
        """Clear all history entries."""
        self._entries.clear()
        self._last_state_change = None

    def format_all(self) -> str:
        """
        Format all entries as a string.

        Returns:
            Formatted string of all entries
        """
        if not self._entries:
            return "No history entries"
        return "\n".join(str(entry) for entry in self._entries)

    def format_summary(self) -> str:
        """
        Format a summary of the history.

        Returns:
            Summary string with statistics
        """
        total = len(self._entries)
        successful = len(self.successful_entries())
        failed = len(self.failed_entries())

        lines = [
            f"History Summary:",
            f"  Total transitions: {total}",
            f"  Successful: {successful}",
            f"  Failed: {failed}",
        ]

        if self._entries:
            first = self.first()
            last = self.last()
            if first and last:
                lines.append(f"  First: {first.timestamp.isoformat()}")
                lines.append(f"  Last: {last.timestamp.isoformat()}")

        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._entries)

    def __bool__(self) -> bool:
        """Always return True - the manager exists even if empty."""
        return True

    def __repr__(self) -> str:
        return f"HistoryManager(entries={len(self._entries)}, max={self._max_entries})"
