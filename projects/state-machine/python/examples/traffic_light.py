"""
Traffic Light State Machine Example

Demonstrates:
- Simple state machine with timed transitions
- Entry actions for state changes
- Context-based state management
"""

import sys
import time
from typing import Any, Dict

sys.path.insert(0, ".")

from src import (
    Event,
    State,
    StateMachine,
    Transition,
    FunctionAction,
    FunctionGuard,
)


# Define States
RED = State("Red")
YELLOW = State("Yellow")
GREEN = State("Green")
FLASHING = State("Flashing")


# Define Events
TIMER = Event("timer")
EMERGENCY = Event("emergency")
NORMAL = Event("normal")


# Define Actions
def on_red_enter(state: State, context: Dict[str, Any]) -> None:
    """Action when entering red state."""
    print("  RED light ON - Stop!")
    if context:
        context["current_light"] = "red"


def on_yellow_enter(state: State, context: Dict[str, Any]) -> None:
    """Action when entering yellow state."""
    print("  YELLOW light ON - Prepare to stop")
    if context:
        context["current_light"] = "yellow"


def on_green_enter(state: State, context: Dict[str, Any]) -> None:
    """Action when entering green state."""
    print("  GREEN light ON - Go!")
    if context:
        context["current_light"] = "green"


def on_flashing_enter(state: State, context: Dict[str, Any]) -> None:
    """Action when entering flashing state."""
    print("  FLASHING light ON - Caution!")
    if context:
        context["current_light"] = "flashing"


def log_transition(from_state: State, to_state: State, event: Event, context: Dict[str, Any]) -> None:
    """Log the transition."""
    print(f"  Transition: {from_state} -> {to_state}")


def create_traffic_light() -> StateMachine:
    """
    Create a traffic light state machine.

    Returns:
        Configured StateMachine instance
    """
    sm = StateMachine(RED, enable_history=True)

    # Add entry actions
    RED.add_entry_action(on_red_enter)
    YELLOW.add_entry_action(on_yellow_enter)
    GREEN.add_entry_action(on_green_enter)
    FLASHING.add_entry_action(on_flashing_enter)

    # Normal cycle: RED -> GREEN -> YELLOW -> RED
    sm.add_transition(Transition(
        from_state=RED,
        to_state=GREEN,
        event=TIMER,
        action=FunctionAction(log_transition, "log"),
        description="Red to Green"
    ))

    sm.add_transition(Transition(
        from_state=GREEN,
        to_state=YELLOW,
        event=TIMER,
        action=FunctionAction(log_transition, "log"),
        description="Green to Yellow"
    ))

    sm.add_transition(Transition(
        from_state=YELLOW,
        to_state=RED,
        event=TIMER,
        action=FunctionAction(log_transition, "log"),
        description="Yellow to Red"
    ))

    # Emergency transitions: any state -> FLASHING
    for state in [RED, YELLOW, GREEN]:
        sm.add_transition(Transition(
            from_state=state,
            to_state=FLASHING,
            event=EMERGENCY,
            action=FunctionAction(log_transition, "log"),
            description=f"Emergency: {state} -> Flashing"
        ))

    # Normal transition: FLASHING -> RED
    sm.add_transition(Transition(
        from_state=FLASHING,
        to_state=RED,
        event=NORMAL,
        action=FunctionAction(log_transition, "log"),
        description="Normal: Flashing -> Red"
    ))

    return sm


def demo_normal_cycle():
    """Demo normal traffic light cycle."""
    print("=" * 60)
    print("Traffic Light - Normal Cycle Demo")
    print("=" * 60)

    sm = create_traffic_light()
    context = {"intersection": "Main & 1st"}

    print(f"\nInitial state: {sm.current_state}")

    # Simulate normal cycle
    for i in range(6):
        print(f"\n--- Cycle {i + 1} ---")
        sm.process_event(TIMER, context)
        print(f"Current state: {sm.current_state}")

    # Show history
    print("\n" + "=" * 60)
    print("Transition History:")
    print("=" * 60)
    if sm.history:
        print(sm.history.format_all())


def demo_emergency():
    """Demo emergency scenario."""
    print("\n" + "=" * 60)
    print("Traffic Light - Emergency Demo")
    print("=" * 60)

    sm = create_traffic_light()
    context = {"intersection": "Main & 1st"}

    print(f"\nInitial state: {sm.current_state}")

    # Normal operation
    print("\n--- Normal Operation ---")
    sm.process_event(TIMER, context)
    print(f"Current state: {sm.current_state}")

    # Emergency!
    print("\n--- Emergency Vehicle Approaching! ---")
    sm.process_event(EMERGENCY, context)
    print(f"Current state: {sm.current_state}")

    # Back to normal
    print("\n--- Emergency Cleared ---")
    sm.process_event(NORMAL, context)
    print(f"Current state: {sm.current_state}")

    # Continue normal cycle
    print("\n--- Resume Normal Cycle ---")
    sm.process_event(TIMER, context)
    print(f"Current state: {sm.current_state}")


def demo_possible_events():
    """Demo checking possible events."""
    print("\n" + "=" * 60)
    print("Traffic Light - Possible Events Demo")
    print("=" * 60)

    sm = create_traffic_light()

    print(f"\nCurrent state: {sm.current_state}")
    print(f"Possible events: {[str(e) for e in sm.possible_events()]}")
    print(f"Can process TIMER? {sm.can_process_event(TIMER)}")
    print(f"Can process EMERGENCY? {sm.can_process_event(EMERGENCY)}")
    print(f"Can process NORMAL? {sm.can_process_event(NORMAL)}")


if __name__ == "__main__":
    demo_normal_cycle()
    demo_emergency()
    demo_possible_events()
