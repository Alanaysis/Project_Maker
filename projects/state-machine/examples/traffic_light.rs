//! Traffic Light Example
//!
//! This example demonstrates a traffic light state machine with:
//! - Simple state transitions
//! - Event-driven architecture
//! - History recording

use state_machine::{StateMachine, State, Event, Transition};

// Define states
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum TrafficLightState {
    Red,
    Yellow,
    Green,
    Off,
}

// Define events
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum TrafficLightEvent {
    TimerExpired,
    PowerOn,
    PowerOff,
    Emergency,
}

// Implement required traits
impl State for TrafficLightState {}
impl Event for TrafficLightEvent {}

fn main() {
    println!("=== Traffic Light State Machine ===\n");

    // Create state machine
    let mut sm = StateMachine::new(TrafficLightState::Off)
        .with_history_capacity(50)
        .on_state_change(|from, to, event| {
            println!("State changed: {:?} -> {:?} (event: {:?})", from, to, event);
        })
        .on_transition_failed(|state, event, error| {
            eprintln!("Transition failed: {:?} + {:?}: {}", state, event, error);
        });

    // Define transitions using builder pattern
    let transitions = vec![
        // Power on: Off -> Red
        Transition::new(TrafficLightState::Off, TrafficLightState::Red, TrafficLightEvent::PowerOn)
            .with_description("Power on the traffic light"),

        // Normal cycle: Red -> Green -> Yellow -> Red
        Transition::new(TrafficLightState::Red, TrafficLightState::Green, TrafficLightEvent::TimerExpired)
            .with_description("Timer expired, switch to green"),
        Transition::new(TrafficLightState::Green, TrafficLightState::Yellow, TrafficLightEvent::TimerExpired)
            .with_description("Timer expired, switch to yellow"),
        Transition::new(TrafficLightState::Yellow, TrafficLightState::Red, TrafficLightEvent::TimerExpired)
            .with_description("Timer expired, switch to red"),

        // Emergency: Any state -> Red
        Transition::new(TrafficLightState::Red, TrafficLightState::Red, TrafficLightEvent::Emergency)
            .with_description("Emergency stop (already red)"),
        Transition::new(TrafficLightState::Green, TrafficLightState::Red, TrafficLightEvent::Emergency)
            .with_description("Emergency stop"),
        Transition::new(TrafficLightState::Yellow, TrafficLightState::Red, TrafficLightEvent::Emergency)
            .with_description("Emergency stop"),

        // Power off: Any state -> Off
        Transition::new(TrafficLightState::Red, TrafficLightState::Off, TrafficLightEvent::PowerOff)
            .with_description("Power off"),
        Transition::new(TrafficLightState::Green, TrafficLightState::Off, TrafficLightEvent::PowerOff)
            .with_description("Power off"),
        Transition::new(TrafficLightState::Yellow, TrafficLightState::Off, TrafficLightEvent::PowerOff)
            .with_description("Power off"),
    ];

    sm.add_transitions(transitions);

    // Display transition graph
    println!("Transition Graph:");
    println!("{}", sm.format_graph());

    // Simulate traffic light operation
    println!("Simulating traffic light operation:\n");

    // Power on
    sm.process_event(TrafficLightEvent::PowerOn).unwrap();

    // Normal cycle
    for _ in 0..3 {
        sm.process_event(TrafficLightEvent::TimerExpired).unwrap();
    }

    // Emergency
    println!("\nEmergency situation!");
    sm.process_event(TrafficLightEvent::Emergency).unwrap();

    // Power off
    println!("\nPowering off...");
    sm.process_event(TrafficLightEvent::PowerOff).unwrap();

    // Display history
    println!("\nTransition History:");
    println!("{}", sm.history().format_all());

    // Display statistics
    println!("\nStatistics:");
    println!("Total transitions: {}", sm.history().len());
    println!("Successful: {}", sm.history().successful_entries().len());
    println!("Failed: {}", sm.history().failed_entries().len());

    // Try invalid transition
    println!("\nAttempting invalid transition...");
    match sm.process_event(TrafficLightEvent::TimerExpired) {
        Ok(_) => println!("Unexpected success"),
        Err(e) => println!("Expected error: {}", e),
    }
}
