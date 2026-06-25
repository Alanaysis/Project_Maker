# State Machine Framework

A generic state machine framework for Rust, supporting state transitions, event-driven architecture, and history recording.

## Features

- **Generic State & Event Types**: Works with any types that implement the `State` and `Event` traits
- **Event-Driven Architecture**: Process events to trigger state transitions
- **Guard Conditions**: Optional conditions that must be met for transitions to occur
- **Transition Actions**: Execute side effects when transitions happen
- **History Recording**: Track all state transitions with timestamps and durations
- **Transition Graph**: Visualize the state machine's structure
- **Builder Pattern**: Easy-to-use API for defining transitions
- **Callbacks**: React to state changes and transition failures
- **Error Handling**: Comprehensive error types for different failure scenarios

## Quick Start

Add to your `Cargo.toml`:

```toml
[dependencies]
state-machine = { path = "../state-machine" }
```

### Basic Usage

```rust
use state_machine::{StateMachine, State, Event, Transition};

// Define your states
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum LightState {
    Off,
    On,
}

// Define your events
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum LightEvent {
    TurnOn,
    TurnOff,
}

// Implement the required traits
impl State for LightState {}
impl Event for LightEvent {}

fn main() {
    // Create a state machine
    let mut sm = StateMachine::new(LightState::Off);

    // Add transitions
    sm.add_transition(Transition::new(
        LightState::Off,
        LightState::On,
        LightEvent::TurnOn,
    ));
    sm.add_transition(Transition::new(
        LightState::On,
        LightState::Off,
        LightEvent::TurnOff,
    ));

    // Process events
    sm.process_event(LightEvent::TurnOn).unwrap();
    assert_eq!(sm.current_state(), &LightState::On);

    sm.process_event(LightEvent::TurnOff).unwrap();
    assert_eq!(sm.current_state(), &LightState::Off);
}
```

### With Guards and Actions

```rust
use state_machine::{StateMachine, State, Event, Transition};

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum DoorState {
    Locked,
    Unlocked,
    Open,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum DoorEvent {
    Unlock,
    Lock,
    Open,
    Close,
}

impl State for DoorState {}
impl Event for DoorEvent {}

fn main() {
    let mut sm = StateMachine::new(DoorState::Locked);

    // Transition with guard and action
    sm.add_transition(
        Transition::new(DoorState::Locked, DoorState::Unlocked, DoorEvent::Unlock)
            .with_guard(|_from, _to, _event| {
                // Check if key is valid
                true
            })
            .with_action(|_from, _to, _event| {
                println!("Door unlocked!");
                Ok(())
            })
            .with_description("Unlock the door"),
    );

    sm.process_event(DoorEvent::Unlock).unwrap();
}
```

### Using the Builder Pattern

```rust
use state_machine::{StateMachine, State, Event, TransitionBuilder};

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum ConnectionState {
    Disconnected,
    Connecting,
    Connected,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum ConnectionEvent {
    Connect,
    Connected,
    Disconnect,
}

impl State for ConnectionState {}
impl Event for ConnectionEvent {}

fn main() {
    let mut sm = StateMachine::new(ConnectionState::Disconnected);

    let transition = TransitionBuilder::new()
        .from(ConnectionState::Disconnected)
        .to(ConnectionState::Connecting)
        .on(ConnectionEvent::Connect)
        .describe("Initiate connection")
        .build()
        .unwrap();

    sm.add_transition(transition);
}
```

## Core Concepts

### States

States represent the possible conditions of your system. They must implement:
- `Debug` - For debugging output
- `Clone` - For copying state values
- `PartialEq` + `Eq` - For comparison
- `Hash` - For use in hash maps

### Events

Events trigger state transitions. They must implement the same traits as states.

### Transitions

A transition defines:
- **From**: The source state
- **To**: The target state
- **Event**: The trigger event
- **Guard**: Optional condition that must be true
- **Action**: Optional side effect to execute
- **Description**: Optional human-readable description

### Guards

Guards are conditions that must be met for a transition to occur:

```rust
Transition::new(from_state, to_state, event)
    .with_guard(|from, to, event| {
        // Return true to allow transition
        // Return false to reject transition
        true
    })
```

### Actions

Actions are executed when a transition occurs:

```rust
Transition::new(from_state, to_state, event)
    .with_action(|from, to, event| {
        // Perform side effects
        // Return Ok(()) on success, Err(...) on failure
        Ok(())
    })
```

### History

The state machine records all transitions:

```rust
let sm = StateMachine::new(initial_state)
    .with_history_capacity(100);

// After processing events...
let history = sm.history();
println!("Total transitions: {}", history.len());
println!("Successful: {}", history.successful_entries().len());
println!("Failed: {}", history.failed_entries().len());
```

## API Reference

### `StateMachine<S, E>`

- `new(initial_state: S)` - Create a new state machine
- `new_without_history(initial_state: S)` - Create without history recording
- `with_history_capacity(capacity: usize)` - Set history capacity
- `on_state_change(callback)` - Set state change callback
- `on_transition_failed(callback)` - Set failure callback
- `add_transition(transition)` - Add a transition
- `add_transitions(transitions)` - Add multiple transitions
- `process_event(event)` - Process an event
- `current_state()` - Get current state
- `set_state(state)` - Set state directly
- `can_process_event(event)` - Check if event can be processed
- `possible_events()` - Get possible events from current state
- `history()` - Get history manager
- `format_transitions()` - Format all transitions
- `format_graph()` - Format transition graph

### `Transition<S, E>`

- `new(from, to, event)` - Create a new transition
- `with_guard(guard)` - Add guard condition
- `with_action(action)` - Add action
- `with_description(desc)` - Add description

### `TransitionBuilder<S, E>`

- `new()` - Create builder
- `from(state)` - Set source state
- `to(state)` - Set target state
- `on(event)` - Set trigger event
- `when(guard)` - Set guard condition
- `then(action)` - Set action
- `describe(desc)` - Set description
- `build()` - Build the transition

### `HistoryManager<S, E>`

- `new(max_entries)` - Create history manager
- `push(entry)` - Add entry
- `last()` - Get most recent entry
- `len()` - Get number of entries
- `is_empty()` - Check if empty
- `entries()` - Get all entries
- `entries_reversed()` - Get entries newest first
- `entries_for_state(state)` - Get entries for a state
- `entries_for_event(event)` - Get entries for an event
- `successful_entries()` - Get successful entries
- `failed_entries()` - Get failed entries
- `clear()` - Clear all entries
- `format_all()` - Format all entries

## Examples

See the `examples/` directory for complete examples:

- `traffic_light.rs` - Simple traffic light state machine
- `order_processing.rs` - Complex order processing workflow

Run examples with:

```bash
cargo run --example traffic_light
cargo run --example order_processing
```

## Testing

Run tests with:

```bash
cargo test
```

## License

MIT
