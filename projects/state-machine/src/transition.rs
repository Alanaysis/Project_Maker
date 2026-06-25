use crate::{Event, Result, State, StateMachineError};
use std::fmt::Debug;

/// Guard function type for transition conditions
pub type GuardFn<S, E> = Box<dyn Fn(&S, &S, &E) -> bool + Send + Sync>;

/// Action function type for transition side effects
pub type ActionFn<S, E> = Box<dyn Fn(&S, &S, &E) -> Result<()> + Send + Sync>;

/// Represents a transition between states
pub struct Transition<S: State, E: Event> {
    /// Source state
    pub from: S,
    /// Target state
    pub to: S,
    /// Event that triggers this transition
    pub event: E,
    /// Optional guard condition
    pub guard: Option<GuardFn<S, E>>,
    /// Optional action to execute on transition
    pub action: Option<ActionFn<S, E>>,
    /// Description of this transition
    pub description: Option<String>,
}

impl<S: State, E: Event> Transition<S, E> {
    /// Create a new transition without guard or action
    pub fn new(from: S, to: S, event: E) -> Self {
        Self {
            from,
            to,
            event,
            guard: None,
            action: None,
            description: None,
        }
    }

    /// Set a guard condition for this transition
    pub fn with_guard(mut self, guard: impl Fn(&S, &S, &E) -> bool + Send + Sync + 'static) -> Self {
        self.guard = Some(Box::new(guard));
        self
    }

    /// Set an action to execute when this transition occurs
    pub fn with_action(mut self, action: impl Fn(&S, &S, &E) -> Result<()> + Send + Sync + 'static) -> Self {
        self.action = Some(Box::new(action));
        self
    }

    /// Set a description for this transition
    pub fn with_description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }

    /// Check if the guard condition allows this transition
    pub fn check_guard(&self, event: &E) -> bool {
        match &self.guard {
            Some(guard) => guard(&self.from, &self.to, event),
            None => true,
        }
    }

    /// Execute the action for this transition
    pub fn execute_action(&self, event: &E) -> Result<()> {
        match &self.action {
            Some(action) => action(&self.from, &self.to, event),
            None => Ok(()),
        }
    }

    /// Check if this transition matches the given state and event
    pub fn matches(&self, state: &S, event: &E) -> bool {
        self.from == *state && self.event == *event
    }
}

impl<S: State, E: Event> Debug for Transition<S, E> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Transition")
            .field("from", &self.from)
            .field("to", &self.to)
            .field("event", &self.event)
            .field("has_guard", &self.guard.is_some())
            .field("has_action", &self.action.is_some())
            .field("description", &self.description)
            .finish()
    }
}

/// Builder for creating transitions
pub struct TransitionBuilder<S: State, E: Event> {
    from: Option<S>,
    to: Option<S>,
    event: Option<E>,
    guard: Option<GuardFn<S, E>>,
    action: Option<ActionFn<S, E>>,
    description: Option<String>,
}

impl<S: State, E: Event> TransitionBuilder<S, E> {
    /// Create a new transition builder
    pub fn new() -> Self {
        Self {
            from: None,
            to: None,
            event: None,
            guard: None,
            action: None,
            description: None,
        }
    }

    /// Set the source state
    pub fn from(mut self, from: S) -> Self {
        self.from = Some(from);
        self
    }

    /// Set the target state
    pub fn to(mut self, to: S) -> Self {
        self.to = Some(to);
        self
    }

    /// Set the trigger event
    pub fn on(mut self, event: E) -> Self {
        self.event = Some(event);
        self
    }

    /// Set a guard condition
    pub fn when(mut self, guard: impl Fn(&S, &S, &E) -> bool + Send + Sync + 'static) -> Self {
        self.guard = Some(Box::new(guard));
        self
    }

    /// Set an action to execute
    pub fn then(mut self, action: impl Fn(&S, &S, &E) -> Result<()> + Send + Sync + 'static) -> Self {
        self.action = Some(Box::new(action));
        self
    }

    /// Set a description
    pub fn describe(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }

    /// Build the transition
    pub fn build(self) -> Result<Transition<S, E>> {
        let from = self.from.ok_or_else(|| {
            StateMachineError::generic("Source state is required")
        })?;
        let to = self.to.ok_or_else(|| {
            StateMachineError::generic("Target state is required")
        })?;
        let event = self.event.ok_or_else(|| {
            StateMachineError::generic("Event is required")
        })?;

        Ok(Transition {
            from,
            to,
            event,
            guard: self.guard,
            action: self.action,
            description: self.description,
        })
    }
}

impl<S: State, E: Event> Default for TransitionBuilder<S, E> {
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

    impl State for TestState {}
    impl Event for TestEvent {}

    #[test]
    fn test_transition_new() {
        let t = Transition::new(TestState::A, TestState::B, TestEvent::GoToB);
        assert_eq!(t.from, TestState::A);
        assert_eq!(t.to, TestState::B);
        assert_eq!(t.event, TestEvent::GoToB);
        assert!(t.guard.is_none());
        assert!(t.action.is_none());
    }

    #[test]
    fn test_transition_matches() {
        let t = Transition::new(TestState::A, TestState::B, TestEvent::GoToB);
        assert!(t.matches(&TestState::A, &TestEvent::GoToB));
        assert!(!t.matches(&TestState::B, &TestEvent::GoToB));
        assert!(!t.matches(&TestState::A, &TestEvent::GoToC));
    }

    #[test]
    fn test_transition_guard_always_true() {
        let t = Transition::new(TestState::A, TestState::B, TestEvent::GoToB);
        assert!(t.check_guard(&TestEvent::GoToB));
    }

    #[test]
    fn test_transition_guard_with_condition() {
        let t = Transition::new(TestState::A, TestState::B, TestEvent::GoToB)
            .with_guard(|_from, _to, event| *event == TestEvent::GoToB);

        assert!(t.check_guard(&TestEvent::GoToB));
        assert!(!t.check_guard(&TestEvent::GoToC));
    }

    #[test]
    fn test_transition_action() {
        let t = Transition::new(TestState::A, TestState::B, TestEvent::GoToB)
            .with_action(|_from, _to, _event| {
                // Action executed successfully
                Ok(())
            });

        assert!(t.execute_action(&TestEvent::GoToB).is_ok());
    }

    #[test]
    fn test_transition_with_description() {
        let t = Transition::new(TestState::A, TestState::B, TestEvent::GoToB)
            .with_description("Move from A to B");

        assert_eq!(t.description, Some("Move from A to B".to_string()));
    }

    #[test]
    fn test_transition_builder_success() {
        let t = TransitionBuilder::new()
            .from(TestState::A)
            .to(TestState::B)
            .on(TestEvent::GoToB)
            .describe("A to B")
            .build()
            .unwrap();

        assert_eq!(t.from, TestState::A);
        assert_eq!(t.to, TestState::B);
        assert_eq!(t.event, TestEvent::GoToB);
        assert_eq!(t.description, Some("A to B".to_string()));
    }

    #[test]
    fn test_transition_builder_missing_from() {
        let result = TransitionBuilder::new()
            .to(TestState::B)
            .on(TestEvent::GoToB)
            .build();

        assert!(result.is_err());
    }

    #[test]
    fn test_transition_builder_missing_to() {
        let result = TransitionBuilder::new()
            .from(TestState::A)
            .on(TestEvent::GoToB)
            .build();

        assert!(result.is_err());
    }

    #[test]
    fn test_transition_builder_missing_event() {
        let result: crate::Result<Transition<TestState, TestEvent>> = TransitionBuilder::new()
            .from(TestState::A)
            .to(TestState::B)
            .build();

        assert!(result.is_err());
    }

    #[test]
    fn test_transition_debug() {
        let t = Transition::new(TestState::A, TestState::B, TestEvent::GoToB);
        let debug_str = format!("{:?}", t);
        assert!(debug_str.contains("A"));
        assert!(debug_str.contains("B"));
        assert!(debug_str.contains("GoToB"));
    }
}
