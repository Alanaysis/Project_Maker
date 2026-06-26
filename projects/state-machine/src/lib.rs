//! # State Machine Framework
//!
//! A generic state machine framework supporting state transitions, event-driven architecture,
//! and history recording.
//!
//! ## Features
//!
//! - Generic state and event types
//! - Event-driven state transitions
//! - Guard conditions for transitions
//! - Actions on state transitions
//! - History recording
//! - Transition graph visualization
//!
//! ## Example
//!
//! ```rust
//! use state_machine::{StateMachine, State, Event, Transition};
//!
//! // Define states
//! #[derive(Debug, Clone, PartialEq, Eq, Hash)]
//! enum LightState {
//!     Off,
//!     On,
//!     Broken,
//! }
//!
//! // Define events
//! #[derive(Debug, Clone, PartialEq, Eq, Hash)]
//! enum LightEvent {
//!     TurnOn,
//!     TurnOff,
//!     Break,
//! }
//!
//! // Implement State trait
//! impl State for LightState {}
//!
//! // Implement Event trait
//! impl Event for LightEvent {}
//!
//! // Create state machine
//! let mut sm = StateMachine::new(LightState::Off);
//!
//! // Add transitions
//! sm.add_transition(Transition::new(
//!     LightState::Off,
//!     LightState::On,
//!     LightEvent::TurnOn,
//! ));
//!
//! // Process event
//! sm.process_event(LightEvent::TurnOn).unwrap();
//! assert_eq!(sm.current_state(), &LightState::On);
//! ```

pub mod error;
pub mod history;
pub mod hierarchical;
pub mod state_machine;
pub mod transition;

pub use error::StateMachineError;
pub use history::{HistoryEntry, HistoryManager};
pub use state_machine::StateMachine;
pub use transition::{Transition, TransitionBuilder};

use std::fmt::Debug;
use std::hash::Hash;

/// Trait for state types
pub trait State: Debug + Clone + PartialEq + Eq + Hash {}

/// Trait for event types
pub trait Event: Debug + Clone + PartialEq + Eq + Hash {}

/// Result type for state machine operations
pub type Result<T> = std::result::Result<T, StateMachineError>;
