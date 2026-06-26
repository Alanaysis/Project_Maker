//! # Hierarchical State Machines (HSM)
//!
//! Hierarchical State Machines extend flat state machines by allowing states
//! to contain substates, creating a state hierarchy. This enables:
//!
//! - **State Reuse**: Common substate behavior shared across parent states
//! - **Orthogonal Regions**: Independent sub-machines running in parallel
//! - **Inherited Transitions**: Transitions defined at parent level apply to all children
//! - **Entry/Exit Actions**: Actions triggered when entering/exiting composite states
//!
//! ## Statechart Semantics
//!
//! This implementation follows UML Statechart semantics:
//!
//! 1. **Orthogonal Regions**: A state can have multiple independent regions
//! 2. **Deep History**: `H*` - restore to the last active substate at any depth
//! 3. **Shallow History**: `H` - restore to the last active direct child
//! 4. **Composite States**: States that contain substates
//!
//! When entering a composite state, the initial state of each region is activated.
//! When exiting, exit actions fire from deepest child to parent.

pub mod region;
pub mod state_entry;
pub mod transition_table;

pub use region::{Region, RegionBuilder};
pub use state_entry::{StateEntry, StateEntryBuilder};
pub use transition_table::HierarchicalTransitionTable;

use crate::error::StateMachineError;
use crate::history::{HistoryEntry, HistoryManager};
use crate::transition::Transition;
use crate::{Event, Result, State};
use log::{debug, info, warn};
use std::collections::HashMap;
use std::fmt::Debug;
use std::time::Instant;

/// Entry action triggered when entering a state
pub type EntryAction<S, E> = Box<dyn Fn(&S, &E) -> Result<()> + Send + Sync>;

/// Exit action triggered when exiting a state
pub type ExitAction<S, E> = Box<dyn Fn(&S, &E) -> Result<()> + Send + Sync>;

/// History restoration type for composite states
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HistoryType {
    /// No history - always restore to initial state
    None,
    /// Shallow history - restore to last active direct child state
    Shallow,
    /// Deep history - restore to last active state at any depth
    Deep,
}

/// A composite state that can contain substates organized in regions
///
/// Composite states enable hierarchical organization of behavior.
/// When entering a composite state, all regions activate their initial states.
/// When exiting, exit actions fire bottom-up through the hierarchy.
pub struct CompositeState<S: State, E: Event> {
    /// Unique identifier for this composite state
    pub id: String,
    /// The composite state name (for display)
    pub name: String,
    /// All regions within this composite state
    pub regions: Vec<Region<S>>,
    /// Entry action fired when entering this composite state
    pub entry_action: Option<EntryAction<S, E>>,
    /// Exit action fired when exiting this composite state
    pub exit_action: Option<ExitAction<S, E>>,
    /// History type: None, Shallow (H), or Deep (H*)
    pub history_type: HistoryType,
    /// Last active state per region (for shallow history)
    shallow_history: HashMap<usize, S>,
    /// Full state history per region (for deep history)
    deep_history: HashMap<usize, Vec<S>>,
    /// Initial state for each region (set when first entered)
    initial_set: bool,
}

impl<S: State, E: Event> Debug for CompositeState<S, E> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("CompositeState")
            .field("id", &self.id)
            .field("name", &self.name)
            .field("history_type", &self.history_type)
            .field("initial_set", &self.initial_set)
            .finish()
    }
}

impl<S: State, E: Event> CompositeState<S, E> {
    /// Create a new composite state
    pub fn new(id: impl Into<String>, name: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            name: name.into(),
            regions: Vec::new(),
            entry_action: None,
            exit_action: None,
            history_type: HistoryType::None,
            shallow_history: HashMap::new(),
            deep_history: HashMap::new(),
            initial_set: false,
        }
    }

    /// Add a region to this composite state
    pub fn with_region(mut self, region: Region<S>) -> Self {
        self.regions.push(region);
        self
    }

    /// Set the entry action
    pub fn with_entry_action(mut self, action: impl Fn(&S, &E) -> Result<()> + Send + Sync + 'static) -> Self {
        self.entry_action = Some(Box::new(action));
        self
    }

    /// Set the exit action
    pub fn with_exit_action(mut self, action: impl Fn(&S, &E) -> Result<()> + Send + Sync + 'static) -> Self {
        self.exit_action = Some(Box::new(action));
        self
    }

    /// Set the history type
    pub fn with_history(mut self, history_type: HistoryType) -> Self {
        self.history_type = history_type;
        self
    }

    /// Get the current active state for a region
    pub fn active_state_for_region(&self, region_idx: usize) -> Option<&S> {
        self.regions.get(region_idx).and_then(|r| r.active_state())
    }

    /// Get all active states across all regions
    pub fn active_states(&self) -> Vec<&S> {
        self.regions
            .iter()
            .enumerate()
            .filter_map(|(i, _)| self.active_state_for_region(i))
            .collect()
    }

    /// Enter this composite state, activating initial states for all regions
    pub fn enter(&mut self, event: &E) -> Result<()> {
        info!("Entering composite state: {} ({})", self.name, self.id);

        // Execute entry action
        if let Some(ref action) = self.entry_action {
            action(&self.as_state(), event)?;
        }

        // Set initial states for each region
        for (region_idx, region) in self.regions.iter_mut().enumerate() {
            if !self.initial_set {
                region.set_initial_state()?;
            } else if self.history_type == HistoryType::None {
                region.set_initial_state()?;
            } else if self.history_type == HistoryType::Shallow {
                if let Some(last_state) = self.shallow_history.get(&region_idx) {
                    if region.states.iter().any(|rs| rs.state == *last_state) {
                        region.set_state(last_state.clone())?;
                        continue;
                    }
                }
                region.set_initial_state()?;
            } else if self.history_type == HistoryType::Deep {
                if let Some(path) = self.deep_history.get(&region_idx) {
                    if let Some(last_state) = path.last() {
                        if region.states.iter().any(|rs| rs.state == *last_state) {
                            region.set_state(last_state.clone())?;
                            continue;
                        }
                    }
                }
                region.set_initial_state()?;
            }
        }

        self.initial_set = true;
        Ok(())
    }

    /// Exit this composite state, collecting history and firing exit actions
    pub fn exit(&mut self, event: &E) -> Result<()> {
        info!("Exiting composite state: {} ({})", self.name, self.id);

        // Collect history before exiting
        if self.history_type != HistoryType::None {
            for (region_idx, region) in self.regions.iter().enumerate() {
                if let Some(active) = region.active_state() {
                    if self.history_type == HistoryType::Shallow {
                        self.shallow_history.insert(region_idx, active.clone());
                    } else if self.history_type == HistoryType::Deep {
                        let path = region.active_path();
                        self.deep_history.insert(region_idx, path);
                    }
                }
            }
        }

        // Execute exit action
        if let Some(ref action) = self.exit_action {
            action(&self.as_state(), event)?;
        }

        Ok(())
    }

    /// Process an event within this composite state
    pub fn handle_event<Ev: Event>(
        &mut self,
        event: &Ev,
        transition_table: &HierarchicalTransitionTable<S, Ev>,
    ) -> Result<S> {
        debug!(
            "Handling event {:?} in composite state: {}",
            event, self.name
        );

        // Try each region to handle the event
        for (region_idx, region) in self.regions.iter_mut().enumerate() {
            match region.handle_event(event, transition_table) {
                Ok(new_state) => {
                    info!(
                        "Event {:?} handled in region {} of composite {}: -> {:?}",
                        event, region_idx, self.name, new_state
                    );
                    return Ok(new_state);
                }
                Err(_) => {
                    debug!(
                        "Region {} in {} could not handle event {:?}",
                        region_idx, self.name, event
                    );
                }
            }
        }

        Err(StateMachineError::NoTransition {
            state: format!("{:?} (composite: {})", self.as_state(), self.id),
            event: format!("{:?}", event),
        })
    }

    /// Get a flat representation of this state for the State trait
    fn as_state(&self) -> S {
        panic!("Cannot convert CompositeState to flat state directly")
    }
}

/// A state that can contain substates
///
/// This is the main building block for hierarchical state machines.
/// It wraps either a simple state or a composite state.
pub enum HState<S: State, E: Event> {
    /// A simple (leaf) state
    Simple(S),
    /// A composite state containing regions of substates
    Composite(Box<CompositeState<S, E>>),
}

impl<S: State, E: Event> Debug for HState<S, E> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            HState::Simple(s) => f.debug_tuple("HState::Simple").field(s).finish(),
            HState::Composite(c) => f.debug_tuple("HState::Composite").field(c).finish(),
        }
    }
}

impl<S: State, E: Event> PartialEq for HState<S, E> {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (HState::Simple(a), HState::Simple(b)) => a == b,
            _ => false,
        }
    }
}

impl<S: State, E: Event> Eq for HState<S, E> {}

impl<S: State, E: Event> HState<S, E> {
    /// Create a simple (leaf) state
    pub fn simple(state: S) -> Self {
        HState::Simple(state)
    }

    /// Create a composite state
    pub fn composite(composite: CompositeState<S, E>) -> Self {
        HState::Composite(Box::new(composite))
    }

    /// Check if this is a composite state
    pub fn is_composite(&self) -> bool {
        matches!(self, HState::Composite(_))
    }

    /// Get the composite state reference if this is composite
    pub fn as_composite(&self) -> Option<&CompositeState<S, E>> {
        match self {
            HState::Composite(c) => Some(c),
            _ => None,
        }
    }

    /// Get the mutable composite state reference if this is composite
    pub fn as_composite_mut(&mut self) -> Option<&mut CompositeState<S, E>> {
        match self {
            HState::Composite(c) => Some(c),
            _ => None,
        }
    }
}

// Note: HState does NOT implement the State trait directly because it cannot
// derive Hash (it contains boxed closures). Instead, it has its own trait
// hierarchy for hierarchical state machines.

/// A hierarchical state machine that supports nested states, regions, and history
///
/// Hierarchical state machines (also called Statecharts) extend flat FSMs by
/// allowing states to contain substates. This enables:
///
/// - **State hierarchy**: Organize related states under composite states
/// - **Orthogonal regions**: Multiple independent sub-machines within a state
/// - **History preservation**: Remember where you were when leaving a composite state
/// - **Entry/Exit actions**: Execute code when entering/exiting states at any level
///
/// ## Example (see `examples/hierarchical_sm.rs` for runnable code):
///
/// See the hierarchical_sm.rs example for complete runnable code demonstrating
/// composite states, regions, and history preservation.
pub struct HStateMachine<S: State, E: Event> {
    /// Current active state (can be simple or composite)
    current_state: HState<S, E>,
    /// Transition table for state transitions
    transition_table: HierarchicalTransitionTable<S, E>,
    /// History manager for tracking transitions
    history: HistoryManager<S, E>,
    /// Whether to record history
    record_history: bool,
    /// Entry actions for states
    entry_actions: HashMap<String, EntryAction<S, E>>,
    /// Exit actions for states
    exit_actions: HashMap<String, ExitAction<S, E>>,
}

impl<S: State, E: Event> HStateMachine<S, E> {
    /// Create a new hierarchical state machine with a root state
    pub fn new(root_state: HState<S, E>) -> Self {
        info!("Creating hierarchical state machine with root: {:?}", root_state);
        Self {
            current_state: root_state,
            transition_table: HierarchicalTransitionTable::new(),
            history: HistoryManager::default(),
            record_history: true,
            entry_actions: HashMap::new(),
            exit_actions: HashMap::new(),
        }
    }

    /// Create without history recording
    pub fn new_without_history(root_state: HState<S, E>) -> Self {
        let mut hsm = Self::new(root_state);
        hsm.record_history = false;
        hsm
    }

    /// Set history capacity
    pub fn with_history_capacity(mut self, capacity: usize) -> Self {
        self.history = HistoryManager::new(capacity);
        self
    }

    /// Register an entry action for a state
    pub fn with_entry_action(mut self, state_id: impl Into<String>, action: EntryAction<S, E>) -> Self {
        self.entry_actions.insert(state_id.into(), action);
        self
    }

    /// Register an exit action for a state
    pub fn with_exit_action(mut self, state_id: impl Into<String>, action: ExitAction<S, E>) -> Self {
        self.exit_actions.insert(state_id.into(), action);
        self
    }

    /// Add a transition to the state machine
    pub fn add_transition(&mut self, transition: Transition<S, E>) {
        self.transition_table.add_transition(transition);
    }

    /// Add multiple transitions
    pub fn add_transitions(&mut self, transitions: Vec<Transition<S, E>>) {
        for t in transitions {
            self.add_transition(t);
        }
    }

    /// Get the current state
    pub fn current_state(&self) -> &HState<S, E> {
        &self.current_state
    }

    /// Get a reference to the underlying simple state if it's a simple state
    pub fn as_simple_state(&self) -> Option<&S> {
        match &self.current_state {
            HState::Simple(s) => Some(s),
            _ => None,
        }
    }

    /// Process an event through the hierarchical state machine
    pub fn process_event(&mut self, event: E) -> Result<()> {
        let start_time = Instant::now();
        debug!("Processing event {:?} in hierarchical state machine", event);

        match &self.current_state {
            HState::Simple(current) => {
                let transition = self.transition_table.find_transition(current, &event)?;
                let from_state = current.clone();

                if !transition.check_guard(&event) {
                    let error = StateMachineError::guard_rejected(&from_state, &transition.to);
                    warn!("Guard rejected: {:?}", error);
                    self.record_history_entry(from_state, transition.to.clone(), event.clone(), false, Some(error.to_string()), None);
                    return Err(error);
                }

                if let Err(e) = transition.execute_action(&event) {
                    warn!("Transition action failed: {:?}", e);
                    self.record_history_entry(from_state, transition.to.clone(), event.clone(), false, Some(e.to_string()), None);
                    return Err(e);
                }

                // Execute exit action for previous state if registered
                let from_key = format!("{:?}", from_state);
                if let Some(ref action) = self.exit_actions.get(&from_key) {
                    action(&from_state, &event)?;
                }

                // Execute entry action for new state if registered
                let to_key = format!("{:?}", transition.to);
                if let Some(ref action) = self.entry_actions.get(&to_key) {
                    action(&transition.to, &event)?;
                }

                self.current_state = HState::Simple(transition.to.clone());
                let duration = start_time.elapsed();

                info!(
                    "Transition: {:?} --({:?})--> {:?} ({:?})",
                    from_state, event, transition.to, duration
                );

                self.record_history_entry(from_state, transition.to.clone(), event.clone(), true, None, Some(duration));
            }
            HState::Composite(_) => {
                // Clone the event for potential reuse
                let event_clone = event.clone();
                let transition_table = &self.transition_table;
                
                // Try each region to handle the event
                let mut handled = false;
                let mut result: Result<S> = Err(StateMachineError::NoTransition {
                    state: "composite state".to_string(),
                    event: format!("{:?}", event),
                });
                
                if let Some(composite_ref) = self.current_state.as_composite() {
                    let region_count = composite_ref.regions.len();
                    
                    for region_idx in 0..region_count {
                        if let Some(composite_mut) = self.current_state.as_composite_mut() {
                            if let Some(active) = composite_mut.active_state_for_region(region_idx) {
                                let _active_clone = active.clone();
                                if let Some(new_state) = composite_mut.regions.get_mut(region_idx)
                                    .and_then(|r| r.handle_event(&event_clone, transition_table).ok())
                                {
                                    handled = true;
                                    result = Ok(new_state);
                                    break;
                                }
                            }
                        }
                    }
                }
                
                if handled {
                    match result {
                        Ok(new_state) => {
                            let from_state = match &self.current_state {
                                HState::Simple(s) => s.clone(),
                                HState::Composite(_c) => panic!("Expected simple state after composite handling"),
                            };
                            self.current_state = HState::Simple(new_state.clone());
                            let duration = start_time.elapsed();
                            info!(
                                "Event handled in composite: {:?} --({:?})--> {:?} ({:?})",
                                from_state, event, new_state, duration
                            );
                            self.record_history_entry(from_state, new_state, event.clone(), true, None, Some(duration));
                        }
                        Err(e) => return Err(e),
                    }
                } else {
                    // No region could handle it - try to exit composite and transition
                    if let Some(composite_mut) = self.current_state.as_composite_mut() {
                        if let Some(active) = composite_mut.active_state_for_region(0).cloned() {
                            match self.transition_table.find_transition(&active, &event) {
                                Ok(transition) => {
                                    composite_mut.exit(&event)?;
                                    
                                    let from_key = format!("{:?}", active);
                                    if let Some(ref action) = self.exit_actions.get(&from_key) {
                                        action(&active, &event)?;
                                    }
                                    let to_key = format!("{:?}", transition.to);
                                    if let Some(ref action) = self.entry_actions.get(&to_key) {
                                        action(&transition.to, &event)?;
                                    }

                                    self.current_state = HState::Simple(transition.to.clone());
                                    let duration = start_time.elapsed();

                                    info!(
                                        "Exit composite, transition: {:?} --({:?})--> {:?} ({:?})",
                                        active, event, transition.to, duration
                                    );

                                    self.record_history_entry(active, transition.to.clone(), event.clone(), true, None, Some(duration));
                                }
                                Err(e) => return Err(e),
                            }
                        } else {
                            return Err(StateMachineError::InvalidState {
                                state: "composite has no active region".to_string(),
                            });
                        }
                    } else {
                        return Err(StateMachineError::InvalidState {
                            state: "current state is not composite".to_string(),
                        });
                    }
                }
            }
        }

        Ok(())
    }

    /// Record a history entry
    fn record_history_entry(
        &mut self,
        from: S,
        to: S,
        event: E,
        success: bool,
        error: Option<String>,
        duration: Option<std::time::Duration>,
    ) {
        if !self.record_history {
            return;
        }

        let entry = if success {
            HistoryEntry::success(from, to, event)
        } else {
            HistoryEntry::failure(from, to, event, error.unwrap_or_else(|| "unknown error".to_string()))
        };

        if let Some(d) = duration {
            self.history.push(entry.with_duration(d));
        } else {
            self.history.push(entry);
        }
    }

    /// Get the history manager
    pub fn history(&self) -> &HistoryManager<S, E> {
        &self.history
    }

    /// Get the transition table
    pub fn transition_table(&self) -> &HierarchicalTransitionTable<S, E> {
        &self.transition_table
    }

    /// Format the state hierarchy as a string
    pub fn format_hierarchy(&self) -> String {
        let mut output = String::new();
        self.format_state_recursive(&self.current_state, &mut output, 0);
        output
    }

    fn format_state_recursive(&self, state: &HState<S, E>, output: &mut String, indent: usize) {
        let prefix = "  ".repeat(indent);
        match state {
            HState::Simple(s) => {
                output.push_str(&format!("{}[●] {:?}\n", prefix, s));
            }
            HState::Composite(c) => {
                output.push_str(&format!("{}[○] {} ({})\n", prefix, c.name, c.id));
                for region in &c.regions {
                    output.push_str(&format!("{}  Region:\n", prefix));
                    for rs in &region.states {
                        if let Some(active) = region.active_state() {
                            if active == &rs.state {
                                output.push_str(&format!("{}    [●] {:?}\n", prefix, rs.state));
                            } else {
                                output.push_str(&format!("{}    [ ] {:?}\n", prefix, rs.state));
                            }
                        } else {
                            output.push_str(&format!("{}    [ ] {:?}\n", prefix, rs.state));
                        }
                    }
                }
            }
        }
    }
}

impl<S: State, E: Event> Debug for HStateMachine<S, E> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("HStateMachine")
            .field("current_state", &self.current_state)
            .field("history_entries", &self.history.len())
            .finish()
    }
}

/// Helper to extract a simple state from an HState
fn previous_state_to_simple<S: State, E: Event>(state: &HState<S, E>) -> Result<S> {
    match state {
        HState::Simple(s) => Ok(s.clone()),
        HState::Composite(_) => {
            Err(StateMachineError::InvalidState {
                state: "cannot extract simple state from composite".to_string(),
            })
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Debug, Clone, PartialEq, Eq, Hash)]
    enum TestState {
        Idle,
        Active,
        Paused,
        Complete,
    }

    #[derive(Debug, Clone, PartialEq, Eq, Hash)]
    enum TestEvent {
        Start,
        Pause,
        Resume,
        Complete,
    }

    impl crate::State for TestState {}
    impl crate::Event for TestEvent {}

    #[test]
    fn test_composite_state_creation() {
        let composite: CompositeState<TestState, TestEvent> = CompositeState::new("test", "Test Composite");
        assert_eq!(composite.id, "test");
        assert_eq!(composite.name, "Test Composite");
        assert_eq!(composite.history_type, HistoryType::None);
        assert!(composite.regions.is_empty());
    }

    #[test]
    fn test_composite_with_region() {
        let region = RegionBuilder::new()
            .with_initial_state(TestState::Idle, "idle")
            .build();

        let composite: CompositeState<TestState, TestEvent> = CompositeState::new("test", "Test")
            .with_region(region);

        assert_eq!(composite.regions.len(), 1);
    }

    #[test]
    fn test_hstate_simple() {
        let hstate: HState<TestState, TestEvent> = HState::simple(TestState::Idle);
        assert!(hstate.is_composite() == false);
        assert!(hstate.as_composite().is_none());
    }

    #[test]
    fn test_hstate_composite() {
        let composite: CompositeState<TestState, TestEvent> = CompositeState::new("c", "C");
        let hstate = HState::composite(composite);
        assert!(hstate.is_composite());
        assert!(hstate.as_composite().is_some());
    }

    #[test]
    fn test_history_type_variants() {
        assert_eq!(HistoryType::None, HistoryType::None);
        assert_eq!(HistoryType::Shallow, HistoryType::Shallow);
        assert_eq!(HistoryType::Deep, HistoryType::Deep);
    }

    #[test]
    fn test_hstate_machine_new() {
        let hsm: HStateMachine<TestState, TestEvent> = HStateMachine::new(HState::simple(TestState::Idle));
        assert!(hsm.history().is_empty());
        assert!(hsm.record_history);
    }

    #[test]
    fn test_hstate_machine_without_history() {
        let hsm: HStateMachine<TestState, TestEvent> = HStateMachine::new_without_history(HState::simple(TestState::Idle));
        assert!(!hsm.record_history);
    }

    #[test]
    fn test_format_hierarchy_simple() {
        let hsm: HStateMachine<TestState, TestEvent> = HStateMachine::new(HState::simple(TestState::Idle));
        let hierarchy = hsm.format_hierarchy();
        assert!(hierarchy.contains("Idle"));
        assert!(hierarchy.contains("[●]"));
    }

    #[test]
    fn test_format_hierarchy_composite() {
        let region = RegionBuilder::new()
            .with_initial_state(TestState::Idle, "idle")
            .build();

        let composite: CompositeState<TestState, TestEvent> = CompositeState::new("test", "Test")
            .with_region(region);

        let hsm: HStateMachine<TestState, TestEvent> = HStateMachine::new(HState::composite(composite));
        let hierarchy = hsm.format_hierarchy();
        assert!(hierarchy.contains("Test"));
        assert!(hierarchy.contains("[○]"));
    }
}
