use crate::{Event, State};
use std::collections::VecDeque;
use std::fmt::Debug;
use std::time::{Duration, Instant};

/// Represents a single history entry
#[derive(Debug, Clone)]
pub struct HistoryEntry<S: State, E: Event> {
    /// Source state before transition
    pub from: S,
    /// Target state after transition
    pub to: S,
    /// Event that triggered the transition
    pub event: E,
    /// Timestamp when the transition occurred
    pub timestamp: Instant,
    /// Duration of the transition (if measured)
    pub duration: Option<Duration>,
    /// Whether the transition was successful
    pub success: bool,
    /// Optional error message if transition failed
    pub error: Option<String>,
}

impl<S: State, E: Event> HistoryEntry<S, E> {
    /// Create a successful history entry
    pub fn success(from: S, to: S, event: E) -> Self {
        Self {
            from,
            to,
            event,
            timestamp: Instant::now(),
            duration: None,
            success: true,
            error: None,
        }
    }

    /// Create a failed history entry
    pub fn failure(from: S, to: S, event: E, error: String) -> Self {
        Self {
            from,
            to,
            event,
            timestamp: Instant::now(),
            duration: None,
            success: false,
            error: Some(error),
        }
    }

    /// Set the duration for this entry
    pub fn with_duration(mut self, duration: Duration) -> Self {
        self.duration = Some(duration);
        self
    }

    /// Get a formatted string representation
    pub fn format(&self) -> String {
        let status = if self.success { "SUCCESS" } else { "FAILURE" };
        let duration_str = self.duration
            .map(|d| format!(" ({:?})", d))
            .unwrap_or_default();

        format!(
            "[{:?}] {:?} --({:?})--> {:?} {}{}",
            self.timestamp, self.from, self.event, self.to, status, duration_str
        )
    }
}

/// Manages history entries for a state machine
pub struct HistoryManager<S: State, E: Event> {
    /// Maximum number of history entries to keep
    max_entries: usize,
    /// History entries
    entries: VecDeque<HistoryEntry<S, E>>,
}

impl<S: State, E: Event> HistoryManager<S, E> {
    /// Create a new history manager with a maximum number of entries
    pub fn new(max_entries: usize) -> Self {
        Self {
            max_entries,
            entries: VecDeque::with_capacity(max_entries),
        }
    }

    /// Add a new history entry
    pub fn push(&mut self, entry: HistoryEntry<S, E>) {
        if self.entries.len() >= self.max_entries {
            self.entries.pop_front();
        }
        self.entries.push_back(entry);
    }

    /// Get the most recent entry
    pub fn last(&self) -> Option<&HistoryEntry<S, E>> {
        self.entries.back()
    }

    /// Get the number of entries
    pub fn len(&self) -> usize {
        self.entries.len()
    }

    /// Check if history is empty
    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    /// Get all entries
    pub fn entries(&self) -> &VecDeque<HistoryEntry<S, E>> {
        &self.entries
    }

    /// Get entries in reverse order (newest first)
    pub fn entries_reversed(&self) -> Vec<&HistoryEntry<S, E>> {
        self.entries.iter().rev().collect()
    }

    /// Get entries for a specific state
    pub fn entries_for_state(&self, state: &S) -> Vec<&HistoryEntry<S, E>> {
        self.entries
            .iter()
            .filter(|entry| entry.from == *state || entry.to == *state)
            .collect()
    }

    /// Get entries for a specific event
    pub fn entries_for_event(&self, event: &E) -> Vec<&HistoryEntry<S, E>> {
        self.entries
            .iter()
            .filter(|entry| entry.event == *event)
            .collect()
    }

    /// Get successful entries only
    pub fn successful_entries(&self) -> Vec<&HistoryEntry<S, E>> {
        self.entries
            .iter()
            .filter(|entry| entry.success)
            .collect()
    }

    /// Get failed entries only
    pub fn failed_entries(&self) -> Vec<&HistoryEntry<S, E>> {
        self.entries
            .iter()
            .filter(|entry| !entry.success)
            .collect()
    }

    /// Clear all history entries
    pub fn clear(&mut self) {
        self.entries.clear();
    }

    /// Get the maximum number of entries
    pub fn max_entries(&self) -> usize {
        self.max_entries
    }

    /// Format all entries as a string
    pub fn format_all(&self) -> String {
        self.entries
            .iter()
            .map(|entry| entry.format())
            .collect::<Vec<_>>()
            .join("\n")
    }
}

impl<S: State, E: Event> Default for HistoryManager<S, E> {
    fn default() -> Self {
        Self::new(100)
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
    fn test_history_entry_success() {
        let entry = HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB);
        assert_eq!(entry.from, TestState::A);
        assert_eq!(entry.to, TestState::B);
        assert_eq!(entry.event, TestEvent::GoToB);
        assert!(entry.success);
        assert!(entry.error.is_none());
    }

    #[test]
    fn test_history_entry_failure() {
        let entry = HistoryEntry::failure(
            TestState::A,
            TestState::B,
            TestEvent::GoToB,
            "guard rejected".to_string(),
        );
        assert!(!entry.success);
        assert_eq!(entry.error, Some("guard rejected".to_string()));
    }

    #[test]
    fn test_history_entry_with_duration() {
        let entry = HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB)
            .with_duration(Duration::from_millis(100));
        assert!(entry.duration.is_some());
        assert_eq!(entry.duration.unwrap(), Duration::from_millis(100));
    }

    #[test]
    fn test_history_entry_format() {
        let entry = HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB);
        let formatted = entry.format();
        assert!(formatted.contains("SUCCESS"));
        assert!(formatted.contains("A"));
        assert!(formatted.contains("B"));
        assert!(formatted.contains("GoToB"));
    }

    #[test]
    fn test_history_manager_new() {
        let manager: HistoryManager<TestState, TestEvent> = HistoryManager::new(50);
        assert_eq!(manager.max_entries(), 50);
        assert!(manager.is_empty());
        assert_eq!(manager.len(), 0);
    }

    #[test]
    fn test_history_manager_push() {
        let mut manager = HistoryManager::new(10);
        let entry = HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB);
        manager.push(entry);
        assert_eq!(manager.len(), 1);
        assert!(!manager.is_empty());
    }

    #[test]
    fn test_history_manager_max_entries() {
        let mut manager = HistoryManager::new(3);
        for _ in 0..5 {
            let entry = HistoryEntry::success(
                TestState::A,
                TestState::B,
                TestEvent::GoToB,
            );
            manager.push(entry);
        }
        assert_eq!(manager.len(), 3);
    }

    #[test]
    fn test_history_manager_last() {
        let mut manager = HistoryManager::new(10);
        assert!(manager.last().is_none());

        manager.push(HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB));
        assert!(manager.last().is_some());
        assert_eq!(manager.last().unwrap().to, TestState::B);
    }

    #[test]
    fn test_history_manager_entries() {
        let mut manager = HistoryManager::new(10);
        manager.push(HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB));
        manager.push(HistoryEntry::success(TestState::B, TestState::C, TestEvent::GoToC));

        let entries = manager.entries();
        assert_eq!(entries.len(), 2);
    }

    #[test]
    fn test_history_manager_entries_reversed() {
        let mut manager = HistoryManager::new(10);
        manager.push(HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB));
        manager.push(HistoryEntry::success(TestState::B, TestState::C, TestEvent::GoToC));

        let reversed = manager.entries_reversed();
        assert_eq!(reversed.len(), 2);
        assert_eq!(reversed[0].to, TestState::C);
        assert_eq!(reversed[1].to, TestState::B);
    }

    #[test]
    fn test_history_manager_entries_for_state() {
        let mut manager = HistoryManager::new(10);
        manager.push(HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB));
        manager.push(HistoryEntry::success(TestState::B, TestState::C, TestEvent::GoToC));
        manager.push(HistoryEntry::success(TestState::C, TestState::A, TestEvent::GoToA));

        let entries_b = manager.entries_for_state(&TestState::B);
        assert_eq!(entries_b.len(), 2);
    }

    #[test]
    fn test_history_manager_entries_for_event() {
        let mut manager = HistoryManager::new(10);
        manager.push(HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB));
        manager.push(HistoryEntry::success(TestState::B, TestState::C, TestEvent::GoToC));
        manager.push(HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB));

        let entries_go_to_b = manager.entries_for_event(&TestEvent::GoToB);
        assert_eq!(entries_go_to_b.len(), 2);
    }

    #[test]
    fn test_history_manager_successful_entries() {
        let mut manager = HistoryManager::new(10);
        manager.push(HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB));
        manager.push(HistoryEntry::failure(
            TestState::B,
            TestState::C,
            TestEvent::GoToC,
            "error".to_string(),
        ));
        manager.push(HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB));

        assert_eq!(manager.successful_entries().len(), 2);
    }

    #[test]
    fn test_history_manager_failed_entries() {
        let mut manager = HistoryManager::new(10);
        manager.push(HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB));
        manager.push(HistoryEntry::failure(
            TestState::B,
            TestState::C,
            TestEvent::GoToC,
            "error".to_string(),
        ));
        manager.push(HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB));

        assert_eq!(manager.failed_entries().len(), 1);
    }

    #[test]
    fn test_history_manager_clear() {
        let mut manager = HistoryManager::new(10);
        manager.push(HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB));
        manager.push(HistoryEntry::success(TestState::B, TestState::C, TestEvent::GoToC));
        assert_eq!(manager.len(), 2);

        manager.clear();
        assert_eq!(manager.len(), 0);
        assert!(manager.is_empty());
    }

    #[test]
    fn test_history_manager_format_all() {
        let mut manager = HistoryManager::new(10);
        manager.push(HistoryEntry::success(TestState::A, TestState::B, TestEvent::GoToB));
        manager.push(HistoryEntry::success(TestState::B, TestState::C, TestEvent::GoToC));

        let formatted = manager.format_all();
        assert!(formatted.contains("SUCCESS"));
        assert!(formatted.contains("A"));
        assert!(formatted.contains("B"));
        assert!(formatted.contains("C"));
    }

    #[test]
    fn test_history_manager_default() {
        let manager: HistoryManager<TestState, TestEvent> = HistoryManager::default();
        assert_eq!(manager.max_entries(), 100);
    }
}
