"""
Event definitions for the state machine framework.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class Event:
    """
    Represents an event that can trigger state transitions.

    Events are immutable and hashable, making them suitable for use as
    dictionary keys and in sets.

    Example:
        >>> turn_on = Event("TurnOn")
        >>> turn_off = Event("TurnOff")
        >>> click = Event("Click", button="left", double=False)
    """

    def __init__(self, name: str, data: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        """
        Initialize an event.

        Args:
            name: Event name
            data: Event data dictionary
            **kwargs: Additional data as keyword arguments
        """
        self._name = name
        self._data: Dict[str, Any] = {}
        if data:
            self._data.update(data)
        self._data.update(kwargs)

    @property
    def name(self) -> str:
        """Get the event name."""
        return self._name

    @property
    def data(self) -> Dict[str, Any]:
        """Get the event data."""
        return self._data.copy()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Event):
            return NotImplemented
        return self._name == other._name

    def __hash__(self) -> int:
        return hash(self._name)

    def __repr__(self) -> str:
        if self._data:
            return f"Event('{self._name}', {self._data})"
        return f"Event('{self._name}')"

    def __str__(self) -> str:
        return self._name

    def with_data(self, **kwargs: Any) -> Event:
        """
        Create a new event with additional data.

        Args:
            **kwargs: Data to add to the event

        Returns:
            A new Event with merged data
        """
        merged_data = {**self._data, **kwargs}
        return Event(self._name, merged_data)


def create_event(name: str, **data: Any) -> Event:
    """
    Factory function to create an event.

    Args:
        name: Event name
        **data: Event data

    Returns:
        A new Event instance
    """
    return Event(name, data)


# Common event types
class EventTypes:
    """Pre-defined event types for common use cases."""

    # Lifecycle events
    ENTER = Event("enter")
    EXIT = Event("exit")
    START = Event("start")
    STOP = Event("stop")
    PAUSE = Event("pause")
    RESUME = Event("resume")

    # Error events
    ERROR = Event("error")
    TIMEOUT = Event("timeout")
    CANCEL = Event("cancel")

    # Data events
    DATA_RECEIVED = Event("data_received")
    DATA_SENT = Event("data_sent")

    # User events
    USER_ACTION = Event("user_action")
    USER_INPUT = Event("user_input")

    # System events
    SYSTEM_READY = Event("system_ready")
    SYSTEM_SHUTDOWN = Event("system_shutdown")


# Event builder for complex events
class EventBuilder:
    """
    Builder pattern for creating complex events.

    Example:
        >>> event = (EventBuilder("OrderPlaced")
        ...     .with_data(order_id=123)
        ...     .with_data(amount=99.99)
        ...     .build())
    """

    def __init__(self, name: str) -> None:
        """Initialize the builder with an event name."""
        self._name = name
        self._data: Dict[str, Any] = {}

    def with_data(self, **kwargs: Any) -> EventBuilder:
        """
        Add data to the event.

        Args:
            **kwargs: Key-value pairs to add

        Returns:
            Self for chaining
        """
        self._data.update(kwargs)
        return self

    def with_key_value(self, key: str, value: Any) -> EventBuilder:
        """
        Add a single key-value pair to the event.

        Args:
            key: The key
            value: The value

        Returns:
            Self for chaining
        """
        self._data[key] = value
        return self

    def build(self) -> Event:
        """
        Build the event.

        Returns:
            The constructed Event
        """
        return Event(self._name, self._data.copy())
