"""
State Machine Framework - A comprehensive state machine library for Python

Features:
- Finite State Machine (FSM)
- Hierarchical State Machine (HSM)
- Guard conditions
- Entry/Exit/Transition actions
- History states
- Event-driven architecture
"""

from .state_machine import StateMachine
from .hierarchical import HierarchicalStateMachine
from .state import State, HierarchicalState
from .event import Event
from .transition import Transition, TransitionBuilder
from .guard import Guard, FunctionGuard
from .action import Action, FunctionAction, EntryAction, ExitAction, TransitionAction
from .history import HistoryManager, HistoryState, HistoryEntry
from .error import (
    StateMachineError,
    TransitionError,
    GuardRejectedError,
    InvalidStateError,
    InvalidEventError,
)

__version__ = "1.0.0"
__all__ = [
    # Core
    "StateMachine",
    "HierarchicalStateMachine",
    # Types
    "State",
    "HierarchicalState",
    "Event",
    "Transition",
    "TransitionBuilder",
    "Guard",
    "FunctionGuard",
    "Action",
    "FunctionAction",
    "EntryAction",
    "ExitAction",
    "TransitionAction",
    # History
    "HistoryManager",
    "HistoryState",
    "HistoryEntry",
    # Errors
    "StateMachineError",
    "TransitionError",
    "GuardRejectedError",
    "InvalidStateError",
    "InvalidEventError",
]
