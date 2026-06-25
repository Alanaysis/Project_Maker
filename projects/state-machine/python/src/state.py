"""
State definitions for the state machine framework.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set


class State(ABC):
    """
    Abstract base class for states in a state machine.

    A state represents a specific condition or situation of the system.
    States must be hashable and comparable.

    Example:
        >>> class LightState(State):
        ...     def __init__(self, name: str):
        ...         super().__init__(name)
        ...
        >>> off = LightState("Off")
        >>> on = LightState("On")
    """

    def __init__(self, name: str, **kwargs: Any) -> None:
        """
        Initialize a state.

        Args:
            name: Human-readable name for the state
            **kwargs: Additional metadata for the state
        """
        self._name = name
        self._metadata: Dict[str, Any] = kwargs
        self._entry_actions: List[Callable] = []
        self._exit_actions: List[Callable] = []

    @property
    def name(self) -> str:
        """Get the state name."""
        return self._name

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get state metadata."""
        return self._metadata.copy()

    def add_entry_action(self, action: Callable) -> None:
        """Add an entry action to execute when entering this state."""
        self._entry_actions.append(action)

    def add_exit_action(self, action: Callable) -> None:
        """Add an exit action to execute when leaving this state."""
        self._exit_actions.append(action)

    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute entry actions when entering this state.

        Args:
            context: Optional context data for the action
        """
        for action in self._entry_actions:
            action(self, context)

    def on_exit(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute exit actions when leaving this state.

        Args:
            context: Optional context data for the action
        """
        for action in self._exit_actions:
            action(self, context)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State):
            return NotImplemented
        return self._name == other._name

    def __hash__(self) -> int:
        return hash(self._name)

    def __repr__(self) -> str:
        return f"State('{self._name}')"

    def __str__(self) -> str:
        return self._name


class HierarchicalState(State):
    """
    A state that can contain sub-states, forming a hierarchical state machine.

    Hierarchical states allow for nested state machines, where entering a parent
    state automatically activates a child state machine.

    Example:
        >>> class ConnectionState(HierarchicalState):
        ...     pass
        >>> active = ConnectionState("Active")
        >>> active.add_sub_state(State("Idle"))
        >>> active.add_sub_state(State("Processing"))
        >>> active.initial_state = "Idle"
    """

    def __init__(self, name: str, use_history: bool = False, **kwargs: Any) -> None:
        """
        Initialize the hierarchical state.

        Args:
            name: State name
            use_history: Whether to use history state on re-entry
            **kwargs: Additional metadata
        """
        super().__init__(name, **kwargs)
        self._sub_states: Dict[str, State] = {}
        self._initial_state: Optional[str] = None
        self._current_sub_state: Optional[str] = None
        self._history_state: Optional[str] = None
        self._use_history = use_history

    @property
    def sub_states(self) -> Dict[str, State]:
        """Get all sub-states."""
        return self._sub_states.copy()

    @property
    def initial_state(self) -> Optional[str]:
        """Get the initial sub-state name."""
        return self._initial_state

    @initial_state.setter
    def initial_state(self, state_name: str) -> None:
        """
        Set the initial sub-state.

        Args:
            state_name: Name of the initial sub-state

        Raises:
            ValueError: If the state doesn't exist in sub-states
        """
        if state_name not in self._sub_states:
            raise ValueError(f"Sub-state '{state_name}' not found")
        self._initial_state = state_name

    @property
    def current_sub_state(self) -> Optional[State]:
        """Get the current active sub-state."""
        if self._current_sub_state:
            return self._sub_states.get(self._current_sub_state)
        return None

    @property
    def history_state(self) -> Optional[str]:
        """Get the last active sub-state (for history)."""
        return self._history_state

    @property
    def use_history(self) -> bool:
        """Whether to use history state on re-entry."""
        return self._use_history

    @use_history.setter
    def use_history(self, value: bool) -> None:
        """Enable or disable history state usage."""
        self._use_history = value

    def add_sub_state(self, state: State) -> None:
        """
        Add a sub-state to this hierarchical state.

        Args:
            state: The sub-state to add
        """
        self._sub_states[state.name] = state
        # If this is the first sub-state, set it as initial
        if len(self._sub_states) == 1 and self._initial_state is None:
            self._initial_state = state.name

    def remove_sub_state(self, state_name: str) -> Optional[State]:
        """
        Remove a sub-state.

        Args:
            state_name: Name of the sub-state to remove

        Returns:
            The removed state, or None if not found
        """
        state = self._sub_states.pop(state_name, None)
        if state_name == self._initial_state:
            self._initial_state = next(iter(self._sub_states), None)
        if state_name == self._current_sub_state:
            self._current_sub_state = None
        return state

    def activate(self) -> State:
        """
        Activate this hierarchical state.

        Returns:
            The initial or history sub-state
        """
        if self._use_history and self._history_state:
            self._current_sub_state = self._history_state
        elif self._initial_state:
            self._current_sub_state = self._initial_state
        return self

    def deactivate(self) -> None:
        """Deactivate this hierarchical state, saving history."""
        if self._current_sub_state:
            self._history_state = self._current_sub_state
            self._current_sub_state = None

    def transition_to(self, state_name: str) -> Optional[State]:
        """
        Transition to a sub-state.

        Args:
            state_name: Name of the target sub-state

        Returns:
            The new current sub-state, or None if invalid
        """
        if state_name in self._sub_states:
            self._history_state = self._current_sub_state
            self._current_sub_state = state_name
            return self._sub_states[state_name]
        return None

    def on_enter(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Execute entry actions and activate sub-state."""
        super().on_enter(context)
        self.activate()

    def on_exit(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Execute exit actions and deactivate sub-state."""
        self.deactivate()
        super().on_exit(context)


def create_state(name: str, **kwargs: Any) -> State:
    """
    Factory function to create a simple state.

    Args:
        name: State name
        **kwargs: Additional metadata

    Returns:
        A new State instance
    """
    return State(name, **kwargs)


def create_hierarchical_state(
    name: str,
    sub_states: Optional[List[State]] = None,
    initial: Optional[str] = None,
    use_history: bool = False,
    **kwargs: Any,
) -> HierarchicalState:
    """
    Factory function to create a hierarchical state.

    Args:
        name: State name
        sub_states: List of sub-states to add
        initial: Name of initial sub-state
        use_history: Whether to use history on re-entry
        **kwargs: Additional metadata

    Returns:
        A new HierarchicalState instance
    """
    state = HierarchicalState(name, **kwargs)
    state.use_history = use_history

    if sub_states:
        for sub_state in sub_states:
            state.add_sub_state(sub_state)

    if initial:
        state.initial_state = initial

    return state
