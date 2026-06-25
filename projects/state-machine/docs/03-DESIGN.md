# State Machine Framework - Design

## Overview

This document describes the detailed design of the state machine framework, including API design, patterns, and implementation details.

## API Design

### StateMachine Creation

```rust
// Basic creation
let sm = StateMachine::new(initial_state);

// Without history
let sm = StateMachine::new_without_history(initial_state);

// With history capacity
let sm = StateMachine::new(initial_state)
    .with_history_capacity(100);

// With callbacks
let sm = StateMachine::new(initial_state)
    .on_state_change(|from, to, event| { /* ... */ })
    .on_transition_failed(|state, event, error| { /* ... */ });
```

**Design Decisions**:
- Builder pattern for configuration
- Sensible defaults (history enabled, capacity 100)
- Optional callbacks

### Adding Transitions

```rust
// Simple transition
sm.add_transition(Transition::new(from, to, event));

// With guard and action
sm.add_transition(
    Transition::new(from, to, event)
        .with_guard(|from, to, event| true)
        .with_action(|from, to, event| Ok(()))
        .with_description("Transition description")
);

// Using builder
let transition = TransitionBuilder::new()
    .from(from)
    .to(to)
    .on(event)
    .when(|from, to, event| true)
    .then(|from, to, event| Ok(()))
    .describe("Transition description")
    .build()?;

sm.add_transition(transition);

// Multiple transitions
sm.add_transitions(vec![t1, t2, t3]);
```

**Design Decisions**:
- Two ways to create transitions (direct and builder)
- Guard and action are optional
- Description for documentation

### Processing Events

```rust
// Process event
sm.process_event(event)?;

// Check if event can be processed
if sm.can_process_event(&event) {
    sm.process_event(event)?;
}

// Get possible events
let events = sm.possible_events();
```

**Design Decisions**:
- Returns Result for error handling
- Can check before processing
- Can query possible events

### Accessing State

```rust
// Get current state
let state = sm.current_state();

// Set state directly
sm.set_state(new_state);
```

**Design Decisions**:
- Reference to current state
- Direct state setting (bypasses transitions)

### History

```rust
// Get history manager
let history = sm.history();

// Query history
history.len();
history.last();
history.entries();
history.entries_reversed();
history.entries_for_state(&state);
history.entries_for_event(&event);
history.successful_entries();
history.failed_entries();

// Format history
history.format_all();
```

**Design Decisions**:
- Rich query methods
- Filtering by state, event, success/failure
- Formatting for display

### Formatting

```rust
// Format transitions
sm.format_transitions();

// Format graph
sm.format_graph();
```

**Design Decisions**:
- Human-readable output
- Graph visualization

## Transition Design

### Transition Structure

```rust
pub struct Transition<S: State, E: Event> {
    pub from: S,           // Source state
    pub to: S,             // Target state
    pub event: E,          // Trigger event
    pub guard: Option<GuardFn<S, E>>,   // Guard condition
    pub action: Option<ActionFn<S, E>>, // Action to execute
    pub description: Option<String>,     // Description
}
```

### Guard Function

```rust
pub type GuardFn<S, E> = Box<dyn Fn(&S, &S, &E) -> bool + Send + Sync>;
```

**Parameters**:
- `from`: Source state
- `to`: Target state
- `event`: Trigger event

**Returns**: `bool` - true to allow, false to reject

### Action Function

```rust
pub type ActionFn<S, E> = Box<dyn Fn(&S, &S, &E) -> Result<()> + Send + Sync>;
```

**Parameters**:
- `from`: Source state
- `to`: Target state
- `event`: Trigger event

**Returns**: `Result<()>` - Ok on success, Err on failure

### Transition Matching

```rust
pub fn matches(&self, state: &S, event: &E) -> bool {
    self.from == *state && self.event == *event
}
```

**Design Decisions**:
- Match on (state, event) pair
- O(1) comparison

## History Design

### History Entry

```rust
pub struct HistoryEntry<S: State, E: Event> {
    pub from: S,              // Source state
    pub to: S,                // Target state
    pub event: E,             // Trigger event
    pub timestamp: Instant,   // When it happened
    pub duration: Option<Duration>, // How long it took
    pub success: bool,        // Whether it succeeded
    pub error: Option<String>, // Error message if failed
}
```

### History Manager

```rust
pub struct HistoryManager<S: State, E: Event> {
    max_entries: usize,
    entries: VecDeque<HistoryEntry<S, E>>,
}
```

**Design Decisions**:
- VecDeque for bounded queue
- O(1) push/pop
- Configurable max entries

### Entry Creation

```rust
// Successful entry
HistoryEntry::success(from, to, event);

// Failed entry
HistoryEntry::failure(from, to, event, error_message);

// With duration
entry.with_duration(duration);
```

## Error Design

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

### Error Constructors

```rust
StateMachineError::no_transition(&state, &event)
StateMachineError::guard_rejected(&from, &to)
StateMachineError::action_failed("reason")
StateMachineError::invalid_transition(&from, &to)
StateMachineError::invalid_state(&state)
StateMachineError::generic("message")
```

**Design Decisions**:
- Use `thiserror` for derive macros
- Store formatted strings
- Comprehensive error variants

## Callback Design

### State Change Callback

```rust
let sm = StateMachine::new(initial_state)
    .on_state_change(|from, to, event| {
        println!("{:?} -> {:?}", from, to);
    });
```

**When called**: After successful transition

### Transition Failed Callback

```rust
let sm = StateMachine::new(initial_state)
    .on_transition_failed(|state, event, error| {
        eprintln!("Failed: {}", error);
    });
```

**When called**: When transition fails

## Builder Pattern Design

### TransitionBuilder

```rust
let transition = TransitionBuilder::new()
    .from(from)
    .to(to)
    .on(event)
    .when(guard)
    .then(action)
    .describe(description)
    .build()?;
```

**Design Decisions**:
- Fluent API
- Required fields: from, to, on
- Optional fields: when, then, describe
- Returns Result

## Thread Safety Design

### Send + Sync

All public types implement Send + Sync:
- StateMachine requires Send + Sync for callbacks
- HistoryManager is Send + Sync
- Transitions are Send + Sync

### Shared State

```rust
use std::sync::{Arc, Mutex};

let sm = Arc::new(Mutex::new(StateMachine::new(initial_state)));

// Clone for sharing
let sm_clone = Arc::clone(&sm);

// Use in thread
let handle = std::thread::spawn(move || {
    let mut sm = sm_clone.lock().unwrap();
    sm.process_event(event).unwrap();
});
```

## Performance Design

### Time Complexity

| Operation | Complexity |
|-----------|------------|
| new() | O(1) |
| add_transition() | O(1) |
| process_event() | O(1) average |
| can_process_event() | O(1) |
| possible_events() | O(n) |
| history queries | O(n) |

### Space Complexity

| Component | Space |
|-----------|-------|
| Transitions | O(n) |
| Transition index | O(n) |
| History | O(k) |

### Optimizations

1. **HashMap for transitions**: Fast lookup
2. **VecDeque for history**: Efficient bounded queue
3. **Boxed closures**: Avoid monomorphization bloat

## Extensibility Design

### Adding New Features

1. **New transition types**: Extend Transition struct
2. **New history queries**: Add methods to HistoryManager
3. **New callbacks**: Add callback fields to StateMachine
4. **New error types**: Add variants to StateMachineError

### Custom Implementations

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum MyState {
    State1,
    State2,
}

impl State for MyState {}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum MyEvent {
    Event1,
    Event2,
}

impl Event for MyEvent {}
```

## Testing Design

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

## Documentation Design

### API Documentation

- Doc comments on all public items
- Examples in doc comments
- Module-level documentation

### User Guide

- README with quick start
- Examples directory
- Documentation directory

### Developer Guide

- Architecture document
- Design document
- Implementation document

## Conclusion

The design focuses on:
- **Usability**: Builder pattern, sensible defaults
- **Performance**: O(1) lookups, bounded history
- **Observability**: Callbacks, history recording
- **Extensibility**: Generic types, optional features
- **Thread Safety**: Send + Sync support
