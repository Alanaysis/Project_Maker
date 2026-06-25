# State Machine Framework (Python)

A comprehensive state machine library for Python, supporting finite state machines, hierarchical state machines, guard conditions, and more.

## Features

- **Finite State Machine (FSM)**: Simple state transitions with events
- **Hierarchical State Machine (HSM)**: Nested states with history tracking
- **Guard Conditions**: Conditional transitions based on context
- **Entry/Exit Actions**: Execute code when entering or leaving states
- **Transition Actions**: Execute code during transitions
- **History States**: Remember last active sub-state in hierarchical machines
- **Event-Driven Architecture**: Process events to trigger transitions
- **Builder Pattern**: Fluent API for defining transitions
- **Callbacks**: React to state changes and failures
- **Comprehensive Error Handling**: Specific exception types for different failures

## Installation

```bash
# Clone or copy the state_machine package to your project
cp -r src/state_machine /path/to/your/project/
```

## Quick Start

### Basic Usage

```python
from src import StateMachine, State, Event, Transition

# Define states
off = State("Off")
on = State("On")

# Define events
turn_on = Event("TurnOn")
turn_off = Event("TurnOff")

# Create state machine
sm = StateMachine(off)

# Add transitions
sm.add_transition(Transition(off, on, turn_on))
sm.add_transition(Transition(on, off, turn_off))

# Process events
sm.process_event(turn_on)
print(sm.current_state)  # State('On')

sm.process_event(turn_off)
print(sm.current_state)  # State('Off')
```

### With Guards and Actions

```python
from src import (
    StateMachine, State, Event, Transition,
    FunctionGuard, FunctionAction
)

# Define states
locked = State("Locked")
unlocked = State("Unlocked")
open_state = State("Open")

# Define events
unlock = Event("Unlock")
open_door = Event("Open")

# Guards
def has_key(from_state, to_state, event, context):
    return context.get("has_key", False)

# Actions
def on_unlock(from_state, to_state, event, context):
    print("Door unlocked!")

# Create state machine
sm = StateMachine(locked)

# Add transitions with guards and actions
sm.add_transition(Transition(
    from_state=locked,
    to_state=unlocked,
    event=unlock,
    guard=FunctionGuard(has_key),
    action=FunctionAction(on_unlock)
))

sm.add_transition(Transition(
    from_state=unlocked,
    to_state=open_state,
    event=open_door
))

# Process with context
context = {"has_key": True}
sm.process_event(unlock, context)  # Door unlocked!
```

### Using Builder Pattern

```python
from src import TransitionBuilder, State, Event

transition = (TransitionBuilder()
    .from_state(State("Disconnected"))
    .to_state(State("Connected"))
    .on(Event("Connect"))
    .when(lambda f, t, e, c: c.get("authorized", False))
    .do(lambda f, t, e, c: print("Connected!"))
    .describe("Establish connection")
    .build())
```

### Hierarchical State Machine

```python
from src import HierarchicalStateMachine, State, HierarchicalState, Event

# Define states
idle = State("Idle")
active = HierarchicalState("Active", use_history=True)
processing = State("Processing")
waiting = State("Waiting")

# Set up hierarchy
active.add_sub_state(processing)
active.add_sub_state(waiting)
active.initial_state = "Processing"

# Create HSM
hsm = HierarchicalStateMachine(idle)
hsm.add_transition(Transition(idle, active, Event("Activate")))

# Process events
hsm.process_event(Event("Activate"))
print(hsm.current_state)  # State('Processing')
print(hsm.state_stack)    # [HierarchicalState('Active'), State('Processing')]
```

## Core Concepts

### States

States represent the possible conditions of your system:

```python
from src import State

# Simple state
idle = State("Idle")

# State with metadata
running = State("Running", speed=100, mode="normal")

# State with actions
active = State("Active")
active.add_entry_action(lambda s, c: print(f"Entering {s.name}"))
active.add_exit_action(lambda s, c: print(f"Exiting {s.name}"))
```

### Events

Events trigger state transitions:

```python
from src import Event

# Simple event
start = Event("Start")

# Event with data
click = Event("Click", x=100, y=200, button="left")
```

### Transitions

Transitions define how the system moves between states:

```python
from src import Transition

transition = Transition(
    from_state=State("Off"),
    to_state=State("On"),
    event=Event("TurnOn"),
    guard=FunctionGuard(lambda f, t, e, c: True),
    action=FunctionAction(lambda f, t, e, c: print("Turning on")),
    description="Turn the light on"
)
```

### Guards

Guards are conditions that must be met for a transition to occur:

```python
from src import FunctionGuard, context_has, state_is

# Function guard
has_permission = FunctionGuard(
    lambda f, t, e, c: c.get("role") == "admin"
)

# Convenience guards
is_admin = context_has("role", "admin")
is_idle = state_is("Idle")

# Combine guards
can_edit = is_admin & context_has("edit_enabled", True)
```

### Actions

Actions are executed during transitions:

```python
from src import (
    FunctionAction, EntryAction, ExitAction, TransitionAction
)

# Function action (receives from, to, event, context)
log = FunctionAction(lambda f, t, e, c: print(f"{f} -> {t}"))

# Entry action (receives state, context)
on_enter = EntryAction(lambda s, c: print(f"Entered {s}"))

# Exit action (receives state, context)
on_exit = ExitAction(lambda s, c: print(f"Left {s}"))

# Transition action (receives from, to, event, context)
on_transition = TransitionAction(lambda f, t, e, c: print("Transitioning"))
```

## API Reference

### StateMachine

- `current_state` - Get current state
- `states` - Get all defined states
- `events` - Get all defined events
- `transitions` - Get all transitions
- `history` - Get history manager
- `context` - Get/set context data
- `add_transition(transition)` - Add a transition
- `process_event(event, context)` - Process an event
- `can_process_event(event)` - Check if event can be processed
- `possible_events()` - Get possible events
- `on_state_change(callback)` - Set state change callback
- `on_transition_failed(callback)` - Set failure callback
- `reset(state)` - Reset to initial state

### HierarchicalStateMachine

- `current_state` - Get current (deepest) state
- `state_stack` - Get full state stack
- `root_state` - Get root state
- `process_event(event, context, bubble)` - Process event (with optional bubbling)
- `enter_sub_state(name)` - Enter a sub-state
- `get_history_state(parent)` - Get history state
- `set_history_state(parent, sub)` - Set history state

### Transition

- `from_state` - Source state
- `to_state` - Target state
- `event` - Triggering event
- `guard` - Guard condition
- `action` - Transition action
- `description` - Human-readable description
- `can_transition(context)` - Check if guard passes
- `execute(context)` - Execute action
- `matches(from_state, event)` - Check if matches

### TransitionBuilder

- `from_state(state)` - Set source state
- `to_state(state)` / `to(state)` - Set target state
- `on(event)` - Set trigger event
- `when(guard)` - Set guard condition
- `do(action)` - Set action
- `describe(description)` - Set description
- `build()` - Build the transition

## Examples

See the `examples/` directory:

- `traffic_light.py` - Simple traffic light state machine
- `order_processing.py` - Order lifecycle management
- `game_ai.py` - Game AI with hierarchical states
- `workflow_engine.py` - Document workflow engine

Run examples:

```bash
cd examples
python traffic_light.py
python order_processing.py
python game_ai.py
python workflow_engine.py
```

## Testing

Run tests:

```bash
cd tests
python -m pytest test_state_machine.py -v
```

## Error Handling

The framework provides specific exception types:

- `StateMachineError` - Base exception
- `TransitionError` - Transition failures
- `GuardRejectedError` - Guard condition rejected
- `InvalidStateError` - Invalid state reference
- `InvalidEventError` - No transition for event
- `ActionError` - Action execution failure
- `ConfigurationError` - Configuration issues

## License

MIT
