"""
Transition definitions for the state machine framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from .action import Action, FunctionAction, TransitionAction
from .event import Event
from .guard import Guard, FunctionGuard, always_true
from .state import State


@dataclass
class Transition:
    """
    Represents a transition between two states triggered by an event.

    A transition defines:
    - Source state (from_state)
    - Target state (to_state)
    - Triggering event
    - Optional guard condition
    - Optional action to execute

    Example:
        >>> transition = Transition(
        ...     from_state=State("Off"),
        ...     to_state=State("On"),
        ...     event=Event("TurnOn"),
        ...     guard=FunctionGuard(lambda f, t, e, c: True),
        ...     action=FunctionAction(lambda f, t, e, c: print("Turned on!")),
        ...     description="Turn the light on"
        ... )
    """

    from_state: State
    to_state: State
    event: Event
    guard: Optional[Guard] = field(default_factory=always_true)
    action: Optional[Action] = None
    description: Optional[str] = None

    def can_transition(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Check if this transition can occur.

        Args:
            context: Optional context data for guard evaluation

        Returns:
            True if the guard condition is satisfied
        """
        if self.guard is None:
            return True
        return self.guard.check(self.from_state, self.to_state, self.event, context)

    def execute(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        Execute the transition action.

        Args:
            context: Optional context data for the action

        Returns:
            Result of the action, if any
        """
        if self.action is None:
            return None
        return self.action.execute(self.from_state, self.to_state, self.event, context)

    def matches(self, from_state: State, event: Event) -> bool:
        """
        Check if this transition matches a source state and event.

        Args:
            from_state: The source state to match
            event: The event to match

        Returns:
            True if this transition matches
        """
        return self.from_state == from_state and self.event == event

    def __repr__(self) -> str:
        parts = [f"{self.from_state} -> {self.to_state} on {self.event}"]
        if self.guard and not isinstance(self.guard, type(always_true())):
            parts.append(f"when {self.guard}")
        if self.action:
            parts.append(f"do {self.action}")
        if self.description:
            parts.append(f"# {self.description}")
        return "Transition(" + ", ".join(parts) + ")"

    def __str__(self) -> str:
        if self.description:
            return self.description
        return f"{self.from_state} -> {self.to_state} on {self.event}"


class TransitionBuilder:
    """
    Builder pattern for creating transitions.

    Provides a fluent API for constructing transitions step by step.

    Example:
        >>> transition = (TransitionBuilder()
        ...     .from_state(State("Off"))
        ...     .to_state(State("On"))
        ...     .on(Event("TurnOn"))
        ...     .when(lambda f, t, e, c: True)
        ...     .do(lambda f, t, e, c: print("Turning on"))
        ...     .describe("Turn the light on")
        ...     .build())
    """

    def __init__(self) -> None:
        """Initialize the builder."""
        self._from_state: Optional[State] = None
        self._to_state: Optional[State] = None
        self._event: Optional[Event] = None
        self._guard: Optional[Guard] = None
        self._action: Optional[Action] = None
        self._description: Optional[str] = None

    def from_state(self, state: State) -> TransitionBuilder:
        """
        Set the source state.

        Args:
            state: The source state

        Returns:
            Self for chaining
        """
        self._from_state = state
        return self

    def to_state(self, state: State) -> TransitionBuilder:
        """
        Set the target state.

        Args:
            state: The target state

        Returns:
            Self for chaining
        """
        self._to_state = state
        return self

    def to(self, state: State) -> TransitionBuilder:
        """
        Alias for to_state.

        Args:
            state: The target state

        Returns:
            Self for chaining
        """
        return self.to_state(state)

    def on(self, event: Event) -> TransitionBuilder:
        """
        Set the triggering event.

        Args:
            event: The triggering event

        Returns:
            Self for chaining
        """
        self._event = event
        return self

    def when(self, guard: Union[Guard, Callable]) -> TransitionBuilder:
        """
        Set the guard condition.

        Args:
            guard: A Guard instance or callable

        Returns:
            Self for chaining
        """
        if callable(guard) and not isinstance(guard, Guard):
            guard = FunctionGuard(guard)
        self._guard = guard
        return self

    def do(self, action: Union[Action, Callable]) -> TransitionBuilder:
        """
        Set the transition action.

        Args:
            action: An Action instance or callable

        Returns:
            Self for chaining
        """
        if callable(action) and not isinstance(action, Action):
            action = FunctionAction(action)
        self._action = action
        return self

    def describe(self, description: str) -> TransitionBuilder:
        """
        Set the description.

        Args:
            description: Human-readable description

        Returns:
            Self for chaining
        """
        self._description = description
        return self

    def build(self) -> Transition:
        """
        Build the transition.

        Returns:
            The constructed Transition

        Raises:
            ValueError: If required fields are missing
        """
        if self._from_state is None:
            raise ValueError("Source state is required")
        if self._to_state is None:
            raise ValueError("Target state is required")
        if self._event is None:
            raise ValueError("Event is required")

        return Transition(
            from_state=self._from_state,
            to_state=self._to_state,
            event=self._event,
            guard=self._guard,
            action=self._action,
            description=self._description,
        )


def create_transition(
    from_state: State,
    to_state: State,
    event: Event,
    guard: Optional[Union[Guard, Callable]] = None,
    action: Optional[Union[Action, Callable]] = None,
    description: Optional[str] = None,
) -> Transition:
    """
    Factory function to create a transition.

    Args:
        from_state: Source state
        to_state: Target state
        event: Triggering event
        guard: Optional guard condition
        action: Optional action to execute
        description: Optional description

    Returns:
        A new Transition instance

    Example:
        >>> transition = create_transition(
        ...     State("Off"), State("On"), Event("TurnOn"),
        ...     guard=lambda f, t, e, c: True,
        ...     action=lambda f, t, e, c: print("On!"),
        ... )
    """
    if callable(guard) and not isinstance(guard, Guard):
        guard = FunctionGuard(guard)
    if callable(action) and not isinstance(action, Action):
        action = FunctionAction(action)

    return Transition(
        from_state=from_state,
        to_state=to_state,
        event=event,
        guard=guard,
        action=action,
        description=description,
    )
