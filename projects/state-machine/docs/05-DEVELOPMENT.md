# State Machine Framework - Development Guide

## Overview

This document provides guidelines for developing and contributing to the state machine framework.

## Getting Started

### Prerequisites

- Rust 1.70+ (2021 edition)
- Cargo

### Building

```bash
cd projects/state-machine
cargo build
```

### Testing

```bash
cargo test
```

### Running Examples

```bash
cargo run --example traffic_light
cargo run --example order_processing
```

## Project Structure

```
state-machine/
├── src/
│   ├── lib.rs           # Main library entry point
│   ├── error.rs         # Error types
│   ├── state_machine.rs # Core implementation
│   ├── transition.rs    # Transition types
│   └── history.rs       # History recording
├── tests/
│   └── integration_tests.rs
├── examples/
│   ├── traffic_light.rs
│   └── order_processing.rs
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-DESIGN.md
│   ├── 04-IMPLEMENTATION.md
│   └── 05-DEVELOPMENT.md
├── Cargo.toml
└── README.md
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature
```

### 2. Make Changes

- Write code
- Add tests
- Update documentation

### 3. Run Tests

```bash
cargo test
```

### 4. Check Code Quality

```bash
# Format code
cargo fmt

# Run linter
cargo clippy

# Check documentation
cargo doc --open
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: your feature description"
```

### 6. Push and Create PR

```bash
git push origin feature/your-feature
```

## Code Style

### Formatting

Use `cargo fmt` to format code:
```bash
cargo fmt
```

### Linting

Use `cargo clippy` to check for issues:
```bash
cargo clippy
```

### Documentation

- Add doc comments to all public items
- Use `///` for item documentation
- Use `//!` for module documentation
- Include examples in doc comments

Example:
```rust
/// Process an event and potentially transition to a new state.
///
/// # Arguments
///
/// * `event` - The event to process
///
/// # Returns
///
/// * `Ok(())` if the transition was successful
/// * `Err(StateMachineError)` if the transition failed
///
/// # Examples
///
/// ```
/// use state_machine::{StateMachine, State, Event, Transition};
///
/// #[derive(Debug, Clone, PartialEq, Eq, Hash)]
/// enum MyState { A, B }
/// #[derive(Debug, Clone, PartialEq, Eq, Hash)]
/// enum MyEvent { GoToB }
/// impl State for MyState {}
/// impl Event for MyEvent {}
///
/// let mut sm = StateMachine::new(MyState::A);
/// sm.add_transition(Transition::new(MyState::A, MyState::B, MyEvent::GoToB));
/// sm.process_event(MyEvent::GoToB).unwrap();
/// assert_eq!(sm.current_state(), &MyState::B);
/// ```
pub fn process_event(&mut self, event: E) -> Result<()> {
    // Implementation
}
```

## Testing Guidelines

### Unit Tests

- Test each module independently
- Test edge cases
- Test error conditions
- Use descriptive test names

Example:
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_process_event_success() {
        // Test successful event processing
    }

    #[test]
    fn test_process_event_no_transition() {
        // Test error when no transition exists
    }

    #[test]
    fn test_process_event_guard_rejected() {
        // Test guard rejection
    }
}
```

### Integration Tests

- Test complete workflows
- Test callbacks
- Test history recording
- Test error handling

Example:
```rust
#[test]
fn test_complete_workflow() {
    let mut sm = StateMachine::new(State::Initial);
    
    // Add transitions
    sm.add_transition(/* ... */);
    
    // Process events
    sm.process_event(Event::Start).unwrap();
    sm.process_event(Event::Complete).unwrap();
    
    // Verify state
    assert_eq!(sm.current_state(), &State::Complete);
    
    // Verify history
    assert_eq!(sm.history().len(), 2);
}
```

### Test Coverage

Aim for high test coverage:
- All public methods
- All error conditions
- All edge cases
- All callback scenarios

## Adding New Features

### 1. Identify the Feature

- What problem does it solve?
- Is it backward compatible?
- Does it require new dependencies?

### 2. Design the API

- Follow existing patterns
- Use builder pattern where appropriate
- Add sensible defaults

### 3. Implement the Feature

- Write the code
- Add tests
- Update documentation

### 4. Test the Feature

- Run unit tests
- Run integration tests
- Run examples
- Check for regressions

### 5. Document the Feature

- Update README
- Add doc comments
- Add examples
- Update changelog

## Common Tasks

### Adding a New Error Type

1. Add variant to `StateMachineError` in `error.rs`
2. Add constructor method
3. Add tests
4. Update documentation

### Adding a New Callback

1. Add field to `StateMachine` in `state_machine.rs`
2. Add setter method
3. Call callback in appropriate places
4. Add tests
5. Update documentation

### Adding a New History Query

1. Add method to `HistoryManager` in `history.rs`
2. Add tests
3. Update documentation

### Adding a New Example

1. Create file in `examples/`
2. Add to `Cargo.toml` `[[example]]` section
3. Test the example
4. Update README

## Debugging

### Enable Logging

Add to your code:
```rust
env_logger::init();
```

Run with:
```bash
RUST_LOG=debug cargo run --example your_example
```

### Debug Output

Use `{:?}` for debug output:
```rust
println!("State machine: {:?}", sm);
println!("Transition: {:?}", transition);
println!("History: {:?}", history);
```

### Common Issues

1. **No transition found**: Check if transition is added correctly
2. **Guard rejected**: Check guard condition
3. **Action failed**: Check action implementation
4. **Type mismatch**: Ensure state/event types match

## Performance Profiling

### Benchmarking

Use `criterion` for benchmarking:
```toml
[dev-dependencies]
criterion = "0.5"

[[bench]]
name = "state_machine_bench"
harness = false
```

### Profiling

Use `perf` or `flamegraph` for profiling:
```bash
cargo build --release
perf record --call-graph dwarf target/release/your_binary
perf report
```

## Release Process

### 1. Update Version

Update `Cargo.toml`:
```toml
[package]
version = "0.2.0"
```

### 2. Update Changelog

Add entry to CHANGELOG.md

### 3. Run Tests

```bash
cargo test
```

### 4. Build Release

```bash
cargo build --release
```

### 5. Publish

```bash
cargo publish
```

## Contributing

### Guidelines

1. Follow code style
2. Add tests
3. Update documentation
4. Keep commits small and focused
5. Write clear commit messages

### Commit Messages

Use conventional commits:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for tests
- `refactor:` for refactoring
- `chore:` for maintenance

### Pull Requests

1. Create feature branch
2. Make changes
3. Run tests
4. Create PR
5. Address review comments
6. Merge

## Resources

- [Rust Book](https://doc.rust-lang.org/book/)
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/)
- [Cargo Book](https://doc.rust-lang.org/cargo/)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)

## Conclusion

This development guide provides:
- Getting started instructions
- Development workflow
- Code style guidelines
- Testing guidelines
- Common tasks
- Debugging tips
- Release process
- Contributing guidelines
