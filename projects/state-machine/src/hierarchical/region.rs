//! # Regions
//!
//! A region is a partition of a composite state's behavior.
//! Multiple orthogonal regions within a composite state operate independently
//! and concurrently, forming an orthogonal decomposition of behavior.
//!
//! ## Orthogonal Regions
//!
//! In UML Statecharts, a composite state can contain multiple regions.
//! Each region maintains its own active state independently.

use crate::error::StateMachineError;
use crate::hierarchical::HierarchicalTransitionTable;
use crate::{Event, Result, State};
use log::debug;
use std::fmt::Debug;

/// Represents a single state within a region
#[derive(Debug, Clone)]
pub struct RegionState<S: State> {
    /// Unique identifier
    pub id: String,
    /// The state value
    pub state: S,
}

impl<S: State> RegionState<S> {
    /// Create a new region state
    pub fn new(id: impl Into<String>, state: S) -> Self {
        Self {
            id: id.into(),
            state,
        }
    }
}

/// A region within a composite state
///
/// Each region has its own set of states and maintains one active state.
/// Regions operate orthogonally - changes in one region do not affect others.
#[derive(Clone)]
pub struct Region<S: State> {
    /// Unique identifier for this region
    pub id: usize,
    /// All states available in this region
    pub states: Vec<RegionState<S>>,
    /// The currently active state in this region
    active_state: Option<S>,
    /// Initial state index (set when first entered)
    initial_state_idx: Option<usize>,
}

impl<S: State> Region<S> {
    /// Create a new region with a given ID
    pub fn new(id: usize) -> Self {
        Self {
            id,
            states: Vec::new(),
            active_state: None,
            initial_state_idx: None,
        }
    }

    /// Add a state to this region
    pub fn with_state(mut self, state: S, state_id: impl Into<String>) -> Self {
        self.states.push(RegionState::new(state_id, state));
        self
    }

    /// Set the initial state for this region
    pub fn with_initial_state(mut self, state: S, state_id: impl Into<String>) -> Result<Self> {
        let idx = self.states.len();
        self.states.push(RegionState::new(state_id, state));
        self.initial_state_idx = Some(idx);
        Ok(self)
    }

    /// Get the currently active state
    pub fn active_state(&self) -> Option<&S> {
        self.active_state.as_ref()
    }

    /// Set the active state
    pub fn set_state(&mut self, state: S) -> Result<()> {
        if !self.states.iter().any(|rs| rs.state == state) {
            return Err(StateMachineError::InvalidState {
                state: format!("{:?}", state),
            });
        }
        self.active_state = Some(state);
        Ok(())
    }

    /// Set the initial state (called on first entry)
    pub fn set_initial_state(&mut self) -> Result<()> {
        if let Some(idx) = self.initial_state_idx {
            if let Some(rs) = self.states.get(idx) {
                self.active_state = Some(rs.state.clone());
                debug!("Region {} set to initial state: {:?}", self.id, rs.state);
                Ok(())
            } else {
                Err(StateMachineError::InvalidState {
                    state: "initial state index out of range".to_string(),
                })
            }
        } else {
            Err(StateMachineError::InvalidState {
                state: "no initial state defined for region".to_string(),
            })
        }
    }

    /// Get the active path (for deep history)
    pub fn active_path(&self) -> Vec<S> {
        if let Some(ref s) = self.active_state {
            vec![s.clone()]
        } else {
            Vec::new()
        }
    }

    /// Try to handle an event within this region
    pub fn handle_event<Ev: Event>(
        &mut self,
        event: &Ev,
        transition_table: &HierarchicalTransitionTable<S, Ev>,
    ) -> Result<S> {
        if let Some(active) = self.active_state.clone() {
            debug!(
                "Region {} trying to handle event {:?} from state {:?}",
                self.id, event, active
            );

            if let Ok(transition) = transition_table.find_transition(&active, event) {
                if !transition.check_guard(event) {
                    debug!("Region {}: guard rejected for {:?}", self.id, event);
                    return Err(StateMachineError::GuardRejected {
                        from: format!("{:?}", active),
                        to: format!("{:?}", transition.to),
                    });
                }

                if let Err(e) = transition.execute_action(event) {
                    debug!("Region {}: action failed: {:?}", self.id, e);
                    return Err(e);
                }

                self.active_state = Some(transition.to.clone());
                debug!(
                    "Region {} transition: {:?} -> {:?}",
                    self.id, active, transition.to
                );

                Ok(transition.to.clone())
            } else {
                debug!("Region {}: no transition for event {:?}", self.id, event);
                Err(StateMachineError::NoTransition {
                    state: format!("{:?}", active),
                    event: format!("{:?}", event),
                })
            }
        } else {
            Err(StateMachineError::InvalidState {
                state: format!("region {} has no active state", self.id),
            })
        }
    }
}

/// Builder for creating regions
pub struct RegionBuilder<S: State> {
    id: usize,
    initial_state: Option<(S, String)>,
    states: Vec<(S, String)>,
}

impl<S: State> RegionBuilder<S> {
    /// Create a new region builder
    pub fn new() -> Self {
        Self {
            id: 0,
            initial_state: None,
            states: Vec::new(),
        }
    }

    /// Set the region ID
    pub fn with_id(mut self, id: usize) -> Self {
        self.id = id;
        self
    }

    /// Set the initial state
    pub fn with_initial_state(mut self, state: S, state_id: impl Into<String>) -> Self {
        self.initial_state = Some((state, state_id.into()));
        self
    }

    /// Add a state to this region
    pub fn with_state(mut self, state: S, state_id: impl Into<String>) -> Self {
        self.states.push((state, state_id.into()));
        self
    }

    /// Build the region
    pub fn build(self) -> Region<S> {
        let mut region = Region::new(self.id);

        for (state, id) in self.states {
            region.states.push(RegionState::new(id, state));
        }

        if let Some((state, id)) = self.initial_state {
            region.states.push(RegionState::new(id, state));
            region.initial_state_idx = Some(region.states.len() - 1);
        }

        region
    }
}

impl<S: State> Default for RegionBuilder<S> {
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
    }

    impl crate::State for TestState {}
    impl crate::Event for TestEvent {}

    #[test]
    fn test_region_creation() {
        let region: Region<TestState> = Region::new(0);
        assert_eq!(region.id, 0);
        assert!(region.active_state().is_none());
        assert!(region.states.is_empty());
    }

    #[test]
    fn test_region_with_state() {
        let region = Region::new(0)
            .with_state(TestState::A, "a");

        assert_eq!(region.states.len(), 1);
    }

    #[test]
    fn test_region_with_initial_state() {
        let region = Region::new(0)
            .with_initial_state(TestState::A, "a")
            .unwrap();

        assert_eq!(region.states.len(), 1);
        assert!(region.initial_state_idx.is_some());
    }

    #[test]
    fn test_region_set_state() {
        let mut region = Region::new(0)
            .with_state(TestState::A, "a")
            .with_state(TestState::B, "b");

        region.set_state(TestState::B).unwrap();
        assert_eq!(*region.active_state().unwrap(), TestState::B);
    }

    #[test]
    fn test_region_set_invalid_state() {
        let mut region = Region::new(0)
            .with_state(TestState::A, "a");

        let result = region.set_state(TestState::B);
        assert!(result.is_err());
    }

    #[test]
    fn test_region_builder() {
        let region = RegionBuilder::new()
            .with_id(1)
            .with_initial_state(TestState::A, "a")
            .with_state(TestState::B, "b")
            .build();

        assert_eq!(region.id, 1);
        assert_eq!(region.states.len(), 2);
    }
}
