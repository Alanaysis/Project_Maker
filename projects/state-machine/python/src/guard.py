"""
Guard conditions for state transitions.

Guards are boolean conditions that must be satisfied for a transition to occur.
They can be used to implement conditional logic in state machines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Union


class Guard(ABC):
    """
    Abstract base class for guard conditions.

    Guards determine whether a transition should be allowed based on
    the current state, event, and optional context.

    Example:
        >>> class AgeGuard(Guard):
        ...     def __init__(self, min_age: int):
        ...         self.min_age = min_age
        ...
        ...     def check(self, from_state, to_state, event, context=None):
        ...         return context.get("age", 0) >= self.min_age
    """

    @abstractmethod
    def check(
        self,
        from_state: Any,
        to_state: Any,
        event: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Check if the guard condition is satisfied.

        Args:
            from_state: The source state
            to_state: The target state
            event: The triggering event
            context: Optional context data

        Returns:
            True if the transition should be allowed, False otherwise
        """
        pass

    def __and__(self, other: Guard) -> Guard:
        """Combine two guards with AND logic."""
        return AndGuard(self, other)

    def __or__(self, other: Guard) -> Guard:
        """Combine two guards with OR logic."""
        return OrGuard(self, other)

    def __invert__(self) -> Guard:
        """Negate this guard."""
        return NotGuard(self)


@dataclass
class FunctionGuard(Guard):
    """
    A guard that wraps a callable function.

    Example:
        >>> guard = FunctionGuard(lambda f, t, e, c: c.get("authenticated", False))
        >>> guard.check("locked", "unlocked", "unlock", {"authenticated": True})
        True
    """

    func: Callable[[Any, Any, Any, Optional[Dict[str, Any]]], bool]
    name: Optional[str] = None

    def check(
        self,
        from_state: Any,
        to_state: Any,
        event: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Check using the wrapped function."""
        return self.func(from_state, to_state, event, context)

    def __repr__(self) -> str:
        if self.name:
            return f"FunctionGuard('{self.name}')"
        return f"FunctionGuard({self.func.__name__})"


@dataclass
class AndGuard(Guard):
    """
    Combines two guards with AND logic.

    Both guards must be satisfied for the combined guard to pass.
    """

    left: Guard
    right: Guard

    def check(
        self,
        from_state: Any,
        to_state: Any,
        event: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Check both guards."""
        return self.left.check(from_state, to_state, event, context) and \
               self.right.check(from_state, to_state, event, context)

    def __repr__(self) -> str:
        return f"({self.left!r} AND {self.right!r})"


@dataclass
class OrGuard(Guard):
    """
    Combines two guards with OR logic.

    Either guard must be satisfied for the combined guard to pass.
    """

    left: Guard
    right: Guard

    def check(
        self,
        from_state: Any,
        to_state: Any,
        event: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Check either guard."""
        return self.left.check(from_state, to_state, event, context) or \
               self.right.check(from_state, to_state, event, context)

    def __repr__(self) -> str:
        return f"({self.left!r} OR {self.right!r})"


@dataclass
class NotGuard(Guard):
    """
    Negates a guard condition.

    The combined guard passes when the wrapped guard fails.
    """

    guard: Guard

    def check(
        self,
        from_state: Any,
        to_state: Any,
        event: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Negate the guard check."""
        return not self.guard.check(from_state, to_state, event, context)

    def __repr__(self) -> str:
        return f"NOT {self.guard!r}"


@dataclass
class AlwaysTrueGuard(Guard):
    """
    A guard that always passes.

    Useful as a default guard or for testing.
    """

    def check(
        self,
        from_state: Any,
        to_state: Any,
        event: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Always return True."""
        return True

    def __repr__(self) -> str:
        return "AlwaysTrue()"


@dataclass
class AlwaysFalseGuard(Guard):
    """
    A guard that always fails.

    Useful for blocking transitions or testing.
    """

    def check(
        self,
        from_state: Any,
        to_state: Any,
        event: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Always return False."""
        return False

    def __repr__(self) -> str:
        return "AlwaysFalse()"


# Convenience functions for creating guards

def guard(func: Callable) -> FunctionGuard:
    """
    Decorator/function to create a guard from a callable.

    Args:
        func: A callable that takes (from_state, to_state, event, context)

    Returns:
        A FunctionGuard wrapping the callable

    Example:
        >>> @guard
        ... def is_authenticated(from_state, to_state, event, context):
        ...     return context.get("authenticated", False)
    """
    return FunctionGuard(func)


def always_true() -> AlwaysTrueGuard:
    """Create a guard that always passes."""
    return AlwaysTrueGuard()


def always_false() -> AlwaysFalseGuard:
    """Create a guard that always fails."""
    return AlwaysFalseGuard()


def context_has(key: str, value: Any = None) -> FunctionGuard:
    """
    Create a guard that checks if context has a specific key/value.

    Args:
        key: The key to check
        value: Optional value to compare against

    Returns:
        A FunctionGuard that checks the context

    Example:
        >>> has_role_admin = context_has("role", "admin")
    """
    def check(f, t, e, c):
        if c is None:
            return False
        if key not in c:
            return False
        if value is not None:
            return c[key] == value
        return True

    return FunctionGuard(check, name=f"context_has({key!r}, {value!r})")


def state_is(state_name: str) -> FunctionGuard:
    """
    Create a guard that checks if the current state matches.

    Args:
        state_name: The state name to check

    Returns:
        A FunctionGuard that checks the from_state

    Example:
        >>> is_idle = state_is("Idle")
    """
    def check(f, t, e, c):
        return str(f) == state_name

    return FunctionGuard(check, name=f"state_is({state_name!r})")
