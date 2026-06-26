//! # State Entry/Exit Actions
//!
//! Entry and exit actions are hooks that fire when entering or exiting states.
//! They are fundamental to state machine design patterns:
//!
//! - **Entry Actions**: Initialize state-specific resources, set up invariants
//! - **Exit Actions**: Clean up resources, save state, invalidate invariants
//!
//! ## When They Fire
//!
//! - **Entry action** fires AFTER entering a state (after the transition completes)
//! - **Exit action** fires BEFORE exiting a state (before the transition starts)
//!
//! ## Hierarchical Semantics
//!
//! For composite states:
//! - Entry actions fire top-down: parent first, then children
//! - Exit actions fire bottom-up: children first, then parent
//! - Only ONE leaf state is active at a time within a region

use crate::{Event, Result, State};
use std::collections::HashMap;

/// Entry action type alias
pub type StateEntry<S, E> = Box<dyn Fn(&S, &E) -> Result<()> + Send + Sync>;

/// Entry action builder for registering entry actions
pub struct StateEntryBuilder<S: State, E: Event> {
    entries: HashMap<String, StateEntry<S, E>>,
}

impl<S: State, E: Event> StateEntryBuilder<S, E> {
    /// Create a new entry action builder
    pub fn new() -> Self {
        Self {
            entries: HashMap::new(),
        }
    }

    /// Register an entry action for a state
    pub fn register(
        mut self,
        state_id: impl Into<String>,
        action: impl Fn(&S, &E) -> Result<()> + Send + Sync + 'static,
    ) -> Self {
        self.entries.insert(state_id.into(), Box::new(action));
        self
    }

    /// Register multiple entry actions at once
    pub fn register_many(
        mut self,
        actions: Vec<(String, StateEntry<S, E>)>,
    ) -> Self {
        for (id, action) in actions {
            self.entries.insert(id, action);
        }
        self
    }

    /// Get a registered entry action
    pub fn get(&self, state_id: &str) -> Option<&StateEntry<S, E>> {
        self.entries.get(state_id)
    }

    /// Check if an entry action is registered for a state
    pub fn has_entry(&self, state_id: &str) -> bool {
        self.entries.contains_key(state_id)
    }

    /// Get the number of registered entry actions
    pub fn len(&self) -> usize {
        self.entries.len()
    }

    /// Check if no entry actions are registered
    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    /// Build and return the entry action map
    pub fn build(self) -> HashMap<String, StateEntry<S, E>> {
        self.entries
    }
}

impl<S: State, E: Event> Default for StateEntryBuilder<S, E> {
    fn default() -> Self {
        Self::new()
    }
}

/// Exit action type alias
pub type StateExit<S, E> = Box<dyn Fn(&S, &E) -> Result<()> + Send + Sync>;

/// Exit action builder for registering exit actions
pub struct StateExitBuilder<S: State, E: Event> {
    exits: HashMap<String, StateExit<S, E>>,
}

impl<S: State, E: Event> StateExitBuilder<S, E> {
    /// Create a new exit action builder
    pub fn new() -> Self {
        Self {
            exits: HashMap::new(),
        }
    }

    /// Register an exit action for a state
    pub fn register(
        mut self,
        state_id: impl Into<String>,
        action: impl Fn(&S, &E) -> Result<()> + Send + Sync + 'static,
    ) -> Self {
        self.exits.insert(state_id.into(), Box::new(action));
        self
    }

    /// Register multiple exit actions at once
    pub fn register_many(
        mut self,
        actions: Vec<(String, StateExit<S, E>)>,
    ) -> Self {
        for (id, action) in actions {
            self.exits.insert(id, action);
        }
        self
    }

    /// Get a registered exit action
    pub fn get(&self, state_id: &str) -> Option<&StateExit<S, E>> {
        self.exits.get(state_id)
    }

    /// Check if an exit action is registered for a state
    pub fn has_exit(&self, state_id: &str) -> bool {
        self.exits.contains_key(state_id)
    }

    /// Get the number of registered exit actions
    pub fn len(&self) -> usize {
        self.exits.len()
    }

    /// Check if no exit actions are registered
    pub fn is_empty(&self) -> bool {
        self.exits.is_empty()
    }

    /// Build and return the exit action map
    pub fn build(self) -> HashMap<String, StateExit<S, E>> {
        self.exits
    }
}

impl<S: State, E: Event> Default for StateExitBuilder<S, E> {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Debug, Clone, PartialEq, Eq, Hash)]
    enum TestState {
        A,
        B,
        C,
    }

    #[derive(Debug, Clone, PartialEq, Eq, Hash)]
    enum TestEvent {
        Go,
    }

    impl crate::State for TestState {}
    impl crate::Event for TestEvent {}

    #[test]
    fn test_entry_builder_new() {
        let builder: StateEntryBuilder<TestState, TestEvent> = StateEntryBuilder::new();
        assert!(builder.is_empty());
        assert_eq!(builder.len(), 0);
    }

    #[test]
    fn test_entry_builder_register() {
        let builder: StateEntryBuilder<TestState, TestEvent> = StateEntryBuilder::new()
            .register("A", |state: &TestState, event: &TestEvent| {
                println!("Entering {:?} on event {:?}", state, event);
                Ok(())
            });

        assert!(!builder.is_empty());
        assert_eq!(builder.len(), 1);
        assert!(builder.has_entry("A"));
        assert!(!builder.has_entry("B"));
    }

    #[test]
    fn test_entry_builder_get() {
        let builder: StateEntryBuilder<TestState, TestEvent> = StateEntryBuilder::new()
            .register("A", |_: &TestState, _: &TestEvent| Ok(()));

        assert!(builder.get("A").is_some());
        assert!(builder.get("B").is_none());
    }

    #[test]
    fn test_exit_builder_new() {
        let builder: StateExitBuilder<TestState, TestEvent> = StateExitBuilder::new();
        assert!(builder.is_empty());
        assert_eq!(builder.len(), 0);
    }

    #[test]
    fn test_exit_builder_register() {
        let builder: StateExitBuilder<TestState, TestEvent> = StateExitBuilder::new()
            .register("A", |state: &TestState, event: &TestEvent| {
                println!("Exiting {:?} on event {:?}", state, event);
                Ok(())
            });

        assert!(!builder.is_empty());
        assert_eq!(builder.len(), 1);
        assert!(builder.has_exit("A"));
        assert!(!builder.has_exit("B"));
    }

    #[test]
    fn test_exit_builder_get() {
        let builder: StateExitBuilder<TestState, TestEvent> = StateExitBuilder::new()
            .register("A", |_: &TestState, _: &TestEvent| Ok(()));

        assert!(builder.get("A").is_some());
        assert!(builder.get("B").is_none());
    }

    #[test]
    fn test_entry_builder_register_many() {
        let builder: StateEntryBuilder<TestState, TestEvent> = StateEntryBuilder::new()
            .register_many(vec![
                ("A".to_string(), Box::new(|_: &TestState, _: &TestEvent| Ok(()))),
                ("B".to_string(), Box::new(|_: &TestState, _: &TestEvent| Ok(()))),
            ]);

        assert_eq!(builder.len(), 2);
        assert!(builder.has_entry("A"));
        assert!(builder.has_entry("B"));
    }
}
