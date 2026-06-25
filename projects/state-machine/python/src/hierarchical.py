"""
Hierarchical State Machine implementation.

Supports nested states with history tracking.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from .action import Action, EntryAction, ExitAction, FunctionAction
from .error import (
    ConfigurationError,
    InvalidEventError,
    InvalidStateError,
    TransitionError,
)
from .event import Event
from .guard import Guard
from .history import HistoryEntry, HistoryManager, HistoryState
from .state import HierarchicalState, State
from .transition import Transition


class HierarchicalStateMachine:
    """
    A hierarchical state machine that supports nested states.

    Features:
    - Nested state hierarchies
    - History states (remember last active sub-state)
    - Event bubbling (events propagate up the hierarchy)
    - Entry/Exit actions at each level

    Example:
        >>> # Define states
        >>> idle = State("Idle")
        >>> processing = State("Processing")
        >>> active = HierarchicalState("Active")
        >>> active.add_sub_state(idle)
        >>> active.add_sub_state(processing)
        >>> active.initial_state = "Idle"
        >>>
        >>> inactive = State("Inactive")
        >>>
        >>> # Create HSM
        >>> hsm = HierarchicalStateMachine(inactive)
        >>> hsm.add_transition(Transition(inactive, active, Event("Activate")))
    """

    def __init__(
        self,
        initial_state: State,
        enable_history: bool = True,
        history_capacity: int = 1000,
    ) -> None:
        """
        Initialize the hierarchical state machine.

        Args:
            initial_state: The initial state
            enable_history: Whether to record history
            history_capacity: Maximum history entries
        """
        self._root_state = initial_state
        self._state_stack: List[State] = [initial_state]
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

        # Context
        self._context: Dict[str, Any] = {}

    @property
    def current_state(self) -> State:
        """Get the current (deepest) state."""
        if not self._state_stack:
            return self._root_state
        return self._state_stack[-1]

    @property
    def state_stack(self) -> List[State]:
        """Get the full state stack."""
        return self._state_stack.copy()

    @property
    def root_state(self) -> State:
        """Get the root state."""
        return self._root_state

    @property
    def states(self) -> Set[State]:
        """Get all defined states."""
        return self._states.copy()

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
        Add a transition to the HSM.

        Args:
            transition: The transition to add
        """
        self._states.add(transition.from_state)
        self._states.add(transition.to_state)
        self._events.add(transition.event)
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

    def process_event(
        self,
        event: Event,
        context: Optional[Dict[str, Any]] = None,
        bubble: bool = True,
    ) -> bool:
        """
        Process an event, triggering a transition if applicable.

        Events can optionally bubble up the hierarchy if no transition
        is found at the current level.

        Args:
            event: The event to process
            context: Optional context data
            bubble: Whether to bubble up the hierarchy

        Returns:
            True if a transition occurred
        """
        merged_context = {**self._context}
        if context:
            merged_context.update(context)

        # Try to find transition at each level of the hierarchy
        for i in range(len(self._state_stack) - 1, -1, -1):
            current = self._state_stack[i]

            # Find matching transitions
            matching = [
                t for t in self._transitions
                if t.matches(current, event)
            ]

            for transition in matching:
                if transition.can_transition(merged_context):
                    return self._execute_transition(transition, merged_context, i)

            if not bubble:
                break

        # No transition found
        error = InvalidEventError(event, self.current_state)
        if self._on_transition_failed:
            self._on_transition_failed(self.current_state, event, error)

        if self._enable_history and self._history:
            self._history.push(HistoryEntry(
                timestamp=datetime.now(),
                from_state=self.current_state,
                to_state=self.current_state,
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
        level: int,
    ) -> bool:
        """
        Execute a transition at a specific level.

        Args:
            transition: The transition to execute
            context: The merged context
            level: The hierarchy level where the transition applies

        Returns:
            True if successful
        """
        from_state = self._state_stack[level]
        to_state = transition.to_state
        event = transition.event

        try:
            # Exit current states up to the transition level
            for i in range(len(self._state_stack) - 1, level - 1, -1):
                self._state_stack[i].on_exit(context)

            # Trim the stack
            self._state_stack = self._state_stack[:level]

            # Execute transition action
            transition.execute(context)

            # Enter the new state
            to_state.on_enter(context)
            self._state_stack.append(to_state)

            # If it's a hierarchical state, enter sub-states
            if isinstance(to_state, HierarchicalState):
                sub_state = to_state.current_sub_state
                if sub_state:
                    sub_state.on_enter(context)
                    self._state_stack.append(sub_state)

            # Record history
            if self._enable_history and self._history:
                self._history.push(HistoryEntry(
                    timestamp=datetime.now(),
                    from_state=from_state,
                    to_state=self.current_state,
                    event=event,
                    success=True,
                    context=context,
                ))

            # Notify callback
            if self._on_state_change:
                self._on_state_change(from_state, self.current_state, event)

            return True

        except Exception as e:
            error = TransitionError(
                f"Transition failed: {e}",
                from_state,
                to_state,
                event,
            )
            if self._on_transition_failed:
                self._on_transition_failed(from_state, event, error)
            return False

    def enter_sub_state(self, state_name: str) -> bool:
        """
        Enter a sub-state of the current hierarchical state.

        Args:
            state_name: Name of the sub-state to enter

        Returns:
            True if successful
        """
        current = self.current_state

        # Check if parent is a hierarchical state
        if len(self._state_stack) >= 2:
            parent = self._state_stack[-2]
            if isinstance(parent, HierarchicalState):
                sub_state = parent.transition_to(state_name)
                if sub_state:
                    # Exit current sub-state
                    current.on_exit(self._context)

                    # Enter new sub-state
                    sub_state.on_enter(self._context)
                    self._state_stack[-1] = sub_state
                    return True

        return False

    def can_process_event(self, event: Event, bubble: bool = True) -> bool:
        """
        Check if an event can be processed.

        Args:
            event: The event to check
            bubble: Whether to check parent states

        Returns:
            True if a transition exists and guard passes
        """
        for i in range(len(self._state_stack) - 1, -1, -1):
            current = self._state_stack[i]
            for transition in self._transitions:
                if transition.matches(current, event):
                    if transition.can_transition(self._context):
                        return True
            if not bubble:
                break
        return False

    def possible_events(self, bubble: bool = True) -> List[Event]:
        """
        Get all possible events from the current state.

        Args:
            bubble: Whether to include events from parent states

        Returns:
            List of possible events
        """
        events = []
        seen = set()

        for i in range(len(self._state_stack) - 1, -1, -1):
            current = self._state_stack[i]
            for transition in self._transitions:
                if transition.from_state == current and transition.event not in seen:
                    events.append(transition.event)
                    seen.add(transition.event)
            if not bubble:
                break

        return events

    def get_history_state(self, parent_state_name: str) -> Optional[str]:
        """
        Get the history state for a hierarchical state.

        Args:
            parent_state_name: Name of the parent state

        Returns:
            The last active sub-state name, or None
        """
        return self._history_state.get(parent_state_name)

    def set_history_state(self, parent_state_name: str, sub_state_name: str) -> None:
        """
        Set the history state for a hierarchical state.

        Args:
            parent_state_name: Name of the parent state
            sub_state_name: Name of the sub-state to remember
        """
        self._history_state.save(parent_state_name, sub_state_name)

    def reset(self, state: Optional[State] = None) -> None:
        """
        Reset the HSM to initial or specified state.

        Args:
            state: Optional state to reset to
        """
        if state:
            self._root_state = state
            self._state_stack = [state]
        else:
            self._state_stack = [self._root_state]

        if self._history:
            self._history.clear()
        self._history_state.clear()

    def format_hierarchy(self) -> str:
        """
        Format the current state hierarchy.

        Returns:
            Formatted string showing the state stack
        """
        parts = []
        for i, state in enumerate(self._state_stack):
            indent = "  " * i
            parts.append(f"{indent}{state}")
        return "\n".join(parts)

    def format_transitions(self) -> str:
        """
        Format all transitions as a string.

        Returns:
            Formatted string of all transitions
        """
        if not self._transitions:
            return "No transitions defined"
        return "\n".join(str(t) for t in self._transitions)

    def __repr__(self) -> str:
        return (
            f"HierarchicalStateMachine(state={self.current_state}, "
            f"depth={len(self._state_stack)}, "
            f"transitions={len(self._transitions)})"
        )
