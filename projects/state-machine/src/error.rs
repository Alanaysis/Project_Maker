use std::fmt::Debug;
use thiserror::Error;

/// Errors that can occur in state machine operations
#[derive(Error, Debug)]
pub enum StateMachineError {
    /// No valid transition found for the given state and event
    #[error("No transition defined for state {state:?} with event {event:?}")]
    NoTransition {
        state: String,
        event: String,
    },

    /// Guard condition rejected the transition
    #[error("Guard condition rejected transition from {from:?} to {to:?}")]
    GuardRejected {
        from: String,
        to: String,
    },

    /// Action execution failed
    #[error("Action execution failed: {reason}")]
    ActionFailed {
        reason: String,
    },

    /// Invalid state transition
    #[error("Invalid transition from {from:?} to {to:?}")]
    InvalidTransition {
        from: String,
        to: String,
    },

    /// State machine is in an invalid state
    #[error("State machine is in an invalid state: {state:?}")]
    InvalidState {
        state: String,
    },

    /// Generic error
    #[error("State machine error: {0}")]
    Generic(String),
}

impl StateMachineError {
    /// Create a NoTransition error
    pub fn no_transition<S: Debug, E: Debug>(state: &S, event: &E) -> Self {
        Self::NoTransition {
            state: format!("{:?}", state),
            event: format!("{:?}", event),
        }
    }

    /// Create a GuardRejected error
    pub fn guard_rejected<S: Debug>(from: &S, to: &S) -> Self {
        Self::GuardRejected {
            from: format!("{:?}", from),
            to: format!("{:?}", to),
        }
    }

    /// Create an ActionFailed error
    pub fn action_failed(reason: impl Into<String>) -> Self {
        Self::ActionFailed {
            reason: reason.into(),
        }
    }

    /// Create an InvalidTransition error
    pub fn invalid_transition<S: Debug>(from: &S, to: &S) -> Self {
        Self::InvalidTransition {
            from: format!("{:?}", from),
            to: format!("{:?}", to),
        }
    }

    /// Create an InvalidState error
    pub fn invalid_state<S: Debug>(state: &S) -> Self {
        Self::InvalidState {
            state: format!("{:?}", state),
        }
    }

    /// Create a generic error
    pub fn generic(message: impl Into<String>) -> Self {
        Self::Generic(message.into())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_no_transition_error() {
        let err = StateMachineError::no_transition(&"Idle", &"Start");
        assert!(err.to_string().contains("Idle"));
        assert!(err.to_string().contains("Start"));
    }

    #[test]
    fn test_guard_rejected_error() {
        let err = StateMachineError::guard_rejected(&"Off", &"On");
        assert!(err.to_string().contains("Off"));
        assert!(err.to_string().contains("On"));
    }

    #[test]
    fn test_action_failed_error() {
        let err = StateMachineError::action_failed("timeout");
        assert!(err.to_string().contains("timeout"));
    }

    #[test]
    fn test_invalid_transition_error() {
        let err = StateMachineError::invalid_transition(&"A", &"B");
        assert!(err.to_string().contains("A"));
        assert!(err.to_string().contains("B"));
    }

    #[test]
    fn test_invalid_state_error() {
        let err = StateMachineError::invalid_state(&"Invalid");
        assert!(err.to_string().contains("Invalid"));
    }

    #[test]
    fn test_generic_error() {
        let err = StateMachineError::generic("something went wrong");
        assert!(err.to_string().contains("something went wrong"));
    }
}
