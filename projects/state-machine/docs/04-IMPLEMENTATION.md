# State Machine Framework - Implementation

## Overview

This document describes the implementation details of the state machine framework, including code structure, algorithms, and implementation decisions.

## Module Implementation

### lib.rs

**Purpose**: Main library entry point, re-exports public types.

**Implementation**:
```rust
pub mod error;
pub mod history;
pub mod state_machine;
pub mod transition;

pub use error::StateMachineError;
pub use history::{HistoryEntry, HistoryManager};
pub use state_machine::StateMachine;
pub use transition::{Guard, Transition, TransitionBuilder};

use std::fmt::Debug;
use std::hash::Hash;

pub trait State: Debug + Clone + PartialEq + Eq + Hash {}
pub trait Event: Debug + Clone + PartialEq + Eq + Hash {}

pub type Result<T> = std::result::Result<T, StateMachineError>;
```

**Key Decisions**:
- Re-export main types for convenience
- Define State and Event traits
- Define Result type alias

### error.rs

**Purpose**: Define error types for the state machine.

**Implementation**:
```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum StateMachineError {
    #[error("No transition defined for state {state:?} with event {event:?}")]
    NoTransition { state: String, event: String },
    
    #[error("Guard condition rejected transition from {from:?} to {to:?}")]
    GuardRejected { from: String, to: String },
    
    #[error("Action execution failed: {reason}")]
    ActionFailed { reason: String },
    
    #[error("Invalid transition from {from:?} to {to:?}")]
    InvalidTransition { from: String, to: String },
    
    #[error("State machine is in an invalid state: {state:?}")]
    InvalidState { state: String },
    
    #[error("State machine error: {0}")]
    Generic(String),
}
```

**Key Decisions**:
- Use `thiserror` for derive macros
- Store formatted strings for debug info
- Comprehensive error variants
- Helper constructors for each error type

### transition.rs

**Purpose**: Define transition types and builder.

**Implementation**:

#### Transition Struct
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

#### Guard and Action Types
```rust
pub type GuardFn<S, E> = Box<dyn Fn(&S, &S, &E) -> bool + Send + Sync>;
pub type ActionFn<S, E> = Box<dyn Fn(&S, &S, &E) -> Result<()> + Send + Sync>;
```

#### Transition Methods
```rust
impl<S: State, E: Event> Transition<S, E> {
    pub fn new(from: S, to: S, event: E) -> Self { /* ... */ }
    pub fn with_guard(mut self, guard: impl Fn(&S, &S, &E) -> bool + Send + Sync + 'static) -> Self { /* ... */ }
    pub fn with_action(mut self, action: impl Fn(&S, &S, &E) -> Result<()> + Send + Sync + 'static) -> Self { /* ... */ }
    pub fn with_description(mut self, description: impl Into<String>) -> Self { /* ... */ }
    pub fn check_guard(&self, event: &E) -> bool { /* ... */ }
    pub fn execute_action(&self, event: &E) -> Result<()> { /* ... */ }
    pub fn matches(&self, state: &S, event: &E) -> bool { /* ... */ }
}
```

#### TransitionBuilder
```rust
pub struct TransitionBuilder<S: State, E: Event> {
    from: Option<S>,
    to: Option<S>,
    event: Option<E>,
    guard: Option<GuardFn<S, E>>,
    action: Option<ActionFn<S, E>>,
    description: Option<String>,
}

impl<S: State, E: Event> TransitionBuilder<S, E> {
    pub fn new() -> Self { /* ... */ }
    pub fn from(mut self, from: S) -> Self { /* ... */ }
    pub fn to(mut self, to: S) -> Self { /* ... */ }
    pub fn on(mut self, event: E) -> Self { /* ... */ }
    pub fn when(mut self, guard: impl Fn(&S, &S, &E) -> bool + Send + Sync + 'static) -> Self { /* ... */ }
    pub fn then(mut self, action: impl Fn(&S, &S, &E) -> Result<()> + Send + Sync + 'static) -> Self { /* ... */ }
    pub fn describe(mut self, description: impl Into<String>) -> Self { /* ... */ }
    pub fn build(self) -> Result<Transition<S, E>> { /* ... */ }
}
```

**Key Decisions**:
- Boxed closures for guards and actions
- Builder pattern for complex transitions
- Fluent API with method chaining

### state_machine.rs

**Purpose**: Core state machine implementation.

**Implementation**:

#### StateMachine Struct
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

#### Creation Methods
```rust
impl<S: State, E: Event> StateMachine<S, E> {
    pub fn new(initial_state: S) -> Self { /* ... */ }
    pub fn new_without_history(initial_state: S) -> Self { /* ... */ }
    pub fn with_history_capacity(mut self, capacity: usize) -> Self { /* ... */ }
    pub fn on_state_change(mut self, callback: impl Fn(&S, &S, &E) + Send + Sync + 'static) -> Self { /* ... */ }
    pub fn on_transition_failed(mut self, callback: impl Fn(&S, &E, &StateMachineError) + Send + Sync + 'static) -> Self { /* ... */ }
}
```

#### Transition Management
```rust
impl<S: State, E: Event> StateMachine<S, E> {
    pub fn add_transition(&mut self, transition: Transition<S, E>) { /* ... */ }
    pub fn add_transitions(&mut self, transitions: Vec<Transition<S, E>>) { /* ... */ }
    pub fn transition_count(&self) -> usize { /* ... */ }
}
```

#### Event Processing
```rust
impl<S: State, E: Event> StateMachine<S, E> {
    pub fn process_event(&mut self, event: E) -> Result<()> { /* ... */ }
    pub fn can_process_event(&self, event: &E) -> bool { /* ... */ }
    pub fn possible_events(&self) -> Vec<&E> { /* ... */ }
}
```

#### State Access
```rust
impl<S: State, E: Event> StateMachine<S, E> {
    pub fn current_state(&self) -> &S { /* ... */ }
    pub fn set_state(&mut self, state: S) { /* ... */ }
}
```

#### History Access
```rust
impl<S: State, E: Event> StateMachine<S, E> {
    pub fn history(&self) -> &HistoryManager<S, E> { /* ... */ }
    pub fn history_mut(&mut self) -> &mut HistoryManager<S, E> { /* ... */ }
    pub fn is_recording_history(&self) -> bool { /* ... */ }
    pub fn set_record_history(&mut self, record: bool) { /* ... */ }
}
```

#### Formatting
```rust
impl<S: State, E: Event> StateMachine<S, E> {
    pub fn format_transitions(&self) -> String { /* ... */ }
    pub fn format_graph(&self) -> String { /* ... */ }
}
```

**Key Decisions**:
- HashMap for O(1) transition lookup
- Vec for ordered storage
- Optional callbacks
- Optional history recording

### history.rs

**Purpose**: Record and query transition history.

**Implementation**:

#### HistoryEntry
```rust
pub struct HistoryEntry<S: State, E: Event> {
    pub from: S,
    pub to: S,
    pub event: E,
    pub timestamp: Instant,
    pub duration: Option<Duration>,
    pub success: bool,
    pub error: Option<String>,
}

impl<S: State, E: Event> HistoryEntry<S, E> {
    pub fn success(from: S, to: S, event: E) -> Self { /* ... */ }
    pub fn failure(from: S, to: S, event: E, error: String) -> Self { /* ... */ }
    pub fn with_duration(mut self, duration: Duration) -> Self { /* ... */ }
    pub fn format(&self) -> String { /* ... */ }
}
```

#### HistoryManager
```rust
pub struct HistoryManager<S: State, E: Event> {
    max_entries: usize,
    entries: VecDeque<HistoryEntry<S, E>>,
}

impl<S: State, E: Event> HistoryManager<S, E> {
    pub fn new(max_entries: usize) -> Self { /* ... */ }
    pub fn push(&mut self, entry: HistoryEntry<S, E>) { /* ... */ }
    pub fn last(&self) -> Option<&HistoryEntry<S, E>> { /* ... */ }
    pub fn len(&self) -> usize { /* ... */ }
    pub fn is_empty(&self) -> bool { /* ... */ }
    pub fn entries(&self) -> &VecDeque<HistoryEntry<S, E>> { /* ... */ }
    pub fn entries_reversed(&self) -> Vec<&HistoryEntry<S, E>> { /* ... */ }
    pub fn entries_for_state(&self, state: &S) -> Vec<&HistoryEntry<S, E>> { /* ... */ }
    pub fn entries_for_event(&self, event: &E) -> Vec<&HistoryEntry<S, E>> { /* ... */ }
    pub fn successful_entries(&self) -> Vec<&HistoryEntry<S, E>> { /* ... */ }
    pub fn failed_entries(&self) -> Vec<&HistoryEntry<S, E>> { /* ... */ }
    pub fn clear(&mut self) { /* ... */ }
    pub fn max_entries(&self) -> usize { /* ... */ }
    pub fn format_all(&self) -> String { /* ... */ }
}
```

**Key Decisions**:
- VecDeque for bounded queue
- O(1) push/pop
- Rich query methods
- Formatting for display

## Algorithms

### Transition Lookup

```rust
fn find_transition(&self, state: &S, event: &E) -> Result<&Transition<S, E>> {
    let key = (state.clone(), event.clone());
    match self.transition_index.get(&key) {
        Some(&index) => Ok(&self.transitions[index]),
        None => Err(StateMachineError::no_transition(state, event)),
    }
}
```

**Time Complexity**: O(1) average case

### Event Processing

```rust
pub fn process_event(&mut self, event: E) -> Result<()> {
    // 1. Find matching transition
    let transition = self.find_transition(&self.current_state, &event)?;
    
    // 2. Check guard condition
    if !transition.check_guard(&event) {
        // Record failure, call callback, return error
    }
    
    // 3. Execute action
    if let Err(e) = transition.execute_action(&event) {
        // Record failure, call callback, return error
    }
    
    // 4. Update state
    self.current_state = transition.to.clone();
    
    // 5. Record history
    if self.record_history {
        self.history.push(/* ... */);
    }
    
    // 6. Notify callbacks
    if let Some(callback) = &self.on_state_change {
        callback(&from_state, &to_state, &event);
    }
    
    Ok(())
}
```

### History Management

```rust
pub fn push(&mut self, entry: HistoryEntry<S, E>) {
    if self.entries.len() >= self.max_entries {
        self.entries.pop_front();
    }
    self.entries.push_back(entry);
}
```

**Time Complexity**: O(1)

## Implementation Decisions

### Why Box<dyn Fn>?

1. **Flexibility**: Allows closures that capture environment
2. **Dynamic dispatch**: Avoids monomorphization bloat
3. **Type erasure**: Simplifies type signatures

### Why HashMap for Transition Index?

1. **O(1) lookup**: Fast event processing
2. **Simple implementation**: Easy to understand
3. **Trade-off**: Memory for speed

### Why VecDeque for History?

1. **O(1) push/pop**: Efficient bounded queue
2. **Good cache locality**: Sequential memory
3. **Simple API**: Easy to use

### Why Generic Types?

1. **Flexibility**: Works with any state/event types
2. **Type safety**: Compile-time checks
3. **No runtime overhead**: Zero-cost abstractions

### Why thiserror?

1. **Derive macros**: Less boilerplate
2. **Error messages**: Automatic formatting
3. **Standard library**: Compatible with std::error::Error

## Error Handling

### Error Propagation

```rust
pub fn process_event(&mut self, event: E) -> Result<()> {
    let transition = self.find_transition(&self.current_state, &event)?;
    
    if !transition.check_guard(&event) {
        return Err(StateMachineError::guard_rejected(/* ... */));
    }
    
    if let Err(e) = transition.execute_action(&event) {
        return Err(e);
    }
    
    // ...
    Ok(())
}
```

### Error Recovery

```rust
match sm.process_event(event) {
    Ok(_) => { /* Success */ }
    Err(StateMachineError::NoTransition { .. }) => { /* Handle */ }
    Err(StateMachineError::GuardRejected { .. }) => { /* Handle */ }
    Err(StateMachineError::ActionFailed { .. }) => { /* Handle */ }
    Err(e) => { /* Handle other errors */ }
}
```

## Performance Optimizations

### Transition Index

- HashMap for O(1) lookup
- Trade-off: memory for speed

### History Bounding

- VecDeque with max_entries
- O(1) push/pop
- Bounded memory usage

### Boxed Closures

- Avoid monomorphization bloat
- Dynamic dispatch overhead (minimal)

## Testing Strategy

### Unit Tests

- Test each module independently
- Test edge cases
- Test error conditions

### Integration Tests

- Test complete workflows
- Test callbacks
- Test history recording

### Examples

- Real-world use cases
- Demonstrate features
- Serve as documentation

## Conclusion

The implementation focuses on:
- **Performance**: O(1) lookups, bounded history
- **Usability**: Builder pattern, sensible defaults
- **Observability**: Callbacks, history recording
- **Extensibility**: Generic types, optional features
- **Thread Safety**: Send + Sync support
