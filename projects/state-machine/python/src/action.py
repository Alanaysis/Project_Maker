"""
Action definitions for state transitions.

Actions are executed during state transitions and can be used to perform
side effects, update data, or trigger external systems.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class ActionTiming(Enum):
    """When an action should be executed."""

    ENTRY = auto()  # When entering a state
    EXIT = auto()  # When leaving a state
    TRANSITION = auto()  # During a transition


class Action(ABC):
    """
    Abstract base class for actions.

    Actions are executed during state transitions and can perform
    various side effects.

    Example:
        >>> class LogAction(Action):
        ...     def execute(self, from_state, to_state, event, context):
        ...         print(f"Transitioning from {from_state} to {to_state}")
    """

    @abstractmethod
    def execute(
        self,
        from_state: Any,
        to_state: Any,
        event: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        Execute the action.

        Args:
            from_state: The source state
            to_state: The target state
            event: The triggering event
            context: Optional context data

        Returns:
            Optional result of the action
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


@dataclass
class FunctionAction(Action):
    """
    An action that wraps a callable function.

    Example:
        >>> action = FunctionAction(lambda f, t, e, c: print(f"From {f} to {t}"))
        >>> action.execute("off", "on", "turn_on")
    """

    func: Callable[[Any, Any, Any, Optional[Dict[str, Any]]], Optional[Any]]
    name: Optional[str] = None

    def execute(
        self,
        from_state: Any,
        to_state: Any,
        event: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """Execute the wrapped function."""
        return self.func(from_state, to_state, event, context)

    def __repr__(self) -> str:
        if self.name:
            return f"FunctionAction('{self.name}')"
        return f"FunctionAction({self.func.__name__})"


class EntryAction(Action):
    """
    Action executed when entering a state.

    Example:
        >>> action = EntryAction(lambda s, c: print(f"Entered {s}"))
        >>> action.execute(None, "active", None)
    """

    def __init__(
        self,
        func: Callable[[Any, Optional[Dict[str, Any]]], Optional[Any]],
        name: Optional[str] = None,
    ) -> None:
        """
        Initialize an entry action.

        Args:
            func: Function taking (state, context)
            name: Optional name for the action
        """
        self._func = func
        self._name = name

    def execute(
        self,
        from_state: Any,
        to_state: Any,
        event: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """Execute when entering to_state."""
        return self._func(to_state, context)

    def __repr__(self) -> str:
        if self._name:
            return f"EntryAction('{self._name}')"
        return f"EntryAction({self._func.__name__})"


class ExitAction(Action):
    """
    Action executed when leaving a state.

    Example:
        >>> action = ExitAction(lambda s, c: print(f"Left {s}"))
        >>> action.execute("active", None, None)
    """

    def __init__(
        self,
        func: Callable[[Any, Optional[Dict[str, Any]]], Optional[Any]],
        name: Optional[str] = None,
    ) -> None:
        """
        Initialize an exit action.

        Args:
            func: Function taking (state, context)
            name: Optional name for the action
        """
        self._func = func
        self._name = name

    def execute(
        self,
        from_state: Any,
        to_state: Any,
        event: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """Execute when leaving from_state."""
        return self._func(from_state, context)

    def __repr__(self) -> str:
        if self._name:
            return f"ExitAction('{self._name}')"
        return f"ExitAction({self._func.__name__})"


class TransitionAction(Action):
    """
    Action executed during a transition.

    Example:
        >>> action = TransitionAction(lambda f, t, e, c: print(f"{f} -> {t}"))
        >>> action.execute("off", "on", "turn_on")
    """

    def __init__(
        self,
        func: Callable[[Any, Any, Any, Optional[Dict[str, Any]]], Optional[Any]],
        name: Optional[str] = None,
    ) -> None:
        """
        Initialize a transition action.

        Args:
            func: Function taking (from_state, to_state, event, context)
            name: Optional name for the action
        """
        self._func = func
        self._name = name

    def execute(
        self,
        from_state: Any,
        to_state: Any,
        event: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """Execute during the transition."""
        return self._func(from_state, to_state, event, context)

    def __repr__(self) -> str:
        if self._name:
            return f"TransitionAction('{self._name}')"
        return f"TransitionAction({self._func.__name__})"


class CompositeAction(Action):
    """
    An action that combines multiple actions.

    Actions are executed in the order they are added.

    Example:
        >>> action = CompositeAction([
        ...     FunctionAction(lambda f, t, e, c: print("Step 1")),
        ...     FunctionAction(lambda f, t, e, c: print("Step 2")),
        ... ])
    """

    def __init__(self, actions: Optional[List[Action]] = None) -> None:
        """
        Initialize with a list of actions.

        Args:
            actions: Initial list of actions
        """
        self._actions: List[Action] = actions or []

    def add(self, action: Action) -> CompositeAction:
        """
        Add an action to the composite.

        Args:
            action: The action to add

        Returns:
            Self for chaining
        """
        self._actions.append(action)
        return self

    def execute(
        self,
        from_state: Any,
        to_state: Any,
        event: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Optional[Any]]:
        """
        Execute all actions in order.

        Returns:
            List of results from each action
        """
        results = []
        for action in self._actions:
            result = action.execute(from_state, to_state, event, context)
            results.append(result)
        return results

    def __repr__(self) -> str:
        return f"CompositeAction({len(self._actions)} actions)"


# Convenience functions for creating actions

def action(func: Callable) -> FunctionAction:
    """
    Create an action from a callable.

    Args:
        func: A callable that takes (from_state, to_state, event, context)

    Returns:
        A FunctionAction wrapping the callable

    Example:
        >>> @action
        ... def log_transition(from_state, to_state, event, context):
        ...     print(f"{from_state} -> {to_state}")
    """
    return FunctionAction(func)


def entry_action(func: Callable) -> EntryAction:
    """
    Create an entry action from a callable.

    Args:
        func: A callable that takes (state, context)

    Returns:
        An EntryAction wrapping the callable
    """
    return EntryAction(func)


def exit_action(func: Callable) -> ExitAction:
    """
    Create an exit action from a callable.

    Args:
        func: A callable that takes (state, context)

    Returns:
        An ExitAction wrapping the callable
    """
    return ExitAction(func)


def transition_action(func: Callable) -> TransitionAction:
    """
    Create a transition action from a callable.

    Args:
        func: A callable that takes (from_state, to_state, event, context)

    Returns:
        A TransitionAction wrapping the callable
    """
    return TransitionAction(func)


def log_action(message: str = "") -> FunctionAction:
    """
    Create an action that logs a message.

    Args:
        message: Optional message template with {from}, {to}, {event} placeholders

    Returns:
        A FunctionAction that prints a log message
    """
    def log(f, t, e, c):
        if message:
            print(message.format(from_state=f, to_state=t, event=e, context=c))
        else:
            print(f"Transition: {f} -> {t} on {e}")

    return FunctionAction(log, name="log")


def update_context_action(key: str, value: Any) -> FunctionAction:
    """
    Create an action that updates the context.

    Args:
        key: The key to set
        value: The value to set

    Returns:
        A FunctionAction that updates context
    """
    def update(f, t, e, c):
        if c is not None:
            c[key] = value
        return value

    return FunctionAction(update, name=f"update_context({key})")
