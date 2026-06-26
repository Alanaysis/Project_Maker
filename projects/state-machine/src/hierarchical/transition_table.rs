//! # Hierarchical Transition Table
//!
//! The transition table manages state transitions for hierarchical state machines.
//! It extends the flat transition table with support for:
//!
//! - **Inherited transitions**: Transitions from parent states apply to all children
//! - **Local transitions**: Transitions that stay within a region
//! - **External transitions**: Transitions that exit a composite state
//! - **Internal transitions**: Transitions that change substate without exiting parent

use crate::transition::Transition;
use crate::{Event, State};
use std::collections::HashMap;
use std::fmt::Debug;

/// A transition table that supports hierarchical state machines
///
/// The transition table stores all valid state transitions and provides
/// fast lookup by (source_state, event) pairs. For hierarchical machines,
/// it also supports inherited transitions from parent states.
#[derive(Debug)]
pub struct HierarchicalTransitionTable<S: State, E: Event> {
    /// All transitions stored by index
    transitions: Vec<Transition<S, E>>,
    /// Index: (from_state, event) -> transition index
    index: HashMap<(String, String), usize>,
    /// Inherited transitions (from parent states to children)
    inherited_transitions: Vec<Transition<S, E>>,
}

impl<S: State, E: Event> HierarchicalTransitionTable<S, E> {
    /// Create a new empty transition table
    pub fn new() -> Self {
        Self {
            transitions: Vec::new(),
            index: HashMap::new(),
            inherited_transitions: Vec::new(),
        }
    }

    /// Add a transition to the table
    pub fn add_transition(&mut self, transition: Transition<S, E>) {
        let key = (format!("{:?}", transition.from), format!("{:?}", transition.event));
        let idx = self.transitions.len();
        self.index.insert(key, idx);
        self.transitions.push(transition);
    }

    /// Add multiple transitions
    pub fn add_transitions(&mut self, transitions: Vec<Transition<S, E>>) {
        for t in transitions {
            self.add_transition(t);
        }
    }

    /// Add an inherited transition (from parent to child states)
    pub fn add_inherited_transition(&mut self, transition: Transition<S, E>) {
        self.inherited_transitions.push(transition);
    }

    /// Find a transition for the given state and event
    pub fn find_transition(&self, state: &S, event: &E) -> Result<&Transition<S, E>, crate::error::StateMachineError> {
        let key = (format!("{:?}", state), format!("{:?}", event));

        // First check direct transitions
        if let Some(&idx) = self.index.get(&key) {
            return Ok(&self.transitions[idx]);
        }

        // Then check inherited transitions
        for transition in &self.inherited_transitions {
            if format!("{:?}", transition.from) == format!("{:?}", state) {
                return Ok(transition);
            }
        }

        Err(crate::error::StateMachineError::NoTransition {
            state: format!("{:?}", state),
            event: format!("{:?}", event),
        })
    }

    /// Check if a transition exists for the given state and event
    pub fn has_transition(&self, state: &S, event: &E) -> bool {
        let key = (format!("{:?}", state), format!("{:?}", event));
        self.index.contains_key(&key)
            || self.inherited_transitions.iter().any(|t| {
                format!("{:?}", t.from) == format!("{:?}", state)
                    && format!("{:?}", t.event) == format!("{:?}", event)
            })
    }

    /// Get all transitions
    pub fn all_transitions(&self) -> &[Transition<S, E>] {
        &self.transitions
    }

    /// Get transitions from a specific state
    pub fn transitions_from(&self, state: &S) -> Vec<&Transition<S, E>> {
        self.transitions
            .iter()
            .filter(|t| format!("{:?}", t.from) == format!("{:?}", state))
            .collect()
    }

    /// Get the number of transitions
    pub fn count(&self) -> usize {
        self.transitions.len()
    }

    /// Format all transitions as a string
    pub fn format_all(&self) -> String {
        self.transitions
            .iter()
            .map(|t| {
                format!(
                    "{:?} --({:?})--> {:?}",
                    t.from, t.event, t.to
                )
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    /// Format inherited transitions
    pub fn format_inherited(&self) -> String {
        self.inherited_transitions
            .iter()
            .map(|t| {
                format!(
                    "[inherited] {:?} --({:?})--> {:?}",
                    t.from, t.event, t.to
                )
            })
            .collect::<Vec<_>>()
            .join("\n")
    }
}

impl<S: State, E: Event> Default for HierarchicalTransitionTable<S, E> {
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
        GoToB,
        GoToC,
        GoToA,
    }

    impl crate::State for TestState {}
    impl crate::Event for TestEvent {}

    #[test]
    fn test_new_table() {
        let table: HierarchicalTransitionTable<TestState, TestEvent> = HierarchicalTransitionTable::new();
        assert_eq!(table.count(), 0);
    }

    #[test]
    fn test_add_transition() {
        let mut table = HierarchicalTransitionTable::new();
        table.add_transition(Transition::new(
            TestState::A, TestState::B, TestEvent::GoToB,
        ));
        assert_eq!(table.count(), 1);
    }

    #[test]
    fn test_find_transition() {
        let mut table = HierarchicalTransitionTable::new();
        table.add_transition(Transition::new(
            TestState::A, TestState::B, TestEvent::GoToB,
        ));

        let result = table.find_transition(&TestState::A, &TestEvent::GoToB);
        assert!(result.is_ok());
        assert_eq!(result.unwrap().to.clone(), TestState::B);
    }

    #[test]
    fn test_find_transition_not_found() {
        let table: HierarchicalTransitionTable<TestState, TestEvent> = HierarchicalTransitionTable::new();
        let result = table.find_transition(&TestState::A, &TestEvent::GoToB);
        assert!(result.is_err());
    }

    #[test]
    fn test_has_transition() {
        let mut table = HierarchicalTransitionTable::new();
        table.add_transition(Transition::new(
            TestState::A, TestState::B, TestEvent::GoToB,
        ));

        assert!(table.has_transition(&TestState::A, &TestEvent::GoToB));
        assert!(!table.has_transition(&TestState::A, &TestEvent::GoToC));
    }

    #[test]
    fn test_transitions_from() {
        let mut table = HierarchicalTransitionTable::new();
        table.add_transition(Transition::new(
            TestState::A, TestState::B, TestEvent::GoToB,
        ));
        table.add_transition(Transition::new(
            TestState::A, TestState::C, TestEvent::GoToC,
        ));

        let from_a = table.transitions_from(&TestState::A);
        assert_eq!(from_a.len(), 2);
    }

    #[test]
    fn test_format_all() {
        let mut table = HierarchicalTransitionTable::new();
        table.add_transition(Transition::new(
            TestState::A, TestState::B, TestEvent::GoToB,
        ));

        let formatted = table.format_all();
        assert!(formatted.contains("A"));
        assert!(formatted.contains("B"));
    }

    #[test]
    fn test_add_inherited_transition() {
        let mut table = HierarchicalTransitionTable::new();
        table.add_inherited_transition(Transition::new(
            TestState::A, TestState::C, TestEvent::GoToC,
        ));

        let result = table.find_transition(&TestState::A, &TestEvent::GoToC);
        assert!(result.is_ok());
    }
}
