# State Machine Framework - Architecture

## Overview

This document describes the architecture of the state machine framework, including the module structure, data flow, and design decisions.

## Module Structure

```
state-machine/
├── src/
│   ├── lib.rs           # Main library entry point, re-exports
│   ├── error.rs         # Error types
│   ├── state_machine.rs # Core state machine implementation
│   ├── transition.rs    # Transition types and builder
│   └── history.rs       # History recording
├── tests/
│   └── integration_tests.rs
├── examples/
│   ├── traffic_light.rs
│   └── order_processing.rs
└── docs/
    ├── 01-RESEARCH.md
    ├── 02-ARCHITECTURE.md
    ├── 03-DESIGN.md
    ├── 04-IMPLEMENTATION.md
    └── 05-DEVELOPMENT.md
```

## Core Components

### 1. State and Event Traits

```rust
pub trait State: Debug + Clone + PartialEq + Eq + Hash {}
pub trait Event: Debug + Clone + PartialEq + Eq + Hash {}
```

**Purpose**: Define the requirements for state and event types.

**Design Decisions**:
- `Debug`: For logging and error messages
- `Clone`: For copying state values during transitions
- `PartialEq + Eq`: For state comparison
- `Hash`: For use in HashMap-based transition index

### 2. Transition

```rust
pub struct Transition<S: State, E: Event> {
    pub from: S,
    pub to: S,
    pub event: E,
    pub guard: Option<GuardFn<S, E>>,
    pub action: Option<ActionFn<S, E>>,
    pub description: Option<String>,
}
```

**Purpose**: Define a state transition with optional guard and action.

**Design Decisions**:
- Generic over state and event types
- Optional guard for conditional transitions
- Optional action for side effects
- Description for documentation

### 3. StateMachine

```rust
pub struct StateMachine<S: State, E: Event> {
    current_state: S,
    transitions: Vec<Transition<S, E>>,
    transition_index: HashMap<(S, E), usize>,
    history: HistoryManager<S, E>,
    record_history: bool,
    on_state_change: Option<Box<dyn Fn(&S, &S, &E) + Send + Sync>>,
    on_transition_failed: Option<Box<dyn Fn(&S, &E, &StateMachineError) + Send + Sync>>,
}
```

**Purpose**: Core state machine implementation.

**Design Decisions**:
- `current_state`: Tracks the current state
- `transitions`: Vec for ordered storage
- `transition_index`: HashMap for O(1) lookup
- `history`: Optional history recording
- Callbacks for observability

### 4. HistoryManager

```rust
pub struct HistoryManager<S: State, E: Event> {
    max_entries: usize,
    entries: VecDeque<HistoryEntry<S, E>>,
}
```

**Purpose**: Record and query transition history.

**Design Decisions**:
- VecDeque for efficient bounded queue
- Configurable max entries
- Query methods for analysis

## Data Flow

### Event Processing Flow

```
Event Input
    │
    ▼
┌─────────────────┐
│ Find Transition  │
│ (HashMap lookup) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Check Guard      │
│ (if exists)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Execute Action   │
│ (if exists)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update State     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Record History   │
│ (if enabled)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Notify Callbacks │
└─────────────────┘
```

### Transition Lookup

```
(S, E) ──► HashMap ──► Index ──► Vec<Transition>
```

**Why HashMap?**
- O(1) average case lookup
- Fast event processing
- Trade-off: memory for speed

## Type System

### Generic Parameters

```rust
StateMachine<S: State, E: Event>
```

- `S`: State type (enum, struct, etc.)
- `E`: Event type (enum, struct, etc.)

### Type Constraints

```rust
pub trait State: Debug + Clone + PartialEq + Eq + Hash {}
pub trait Event: Debug + Clone + PartialEq + Eq + Hash {}
```

**Why these constraints?**
- `Debug`: Logging, error messages
- `Clone`: Copying values
- `PartialEq + Eq`: Comparison
- `Hash`: HashMap keys

## Error Handling

### Error Types

```rust
pub enum StateMachineError {
    NoTransition { state: String, event: String },
    GuardRejected { from: String, to: String },
    ActionFailed { reason: String },
    InvalidTransition { from: String, to: String },
    InvalidState { state: String },
    Generic(String),
}
```

**Design Decisions**:
- Use `thiserror` for derive macros
- Store formatted strings for debug info
- Comprehensive error variants

### Error Propagation

```rust
pub type Result<T> = std::result::Result<T, StateMachineError>;
```

## Callbacks

### State Change Callback

```rust
Box<dyn Fn(&S, &S, &E) + Send + Sync>
```

- Called after successful transition
- Receives: from_state, to_state, event
- Thread-safe with Send + Sync

### Transition Failed Callback

```rust
Box<dyn Fn(&S, &E, &StateMachineError) + Send + Sync>
```

- Called when transition fails
- Receives: current_state, event, error
- Thread-safe with Send + Sync

## Performance Considerations

### Time Complexity

| Operation | Complexity |
|-----------|------------|
| Add transition | O(1) |
| Process event | O(1) average |
| Find transition | O(1) average |
| Record history | O(1) |
| Query history | O(n) |

### Space Complexity

| Component | Space |
|-----------|-------|
| Transitions | O(n) |
| Transition index | O(n) |
| History | O(k) where k = max_entries |

### Optimizations

1. **HashMap for transitions**: Fast lookup
2. **VecDeque for history**: Efficient bounded queue
3. **Boxed closures**: Avoid monomorphization bloat

## Thread Safety

### Send + Sync

All public types are Send + Sync:
- StateMachine requires Send + Sync for callbacks
- HistoryManager is Send + Sync
- Transitions are Send + Sync

### Shared State

For shared state machines:
```rust
use std::sync::{Arc, Mutex};

let sm = Arc::new(Mutex::new(StateMachine::new(initial_state)));
```

## Extensibility

### Adding New Features

1. **New transition types**: Extend Transition struct
2. **New history queries**: Add methods to HistoryManager
3. **New callbacks**: Add callback fields to StateMachine
4. **New error types**: Add variants to StateMachineError

### Custom Implementations

Users can implement State and Event for any type:
```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum MyState { /* ... */ }

impl State for MyState {}
```

## Testing Strategy

### Unit Tests

- Test each module independently
- Mock external dependencies
- Test edge cases

### Integration Tests

- Test complete workflows
- Test callbacks
- Test error handling

### Examples

- Real-world use cases
- Demonstrate features
- Serve as documentation

## Future Enhancements

### Possible Additions

1. **Hierarchical states**: States with sub-states
2. **Parallel states**: Multiple active states
3. **State charts**: Visual state machine definition
4. **Serialization**: Save/load state machines
5. **Async support**: Async guards and actions
6. **Metrics**: Transition counts, timing

### Backward Compatibility

- Add new features with defaults
- Don't break existing API
- Use feature flags for experimental features

## Conclusion

The architecture is designed to be:
- **Generic**: Works with any state/event types
- **Efficient**: O(1) lookups, bounded history
- **Observable**: Callbacks for monitoring
- **Extensible**: Easy to add features
- **Thread-safe**: Send + Sync support
