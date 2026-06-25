use state_machine::{StateMachine, State, Event, Transition, TransitionBuilder};
use state_machine::error::StateMachineError;

// Test states and events
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum ConnectionState {
    Disconnected,
    Connecting,
    Connected,
    Error,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum ConnectionEvent {
    Connect,
    Connected,
    Disconnect,
    Error,
    Retry,
}

impl State for ConnectionState {}
impl Event for ConnectionEvent {}

#[test]
fn test_basic_state_transitions() {
    let mut sm = StateMachine::new(ConnectionState::Disconnected);

    sm.add_transition(Transition::new(
        ConnectionState::Disconnected,
        ConnectionState::Connecting,
        ConnectionEvent::Connect,
    ));
    sm.add_transition(Transition::new(
        ConnectionState::Connecting,
        ConnectionState::Connected,
        ConnectionEvent::Connected,
    ));
    sm.add_transition(Transition::new(
        ConnectionState::Connected,
        ConnectionState::Disconnected,
        ConnectionEvent::Disconnect,
    ));

    assert_eq!(sm.current_state(), &ConnectionState::Disconnected);

    sm.process_event(ConnectionEvent::Connect).unwrap();
    assert_eq!(sm.current_state(), &ConnectionState::Connecting);

    sm.process_event(ConnectionEvent::Connected).unwrap();
    assert_eq!(sm.current_state(), &ConnectionState::Connected);

    sm.process_event(ConnectionEvent::Disconnect).unwrap();
    assert_eq!(sm.current_state(), &ConnectionState::Disconnected);
}

#[test]
fn test_guard_conditions() {
    let mut sm = StateMachine::new(ConnectionState::Disconnected);

    sm.add_transition(
        Transition::new(
            ConnectionState::Disconnected,
            ConnectionState::Connecting,
            ConnectionEvent::Connect,
        )
        .with_guard(|_from, _to, _event| {
            // Simulate connection limit check
            true
        }),
    );

    sm.process_event(ConnectionEvent::Connect).unwrap();
    assert_eq!(sm.current_state(), &ConnectionState::Connecting);
}

#[test]
fn test_guard_rejection() {
    let mut sm = StateMachine::new(ConnectionState::Disconnected);

    sm.add_transition(
        Transition::new(
            ConnectionState::Disconnected,
            ConnectionState::Connecting,
            ConnectionEvent::Connect,
        )
        .with_guard(|_from, _to, _event| false),
    );

    let result = sm.process_event(ConnectionEvent::Connect);
    assert!(result.is_err());
    assert_eq!(sm.current_state(), &ConnectionState::Disconnected);
}

#[test]
fn test_actions() {
    let mut sm = StateMachine::new(ConnectionState::Disconnected);

    sm.add_transition(
        Transition::new(
            ConnectionState::Disconnected,
            ConnectionState::Connecting,
            ConnectionEvent::Connect,
        )
        .with_action(|_from, _to, _event| {
            // Simulate connection initialization
            Ok(())
        }),
    );

    sm.process_event(ConnectionEvent::Connect).unwrap();
    assert_eq!(sm.current_state(), &ConnectionState::Connecting);
}

#[test]
fn test_action_failure() {
    let mut sm = StateMachine::new(ConnectionState::Disconnected);

    sm.add_transition(
        Transition::new(
            ConnectionState::Disconnected,
            ConnectionState::Connecting,
            ConnectionEvent::Connect,
        )
        .with_action(|_from, _to, _event| {
            Err(StateMachineError::action_failed("connection failed"))
        }),
    );

    let result = sm.process_event(ConnectionEvent::Connect);
    assert!(result.is_err());
    assert_eq!(sm.current_state(), &ConnectionState::Disconnected);
}

#[test]
fn test_error_handling() {
    let mut sm = StateMachine::new(ConnectionState::Disconnected);

    sm.add_transition(Transition::new(
        ConnectionState::Disconnected,
        ConnectionState::Connecting,
        ConnectionEvent::Connect,
    ));
    sm.add_transition(Transition::new(
        ConnectionState::Connecting,
        ConnectionState::Error,
        ConnectionEvent::Error,
    ));
    sm.add_transition(Transition::new(
        ConnectionState::Error,
        ConnectionState::Connecting,
        ConnectionEvent::Retry,
    ));

    sm.process_event(ConnectionEvent::Connect).unwrap();
    assert_eq!(sm.current_state(), &ConnectionState::Connecting);

    sm.process_event(ConnectionEvent::Error).unwrap();
    assert_eq!(sm.current_state(), &ConnectionState::Error);

    sm.process_event(ConnectionEvent::Retry).unwrap();
    assert_eq!(sm.current_state(), &ConnectionState::Connecting);
}

#[test]
fn test_history_recording() {
    let mut sm = StateMachine::new(ConnectionState::Disconnected)
        .with_history_capacity(10);

    sm.add_transition(Transition::new(
        ConnectionState::Disconnected,
        ConnectionState::Connecting,
        ConnectionEvent::Connect,
    ));
    sm.add_transition(Transition::new(
        ConnectionState::Connecting,
        ConnectionState::Connected,
        ConnectionEvent::Connected,
    ));

    sm.process_event(ConnectionEvent::Connect).unwrap();
    sm.process_event(ConnectionEvent::Connected).unwrap();

    assert_eq!(sm.history().len(), 2);

    let entries = sm.history().entries();
    assert_eq!(entries[0].from, ConnectionState::Disconnected);
    assert_eq!(entries[0].to, ConnectionState::Connecting);
    assert_eq!(entries[1].from, ConnectionState::Connecting);
    assert_eq!(entries[1].to, ConnectionState::Connected);
}

#[test]
fn test_history_max_entries() {
    let mut sm = StateMachine::new(ConnectionState::Disconnected)
        .with_history_capacity(2);

    sm.add_transition(Transition::new(
        ConnectionState::Disconnected,
        ConnectionState::Connecting,
        ConnectionEvent::Connect,
    ));
    sm.add_transition(Transition::new(
        ConnectionState::Connecting,
        ConnectionState::Connected,
        ConnectionEvent::Connected,
    ));
    sm.add_transition(Transition::new(
        ConnectionState::Connected,
        ConnectionState::Disconnected,
        ConnectionEvent::Disconnect,
    ));

    // Add more entries than capacity
    for _ in 0..5 {
        sm.process_event(ConnectionEvent::Connect).unwrap();
        sm.process_event(ConnectionEvent::Connected).unwrap();
        sm.process_event(ConnectionEvent::Disconnect).unwrap();
    }

    assert_eq!(sm.history().len(), 2);
}

#[test]
fn test_possible_events() {
    let mut sm = StateMachine::new(ConnectionState::Disconnected);

    sm.add_transition(Transition::new(
        ConnectionState::Disconnected,
        ConnectionState::Connecting,
        ConnectionEvent::Connect,
    ));
    sm.add_transition(Transition::new(
        ConnectionState::Disconnected,
        ConnectionState::Error,
        ConnectionEvent::Error,
    ));

    let events = sm.possible_events();
    assert_eq!(events.len(), 2);
    assert!(events.contains(&&ConnectionEvent::Connect));
    assert!(events.contains(&&ConnectionEvent::Error));
}

#[test]
fn test_can_process_event() {
    let mut sm = StateMachine::new(ConnectionState::Disconnected);

    sm.add_transition(Transition::new(
        ConnectionState::Disconnected,
        ConnectionState::Connecting,
        ConnectionEvent::Connect,
    ));

    assert!(sm.can_process_event(&ConnectionEvent::Connect));
    assert!(!sm.can_process_event(&ConnectionEvent::Disconnect));
}

#[test]
fn test_transition_builder() {
    let mut sm = StateMachine::new(ConnectionState::Disconnected);

    let transition = TransitionBuilder::new()
        .from(ConnectionState::Disconnected)
        .to(ConnectionState::Connecting)
        .on(ConnectionEvent::Connect)
        .describe("Initiate connection")
        .build()
        .unwrap();

    sm.add_transition(transition);
    sm.process_event(ConnectionEvent::Connect).unwrap();
    assert_eq!(sm.current_state(), &ConnectionState::Connecting);
}

#[test]
fn test_multiple_transitions() {
    let mut sm = StateMachine::new(ConnectionState::Disconnected);

    sm.add_transitions(vec![
        Transition::new(
            ConnectionState::Disconnected,
            ConnectionState::Connecting,
            ConnectionEvent::Connect,
        ),
        Transition::new(
            ConnectionState::Connecting,
            ConnectionState::Connected,
            ConnectionEvent::Connected,
        ),
        Transition::new(
            ConnectionState::Connected,
            ConnectionState::Disconnected,
            ConnectionEvent::Disconnect,
        ),
    ]);

    assert_eq!(sm.transition_count(), 3);
}

#[test]
fn test_callbacks() {
    let mut sm = StateMachine::new(ConnectionState::Disconnected)
        .on_state_change(|from, to, event| {
            println!("State changed: {:?} -> {:?} (event: {:?})", from, to, event);
        });

    sm.add_transition(Transition::new(
        ConnectionState::Disconnected,
        ConnectionState::Connecting,
        ConnectionEvent::Connect,
    ));

    sm.process_event(ConnectionEvent::Connect).unwrap();
}

#[test]
fn test_complex_scenario() {
    let mut sm = StateMachine::new(ConnectionState::Disconnected)
        .with_history_capacity(20)
        .on_state_change(|from, to, event| {
            println!("[{:?}] {:?} -> {:?}", event, from, to);
        });

    // Define all transitions
    sm.add_transitions(vec![
        Transition::new(
            ConnectionState::Disconnected,
            ConnectionState::Connecting,
            ConnectionEvent::Connect,
        ),
        Transition::new(
            ConnectionState::Connecting,
            ConnectionState::Connected,
            ConnectionEvent::Connected,
        ),
        Transition::new(
            ConnectionState::Connecting,
            ConnectionState::Error,
            ConnectionEvent::Error,
        ),
        Transition::new(
            ConnectionState::Connected,
            ConnectionState::Disconnected,
            ConnectionEvent::Disconnect,
        ),
        Transition::new(
            ConnectionState::Error,
            ConnectionState::Connecting,
            ConnectionEvent::Retry,
        ),
    ]);

    // Simulate connection lifecycle
    sm.process_event(ConnectionEvent::Connect).unwrap();
    assert_eq!(sm.current_state(), &ConnectionState::Connecting);

    // Connection fails
    sm.process_event(ConnectionEvent::Error).unwrap();
    assert_eq!(sm.current_state(), &ConnectionState::Error);

    // Retry
    sm.process_event(ConnectionEvent::Retry).unwrap();
    assert_eq!(sm.current_state(), &ConnectionState::Connecting);

    // Success
    sm.process_event(ConnectionEvent::Connected).unwrap();
    assert_eq!(sm.current_state(), &ConnectionState::Connected);

    // Disconnect
    sm.process_event(ConnectionEvent::Disconnect).unwrap();
    assert_eq!(sm.current_state(), &ConnectionState::Disconnected);

    // Check history
    assert_eq!(sm.history().len(), 5);
}

#[test]
fn test_no_transition_error() {
    let sm = StateMachine::<ConnectionState, ConnectionEvent>::new(ConnectionState::Disconnected);
    let mut sm = sm;

    let result = sm.process_event(ConnectionEvent::Connect);
    assert!(result.is_err());

    match result {
        Err(StateMachineError::NoTransition { state, event }) => {
            assert!(state.contains("Disconnected"));
            assert!(event.contains("Connect"));
        }
        _ => panic!("Expected NoTransition error"),
    }
}

#[test]
fn test_invalid_state_error() {
    let sm = StateMachine::<ConnectionState, ConnectionEvent>::new(ConnectionState::Disconnected);
    assert_eq!(sm.current_state(), &ConnectionState::Disconnected);
}

#[test]
fn test_transition_debug() {
    let t = Transition::new(
        ConnectionState::Disconnected,
        ConnectionState::Connecting,
        ConnectionEvent::Connect,
    );
    let debug_str = format!("{:?}", t);
    assert!(debug_str.contains("Disconnected"));
    assert!(debug_str.contains("Connecting"));
    assert!(debug_str.contains("Connect"));
}

#[test]
fn test_state_machine_debug() {
    let sm = StateMachine::<ConnectionState, ConnectionEvent>::new(ConnectionState::Disconnected);
    let debug_str = format!("{:?}", sm);
    assert!(debug_str.contains("Disconnected"));
    assert!(debug_str.contains("transition_count: 0"));
}
