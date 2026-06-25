"""
Core State Machine implementation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from .action import Action, EntryAction, ExitAction, FunctionAction, TransitionAction
from .error import (
    ActionError,
    ConfigurationError,
    GuardRejectedError,
    InvalidEventError,
    InvalidStateError,
    TransitionError,
)
from .event import Event
from .guard import Guard
from .history import HistoryEntry, HistoryManager, HistoryState
from .state import State
from .transition import Transition, TransitionBuilder


class StateMachine:
    """
    A finite state machine implementation.

    Supports:
    - State definitions with entry/exit actions
    - Event-driven transitions
    - Guard conditions
    - Transition actions
    - History recording
    - Callbacks for state changes and failures

    Example:
        >>> sm = StateMachine(State("Off"))
        >>> sm.add_transition(Transition(
        ...     from_state=State("Off"),
        ...     to_state=State("On"),
        ...     event=Event("TurnOn")
        ... ))
        >>> sm.process_event(Event("TurnOn"))
        >>> sm.current_state
        State('On')
    """

    def __init__(
        self,
        initial_state: State,
        enable_history: bool = True,
        history_capacity: int = 1000,
    ) -> None:
        """
        Initialize the state machine.

        Args:
            initial_state: The initial state
            enable_history: Whether to record transition history
            history_capacity: Maximum history entries to keep
        """
        self._initial_state: State = initial_state
        self._current_state: State = initial_state
        self._transitions: List[Transition] = []
        self._states: Set[State] = {initial_state}
        self._events: Set[Event] = set()

        # History
        self._enable_history = enable_history
        self._history: Optional[HistoryManager] = (
            HistoryManager(history_capacity) if enable_history else None
        )
        self._history_state = HistoryState()

        # Callbacks
        self._on_state_change: Optional[Callable] = None
        self._on_transition_failed: Optional[Callable] = None
        self._on_event_processed: Optional[Callable] = None

        # Context
        self._context: Dict[str, Any] = {}

    @property
    def current_state(self) -> State:
        """Get the current state."""
        return self._current_state

    @property
    def states(self) -> Set[State]:
        """Get all defined states."""
        return self._states.copy()

    @property
    def events(self) -> Set[Event]:
        """Get all defined events."""
        return self._events.copy()

    @property
    def transitions(self) -> List[Transition]:
        """Get all defined transitions."""
        return self._transitions.copy()

    @property
    def history(self) -> Optional[HistoryManager]:
        """Get the history manager."""
        return self._history

    @property
    def context(self) -> Dict[str, Any]:
        """Get the current context."""
        return self._context

    @context.setter
    def context(self, value: Dict[str, Any]) -> None:
        """Set the context."""
        self._context = value

    def add_transition(self, transition: Transition) -> None:
        """
        Add a transition to the state machine.

        Args:
            transition: The transition to add

        Raises:
            ConfigurationError: If the transition is invalid
        """
        # Validate states exist
        self._states.add(transition.from_state)
        self._states.add(transition.to_state)
        self._events.add(transition.event)

        # Check for duplicate transitions
        for existing in self._transitions:
            if existing.matches(transition.from_state, transition.event):
                if existing.to_state == transition.to_state:
                    raise ConfigurationError(
                        f"Duplicate transition: {transition.from_state} -> "
                        f"{transition.to_state} on {transition.event}"
                    )

        self._transitions.append(transition)

    def add_transitions(self, transitions: List[Transition]) -> None:
        """
        Add multiple transitions.

        Args:
            transitions: List of transitions to add
        """
        for transition in transitions:
            self.add_transition(transition)

    def on_state_change(self, callback: Callable) -> None:
        """
        Set callback for state changes.

        Args:
            callback: Function(from_state, to_state, event)
        """
        self._on_state_change = callback

    def on_transition_failed(self, callback: Callable) -> None:
        """
        Set callback for failed transitions.

        Args:
            callback: Function(from_state, event, error)
        """
        self._on_transition_failed = callback

    def on_event_processed(self, callback: Callable) -> None:
        """
        Set callback for event processing.

        Args:
            callback: Function(event, success)
        """
        self._on_event_processed = callback

    def process_event(
        self,
        event: Event,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Process an event, triggering a transition if applicable.

        Args:
            event: The event to process
            context: Optional context data (merged with instance context)

        Returns:
            True if a transition occurred, False otherwise

        Raises:
            InvalidEventError: If no transition is defined for the event
        """
        # Merge contexts
        merged_context = {**self._context}
        if context:
            merged_context.update(context)

        # Find matching transitions
        matching_transitions = [
            t for t in self._transitions
            if t.matches(self._current_state, event)
        ]

        if not matching_transitions:
            error = InvalidEventError(event, self._current_state)
            if self._on_transition_failed:
                self._on_transition_failed(self._current_state, event, error)
            if self._enable_history and self._history:
                self._history.push(HistoryEntry(
                    timestamp=datetime.now(),
                    from_state=self._current_state,
                    to_state=self._current_state,
                    event=event,
                    success=False,
                    context=merged_context,
                    error=error,
                ))
            return False

        # Try each matching transition
        for transition in matching_transitions:
            if transition.can_transition(merged_context):
                return self._execute_transition(transition, merged_context)

        # All guards rejected
        error = GuardRejectedError(
            self._current_state,
            matching_transitions[0].to_state,
            event,
        )
        if self._on_transition_failed:
            self._on_transition_failed(self._current_state, event, error)
        if self._enable_history and self._history:
            self._history.push(HistoryEntry(
                timestamp=datetime.now(),
                from_state=self._current_state,
                to_state=matching_transitions[0].to_state,
                event=event,
                success=False,
                context=merged_context,
                error=error,
            ))
        return False

    def _execute_transition(
        self,
        transition: Transition,
        context: Dict[str, Any],
    ) -> bool:
        """
        Execute a transition.

        Args:
            transition: The transition to execute
            context: The merged context

        Returns:
            True if successful
        """
        from_state = self._current_state
        to_state = transition.to_state
        event = transition.event

        try:
            # Execute exit action on current state
            from_state.on_exit(context)

            # Execute transition action
            transition.execute(context)

            # Update state
            self._current_state = to_state

            # Execute entry action on new state
            to_state.on_enter(context)

            # Record history
            if self._enable_history and self._history:
                entry = HistoryEntry(
                    timestamp=datetime.now(),
                    from_state=from_state,
                    to_state=to_state,
                    event=event,
                    success=True,
                    context=context,
                )
                self._history.push(entry)

            # Notify callback
            if self._on_state_change:
                self._on_state_change(from_state, to_state, event)

            if self._on_event_processed:
                self._on_event_processed(event, True)

            return True

        except Exception as e:
            error = ActionError(
                f"Action failed during transition: {e}",
                original_error=e,
            )
            if self._on_transition_failed:
                self._on_transition_failed(from_state, event, error)
            if self._enable_history and self._history:
                entry = HistoryEntry(
                    timestamp=datetime.now(),
                    from_state=from_state,
                    to_state=to_state,
                    event=event,
                    success=False,
                    context=context,
                    error=error,
                )
                self._history.push(entry)
            return False

    def can_process_event(self, event: Event) -> bool:
        """
        Check if an event can be processed.

        Args:
            event: The event to check

        Returns:
            True if a transition exists and guard passes
        """
        for transition in self._transitions:
            if transition.matches(self._current_state, event):
                if transition.can_transition(self._context):
                    return True
        return False

    def possible_events(self) -> List[Event]:
        """
        Get all possible events from the current state.

        Returns:
            List of events that have defined transitions
        """
        return [
            t.event for t in self._transitions
            if t.from_state == self._current_state
        ]

    def possible_transitions(self) -> List[Transition]:
        """
        Get all possible transitions from the current state.

        Returns:
            List of transitions from the current state
        """
        return [
            t for t in self._transitions
            if t.from_state == self._current_state
        ]

    def set_state(self, state: State) -> None:
        """
        Directly set the current state (without transition).

        Args:
            state: The state to set

        Raises:
            InvalidStateError: If the state is not defined
        """
        if state not in self._states:
            raise InvalidStateError(state)
        self._current_state = state

    def reset(self, state: Optional[State] = None) -> None:
        """
        Reset the state machine to initial or specified state.

        Args:
            state: Optional state to reset to
        """
        if state:
            self._current_state = state
        else:
            self._current_state = self._initial_state
        if self._history:
            self._history.clear()

    def format_transitions(self) -> str:
        """
        Format all transitions as a string.

        Returns:
            Formatted string of all transitions
        """
        if not self._transitions:
            return "No transitions defined"
        return "\n".join(str(t) for t in self._transitions)

    def format_graph(self) -> str:
        """
        Format the state machine as a DOT graph.

        Returns:
            DOT format graph string
        """
        lines = ["digraph StateMachine {"]
        lines.append('  rankdir=LR;')
        lines.append('  node [shape=circle];')

        # Mark initial state
        lines.append(f'  "" [shape=point];')
        lines.append(f'  "" -> "{self._current_state}";')

        # Add transitions
        for t in self._transitions:
            label = str(t.event)
            if t.description:
                label = t.description
            lines.append(f'  "{t.from_state}" -> "{t.to_state}" [label="{label}"];')

        lines.append("}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"StateMachine(state={self._current_state}, "
            f"transitions={len(self._transitions)}, "
            f"states={len(self._states)})"
        )


def create_state_machine(
    initial_state: State,
    transitions: Optional[List[Transition]] = None,
    enable_history: bool = True,
) -> StateMachine:
    """
    Factory function to create a state machine.

    Args:
        initial_state: The initial state
        transitions: Optional list of transitions
        enable_history: Whether to enable history

    Returns:
        A configured StateMachine instance

    Example:
        >>> sm = create_state_machine(
        ...     State("Off"),
        ...     transitions=[
        ...         Transition(State("Off"), State("On"), Event("TurnOn")),
        ...         Transition(State("On"), State("Off"), Event("TurnOff")),
        ...     ]
        ... )
    """
    sm = StateMachine(initial_state, enable_history)
    if transitions:
        sm.add_transitions(transitions)
    return sm
