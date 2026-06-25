use crate::error::StateMachineError;
use crate::history::{HistoryEntry, HistoryManager};
use crate::transition::Transition;
use crate::{Event, Result, State};
use log::{debug, info, warn};
use std::collections::HashMap;
use std::fmt::Debug;
use std::time::Instant;

/// Type alias for state change callback
type StateChangeCallback<S, E> = Box<dyn Fn(&S, &S, &E) + Send + Sync>;

/// Type alias for transition failed callback
type TransitionFailedCallback<S, E> = Box<dyn Fn(&S, &E, &StateMachineError) + Send + Sync>;

/// Represents a state machine instance
pub struct StateMachine<S: State, E: Event> {
    /// Current state
    current_state: S,
    /// List of all defined transitions
    transitions: Vec<Transition<S, E>>,
    /// Index of transitions by (state, event) for fast lookup
    transition_index: HashMap<(S, E), usize>,
    /// History manager
    history: HistoryManager<S, E>,
    /// Whether to record history
    record_history: bool,
    /// Optional callback when state changes
    on_state_change: Option<StateChangeCallback<S, E>>,
    /// Optional callback when transition fails
    on_transition_failed: Option<TransitionFailedCallback<S, E>>,
}

impl<S: State, E: Event> StateMachine<S, E> {
    /// Create a new state machine with an initial state
    pub fn new(initial_state: S) -> Self {
        info!("Creating new state machine with initial state: {:?}", initial_state);
        Self {
            current_state: initial_state,
            transitions: Vec::new(),
            transition_index: HashMap::new(),
            history: HistoryManager::default(),
            record_history: true,
            on_state_change: None,
            on_transition_failed: None,
        }
    }

    /// Create a new state machine with history recording disabled
    pub fn new_without_history(initial_state: S) -> Self {
        let mut sm = Self::new(initial_state);
        sm.record_history = false;
        sm
    }

    /// Set the maximum number of history entries
    pub fn with_history_capacity(mut self, capacity: usize) -> Self {
        self.history = HistoryManager::new(capacity);
        self
    }

    /// Set a callback for state changes
    pub fn on_state_change(mut self, callback: impl Fn(&S, &S, &E) + Send + Sync + 'static) -> Self {
        self.on_state_change = Some(Box::new(callback));
        self
    }

    /// Set a callback for transition failures
    pub fn on_transition_failed(mut self, callback: impl Fn(&S, &E, &StateMachineError) + Send + Sync + 'static) -> Self {
        self.on_transition_failed = Some(Box::new(callback));
        self
    }

    /// Add a transition to the state machine
    pub fn add_transition(&mut self, transition: Transition<S, E>) {
        let key = (transition.from.clone(), transition.event.clone());
        let index = self.transitions.len();

        debug!(
            "Adding transition: {:?} --({:?})--> {:?}",
            transition.from, transition.event, transition.to
        );

        self.transition_index.insert(key, index);
        self.transitions.push(transition);
    }

    /// Add multiple transitions at once
    pub fn add_transitions(&mut self, transitions: Vec<Transition<S, E>>) {
        for transition in transitions {
            self.add_transition(transition);
        }
    }

    /// Get the current state
    pub fn current_state(&self) -> &S {
        &self.current_state
    }

    /// Set the current state directly (bypasses transitions)
    pub fn set_state(&mut self, state: S) {
        info!("Directly setting state from {:?} to {:?}", self.current_state, state);
        self.current_state = state;
    }

    /// Process an event and potentially transition to a new state
    pub fn process_event(&mut self, event: E) -> Result<()> {
        let start_time = Instant::now();
        debug!("Processing event: {:?}", event);

        // Find matching transition
        let transition = self.find_transition(&self.current_state, &event)?;

        let from_state = self.current_state.clone();
        let to_state = transition.to.clone();

        // Check guard condition
        if !transition.check_guard(&event) {
            let error = StateMachineError::guard_rejected(&from_state, &to_state);
            warn!("Guard rejected transition: {:?}", error);

            if self.record_history {
                self.history.push(HistoryEntry::failure(
                    from_state.clone(),
                    to_state.clone(),
                    event.clone(),
                    error.to_string(),
                ));
            }

            if let Some(callback) = &self.on_transition_failed {
                callback(&from_state, &event, &error);
            }

            return Err(error);
        }

        // Execute action
        if let Err(e) = transition.execute_action(&event) {
            warn!("Action failed: {:?}", e);

            if self.record_history {
                self.history.push(HistoryEntry::failure(
                    from_state.clone(),
                    to_state.clone(),
                    event.clone(),
                    e.to_string(),
                ));
            }

            if let Some(callback) = &self.on_transition_failed {
                callback(&from_state, &event, &e);
            }

            return Err(e);
        }

        // Perform the transition
        self.current_state = to_state.clone();
        let duration = start_time.elapsed();

        info!(
            "Transition successful: {:?} --({:?})--> {:?} ({:?})",
            from_state, event, to_state, duration
        );

        // Record history
        if self.record_history {
            self.history.push(
                HistoryEntry::success(from_state.clone(), to_state.clone(), event.clone())
                    .with_duration(duration),
            );
        }

        // Notify state change
        if let Some(callback) = &self.on_state_change {
            callback(&from_state, &to_state, &event);
        }

        Ok(())
    }

    /// Find a transition for the given state and event
    fn find_transition(&self, state: &S, event: &E) -> Result<&Transition<S, E>> {
        let key = (state.clone(), event.clone());

        match self.transition_index.get(&key) {
            Some(&index) => Ok(&self.transitions[index]),
            None => Err(StateMachineError::no_transition(state, event)),
        }
    }

    /// Check if a transition is possible for the given event
    pub fn can_process_event(&self, event: &E) -> bool {
        let key = (self.current_state.clone(), event.clone());
        self.transition_index.contains_key(&key)
    }

    /// Get all possible events from the current state
    pub fn possible_events(&self) -> Vec<&E> {
        self.transitions
            .iter()
            .filter(|t| t.from == self.current_state)
            .map(|t| &t.event)
            .collect()
    }

    /// Get all transitions
    pub fn transitions(&self) -> &[Transition<S, E>] {
        &self.transitions
    }

    /// Get the history manager
    pub fn history(&self) -> &HistoryManager<S, E> {
        &self.history
    }

    /// Get a mutable reference to the history manager
    pub fn history_mut(&mut self) -> &mut HistoryManager<S, E> {
        &mut self.history
    }

    /// Check if history recording is enabled
    pub fn is_recording_history(&self) -> bool {
        self.record_history
    }

    /// Enable or disable history recording
    pub fn set_record_history(&mut self, record: bool) {
        self.record_history = record;
    }

    /// Get the number of defined transitions
    pub fn transition_count(&self) -> usize {
        self.transitions.len()
    }

    /// Get a formatted string of all transitions
    pub fn format_transitions(&self) -> String {
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

    /// Get a formatted string of the transition graph
    pub fn format_graph(&self) -> String {
        let mut graph = String::new();
        graph.push_str("State Machine Transition Graph\n");
        graph.push_str("==============================\n\n");

        // Group transitions by source state
        let mut by_state: HashMap<&S, Vec<&Transition<S, E>>> = HashMap::new();
        for t in &self.transitions {
            by_state.entry(&t.from).or_default().push(t);
        }

        for (state, transitions) in &by_state {
            graph.push_str(&format!("State {:?}:\n", state));
            for t in transitions {
                let guard_str = if t.guard.is_some() { " [guarded]" } else { "" };
                let action_str = if t.action.is_some() { " [action]" } else { "" };
                let desc_str = t.description
                    .as_ref()
                    .map(|d| format!(" - {}", d))
                    .unwrap_or_default();

                graph.push_str(&format!(
                    "  --({:?})--> {:?}{}{}{}\n",
                    t.event, t.to, guard_str, action_str, desc_str
                ));
            }
            graph.push('\n');
        }

        graph
    }
}

impl<S: State, E: Event> Debug for StateMachine<S, E> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("StateMachine")
            .field("current_state", &self.current_state)
            .field("transition_count", &self.transitions.len())
            .field("history_entries", &self.history.len())
            .field("record_history", &self.record_history)
            .finish()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::transition::TransitionBuilder;

    #[derive(Debug, Clone, PartialEq, Eq, Hash)]
    enum TestState {
        Idle,
        Running,
        Paused,
        Stopped,
    }

    #[derive(Debug, Clone, PartialEq, Eq, Hash)]
    enum TestEvent {
        Start,
        Pause,
        Resume,
        Stop,
    }

    impl State for TestState {}
    impl Event for TestEvent {}

    fn create_test_sm() -> StateMachine<TestState, TestEvent> {
        let mut sm = StateMachine::new(TestState::Idle);

        sm.add_transition(Transition::new(TestState::Idle, TestState::Running, TestEvent::Start));
        sm.add_transition(Transition::new(TestState::Running, TestState::Paused, TestEvent::Pause));
        sm.add_transition(Transition::new(TestState::Paused, TestState::Running, TestEvent::Resume));
        sm.add_transition(Transition::new(TestState::Running, TestState::Stopped, TestEvent::Stop));
        sm.add_transition(Transition::new(TestState::Paused, TestState::Stopped, TestEvent::Stop));

        sm
    }

    #[test]
    fn test_new_state_machine() {
        let sm = StateMachine::<TestState, TestEvent>::new(TestState::Idle);
        assert_eq!(sm.current_state(), &TestState::Idle);
        assert_eq!(sm.transition_count(), 0);
        assert!(sm.is_recording_history());
    }

    #[test]
    fn test_new_without_history() {
        let sm = StateMachine::<TestState, TestEvent>::new_without_history(TestState::Idle);
        assert!(!sm.is_recording_history());
    }

    #[test]
    fn test_add_transition() {
        let mut sm = StateMachine::new(TestState::Idle);
        sm.add_transition(Transition::new(TestState::Idle, TestState::Running, TestEvent::Start));
        assert_eq!(sm.transition_count(), 1);
    }

    #[test]
    fn test_add_transitions() {
        let mut sm = StateMachine::new(TestState::Idle);
        sm.add_transitions(vec![
            Transition::new(TestState::Idle, TestState::Running, TestEvent::Start),
            Transition::new(TestState::Running, TestState::Paused, TestEvent::Pause),
        ]);
        assert_eq!(sm.transition_count(), 2);
    }

    #[test]
    fn test_process_event() {
        let mut sm = create_test_sm();
        assert_eq!(sm.current_state(), &TestState::Idle);

        sm.process_event(TestEvent::Start).unwrap();
        assert_eq!(sm.current_state(), &TestState::Running);

        sm.process_event(TestEvent::Pause).unwrap();
        assert_eq!(sm.current_state(), &TestState::Paused);

        sm.process_event(TestEvent::Resume).unwrap();
        assert_eq!(sm.current_state(), &TestState::Running);

        sm.process_event(TestEvent::Stop).unwrap();
        assert_eq!(sm.current_state(), &TestState::Stopped);
    }

    #[test]
    fn test_process_event_no_transition() {
        let mut sm = create_test_sm();
        let result = sm.process_event(TestEvent::Stop);
        assert!(result.is_err());
        assert_eq!(sm.current_state(), &TestState::Idle);
    }

    #[test]
    fn test_process_event_with_guard() {
        let mut sm = StateMachine::new(TestState::Idle);

        sm.add_transition(
            Transition::new(TestState::Idle, TestState::Running, TestEvent::Start)
                .with_guard(|_from, _to, event| *event == TestEvent::Start),
        );

        sm.process_event(TestEvent::Start).unwrap();
        assert_eq!(sm.current_state(), &TestState::Running);
    }

    #[test]
    fn test_process_event_guard_rejected() {
        let mut sm = StateMachine::new(TestState::Idle);

        sm.add_transition(
            Transition::new(TestState::Idle, TestState::Running, TestEvent::Start)
                .with_guard(|_from, _to, _event| false),
        );

        let result = sm.process_event(TestEvent::Start);
        assert!(result.is_err());
        assert_eq!(sm.current_state(), &TestState::Idle);
    }

    #[test]
    fn test_process_event_with_action() {
        let mut sm = StateMachine::new(TestState::Idle);

        sm.add_transition(
            Transition::new(TestState::Idle, TestState::Running, TestEvent::Start)
                .with_action(|_from, _to, _event| {
                    // Action executed
                    Ok(())
                }),
        );

        sm.process_event(TestEvent::Start).unwrap();
        assert_eq!(sm.current_state(), &TestState::Running);
    }

    #[test]
    fn test_process_event_action_failed() {
        let mut sm = StateMachine::new(TestState::Idle);

        sm.add_transition(
            Transition::new(TestState::Idle, TestState::Running, TestEvent::Start)
                .with_action(|_from, _to, _event| {
                    Err(StateMachineError::action_failed("test error"))
                }),
        );

        let result = sm.process_event(TestEvent::Start);
        assert!(result.is_err());
        assert_eq!(sm.current_state(), &TestState::Idle);
    }

    #[test]
    fn test_can_process_event() {
        let sm = create_test_sm();
        assert!(sm.can_process_event(&TestEvent::Start));
        assert!(!sm.can_process_event(&TestEvent::Pause));
        assert!(!sm.can_process_event(&TestEvent::Resume));
        assert!(!sm.can_process_event(&TestEvent::Stop));
    }

    #[test]
    fn test_possible_events() {
        let sm = create_test_sm();
        let events = sm.possible_events();
        assert_eq!(events.len(), 1);
        assert_eq!(events[0], &TestEvent::Start);
    }

    #[test]
    fn test_history_recording() {
        let mut sm = create_test_sm();

        sm.process_event(TestEvent::Start).unwrap();
        sm.process_event(TestEvent::Pause).unwrap();
        sm.process_event(TestEvent::Resume).unwrap();

        assert_eq!(sm.history().len(), 3);
    }

    #[test]
    fn test_history_disabled() {
        let mut sm = StateMachine::new_without_history(TestState::Idle);
        sm.add_transition(Transition::new(TestState::Idle, TestState::Running, TestEvent::Start));

        sm.process_event(TestEvent::Start).unwrap();
        assert_eq!(sm.history().len(), 0);
    }

    #[test]
    fn test_on_state_change_callback() {
        let mut sm = StateMachine::new(TestState::Idle);

        sm = sm.on_state_change(|_from, _to, _event| {
            // Callback would be called
        });

        sm.add_transition(Transition::new(TestState::Idle, TestState::Running, TestEvent::Start));
        sm.process_event(TestEvent::Start).unwrap();
    }

    #[test]
    fn test_set_state() {
        let mut sm: StateMachine<TestState, TestEvent> = StateMachine::new(TestState::Idle);
        assert_eq!(sm.current_state(), &TestState::Idle);

        sm.set_state(TestState::Running);
        assert_eq!(sm.current_state(), &TestState::Running);
    }

    #[test]
    fn test_format_transitions() {
        let sm = create_test_sm();
        let formatted = sm.format_transitions();
        assert!(formatted.contains("Idle"));
        assert!(formatted.contains("Running"));
        assert!(formatted.contains("Start"));
    }

    #[test]
    fn test_format_graph() {
        let sm = create_test_sm();
        let graph = sm.format_graph();
        assert!(graph.contains("State Machine Transition Graph"));
        assert!(graph.contains("Idle"));
        assert!(graph.contains("Running"));
    }

    #[test]
    fn test_debug() {
        let sm = create_test_sm();
        let debug_str = format!("{:?}", sm);
        assert!(debug_str.contains("Idle"));
        assert!(debug_str.contains("transition_count: 5"));
    }

    #[test]
    fn test_transition_builder() {
        let mut sm = StateMachine::new(TestState::Idle);

        let transition = TransitionBuilder::new()
            .from(TestState::Idle)
            .to(TestState::Running)
            .on(TestEvent::Start)
            .describe("Start the machine")
            .build()
            .unwrap();

        sm.add_transition(transition);
        sm.process_event(TestEvent::Start).unwrap();
        assert_eq!(sm.current_state(), &TestState::Running);
    }
}
