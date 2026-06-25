"""
Error definitions for the state machine framework.
"""

from __future__ import annotations

from typing import Any, Optional


class StateMachineError(Exception):
    """
    Base exception for state machine errors.

    All state machine related exceptions inherit from this.
    """

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        """
        Initialize the error.

        Args:
            message: Error message
            details: Optional additional details
        """
        super().__init__(message)
        self.details = details


class TransitionError(StateMachineError):
    """
    Raised when a transition fails.

    This can happen when:
    - No transition is defined for the current state and event
    - The transition guard rejects the transition
    - The transition action fails
    """

    def __init__(
        self,
        message: str,
        from_state: Optional[Any] = None,
        to_state: Optional[Any] = None,
        event: Optional[Any] = None,
        details: Optional[Any] = None,
    ) -> None:
        """
        Initialize the transition error.

        Args:
            message: Error message
            from_state: The source state
            to_state: The target state (if known)
            event: The triggering event
            details: Optional additional details
        """
        super().__init__(message, details)
        self.from_state = from_state
        self.to_state = to_state
        self.event = event


class GuardRejectedError(TransitionError):
    """
    Raised when a guard condition rejects a transition.

    This is a specific type of TransitionError that occurs when
    the guard condition returns False.
    """

    def __init__(
        self,
        from_state: Optional[Any] = None,
        to_state: Optional[Any] = None,
        event: Optional[Any] = None,
        guard: Optional[Any] = None,
        details: Optional[Any] = None,
    ) -> None:
        """
        Initialize the guard rejected error.

        Args:
            from_state: The source state
            to_state: The target state
            event: The triggering event
            guard: The guard that rejected the transition
            details: Optional additional details
        """
        message = f"Guard rejected transition"
        if from_state and to_state and event:
            message = f"Guard rejected transition: {from_state} -> {to_state} on {event}"
        super().__init__(message, from_state, to_state, event, details)
        self.guard = guard


class InvalidStateError(StateMachineError):
    """
    Raised when an invalid state is referenced.

    This can happen when:
    - Trying to set an undefined state
    - Referencing a non-existent state in a transition
    """

    def __init__(
        self,
        state: Optional[Any] = None,
        message: Optional[str] = None,
        details: Optional[Any] = None,
    ) -> None:
        """
        Initialize the invalid state error.

        Args:
            state: The invalid state
            message: Optional custom message
            details: Optional additional details
        """
        if message is None:
            message = f"Invalid state: {state}" if state else "Invalid state"
        super().__init__(message, details)
        self.state = state


class InvalidEventError(StateMachineError):
    """
    Raised when an invalid event is processed.

    This can happen when:
    - Processing an event with no defined transition
    - The event is not recognized by the state machine
    """

    def __init__(
        self,
        event: Optional[Any] = None,
        state: Optional[Any] = None,
        message: Optional[str] = None,
        details: Optional[Any] = None,
    ) -> None:
        """
        Initialize the invalid event error.

        Args:
            event: The invalid event
            state: The current state (if known)
            message: Optional custom message
            details: Optional additional details
        """
        if message is None:
            if event and state:
                message = f"No transition defined for event {event} in state {state}"
            elif event:
                message = f"Invalid event: {event}"
            else:
                message = "Invalid event"
        super().__init__(message, details)
        self.event = event
        self.state = state


class ActionError(StateMachineError):
    """
    Raised when an action fails during execution.

    This can happen when:
    - An entry action throws an exception
    - An exit action throws an exception
    - A transition action throws an exception
    """

    def __init__(
        self,
        message: str,
        action: Optional[Any] = None,
        original_error: Optional[Exception] = None,
        details: Optional[Any] = None,
    ) -> None:
        """
        Initialize the action error.

        Args:
            message: Error message
            action: The action that failed
            original_error: The original exception
            details: Optional additional details
        """
        super().__init__(message, details)
        self.action = action
        self.original_error = original_error


class ConfigurationError(StateMachineError):
    """
    Raised when the state machine is misconfigured.

    This can happen when:
    - Missing required transitions
    - Invalid state hierarchy
    - Duplicate state definitions
    """

    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        details: Optional[Any] = None,
    ) -> None:
        """
        Initialize the configuration error.

        Args:
            message: Error message
            component: The component with the configuration issue
            details: Optional additional details
        """
        super().__init__(message, details)
        self.component = component
