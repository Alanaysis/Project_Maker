//! Hierarchical State Machine Example
//!
//! This example demonstrates a hierarchical state machine with:
//! - Nested composite states with regions
//! - History preservation (deep and shallow)
//! - Entry/exit actions at all levels
//! - Orthogonal regions (independent sub-machines)
//!
//! ## Architecture
//!
//! ```
//! NetworkConnection (composite)
//!   ├── Region 1: Connection Lifecycle
//!   │   ├── Disconnected
//!   │   ├── Connecting
//!   │   └── Connected (composite)
//!   │       ├── Region A: Data Flow
//!   │       │   ├── Idle
//!   │       │   ├── Sending
//!   │       │   └── Receiving
//!   │       └── Region B: Security
//!   │           ├── Unencrypted
//!   │           └── Encrypted
//!   └── Region 2: Error Handling
//!       ├── Normal
//!       └── Error
//! ```

use state_machine::hierarchical::*;
use state_machine::{Event, State, Transition};

// Define connection states
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum ConnectionState {
    // Connection lifecycle states
    Disconnected,
    Connecting,
    Connected,
    // Error states
    NetworkError,
    AuthError,
    Timeout,
    // Reconnection states
    Reconnecting,
    // Final states
    Closed,
}

// Define connection events
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum ConnectionEvent {
    // Connection lifecycle events
    Connect,
    Connected,
    Disconnect,
    Close,
    // Data events
    SendData,
    DataSent,
    ReceiveData,
    DataReceived,
    // Error events
    NetworkFailed,
    AuthFailed,
    TimedOut,
    // Recovery events
    Retry,
    Reconnected,
    // Timeout events
    Timeout,
}

impl State for ConnectionState {}
impl Event for ConnectionEvent {}

/// Create the hierarchical state machine
fn create_hierarchical_connection() {
    println!("=== Hierarchical Network Connection State Machine ===\n");

    // Create the Connected composite state with two orthogonal regions
    let connected_composite = CompositeState::new("connected", "Connected")
        .with_history(HistoryType::Deep)
        .with_entry_action(|state, _event| {
            println!("  [ENTER] Connected state - establishing secure channel");
            Ok(())
        })
        .with_exit_action(|state, _event| {
            println!("  [EXIT] Connected state - closing secure channel");
            Ok(())
        })
        // Region 1: Data Flow (orthogonal to security)
        .with_region(
            RegionBuilder::new()
                .with_id(0)
                .with_initial_state(ConnectionState::Connected, "connected")
                .with_state(ConnectionState::Disconnected, "disconnected")
                .with_state(ConnectionState::Connecting, "connecting")
                .build()
        )
        // Region 2: Security Status (orthogonal to data flow)
        .with_region(
            RegionBuilder::new()
                .with_id(1)
                .with_initial_state(ConnectionState::Connected, "connected")
                .with_state(ConnectionState::AuthError, "auth_error")
                .build()
        );

    // Create the main hierarchical state machine
    let mut hsm = HStateMachine::new(HState::composite(connected_composite))
        .with_history_capacity(100);

    // Add transitions at the top level
    hsm.add_transitions(vec![
        // From disconnected to connecting
        Transition::new(
            ConnectionState::Disconnected,
            ConnectionState::Connecting,
            ConnectionEvent::Connect,
        )
        .with_action(|_from, _to, _event| {
            println!("  Initiating connection...");
            Ok(())
        })
        .with_description("Start connection"),

        // From connecting to connected (enters the composite state)
        Transition::new(
            ConnectionState::Connecting,
            ConnectionState::Connected,
            ConnectionEvent::Connected,
        )
        .with_guard(|_from, _to, _event| {
            println!("  Connection authenticated successfully");
            true
        })
        .with_action(|_from, _to, _event| {
            println!("  Connection established!");
            Ok(())
        })
        .with_description("Connection established"),

        // From connecting to timeout
        Transition::new(
            ConnectionState::Connecting,
            ConnectionState::Timeout,
            ConnectionEvent::TimedOut,
        )
        .with_action(|_from, _to, _event| {
            println!("  Connection timed out");
            Ok(())
        })
        .with_description("Connection timeout"),

        // From timeout to reconnecting
        Transition::new(
            ConnectionState::Timeout,
            ConnectionState::Reconnecting,
            ConnectionEvent::Retry,
        )
        .with_action(|_from, _to, _event| {
            println!("  Attempting to reconnect...");
            Ok(())
        })
        .with_description("Retry connection"),

        // From reconnecting back to connecting
        Transition::new(
            ConnectionState::Reconnecting,
            ConnectionState::Connecting,
            ConnectionEvent::Connect,
        )
        .with_action(|_from, _to, _event| {
            println!("  Reconnecting...");
            Ok(())
        })
        .with_description("Reconnect attempt"),

        // From error states to disconnected
        Transition::new(
            ConnectionState::NetworkError,
            ConnectionState::Disconnected,
            ConnectionEvent::Disconnect,
        )
        .with_action(|_from, _to, _event| {
            println!("  Network error - disconnecting");
            Ok(())
        })
        .with_description("Disconnect after network error"),

        Transition::new(
            ConnectionState::AuthError,
            ConnectionState::Disconnected,
            ConnectionEvent::Disconnect,
        )
        .with_action(|_from, _to, _event| {
            println!("  Auth error - disconnecting");
            Ok(())
        })
        .with_description("Disconnect after auth error"),

        Transition::new(
            ConnectionState::Timeout,
            ConnectionState::Disconnected,
            ConnectionEvent::Disconnect,
        )
        .with_action(|_from, _to, _event| {
            println!("  Timeout - disconnecting");
            Ok(())
        })
        .with_description("Disconnect after timeout"),

        // From error states to reconnecting
        Transition::new(
            ConnectionState::NetworkError,
            ConnectionState::Reconnecting,
            ConnectionEvent::Retry,
        )
        .with_action(|_from, _to, _event| {
            println!("  Retrying after network error");
            Ok(())
        })
        .with_description("Retry after network error"),

        Transition::new(
            ConnectionState::AuthError,
            ConnectionState::Reconnecting,
            ConnectionEvent::Retry,
        )
        .with_action(|_from, _to, _event| {
            println!("  Retrying after auth error");
            Ok(())
        })
        .with_description("Retry after auth error"),

        // From reconnecting to error
        Transition::new(
            ConnectionState::Reconnecting,
            ConnectionState::NetworkError,
            ConnectionEvent::NetworkFailed,
        )
        .with_action(|_from, _to, _event| {
            println!("  Reconnection failed");
            Ok(())
        })
        .with_description("Reconnection failed"),

        // Close connections
        Transition::new(
            ConnectionState::Connected,
            ConnectionState::Closed,
            ConnectionEvent::Close,
        )
        .with_action(|_from, _to, _event| {
            println!("  Connection closed gracefully");
            Ok(())
        })
        .with_description("Close connection"),

        Transition::new(
            ConnectionState::Disconnected,
            ConnectionState::Closed,
            ConnectionEvent::Close,
        )
        .with_action(|_from, _to, _event| {
            println!("  Already disconnected, marking as closed");
            Ok(())
        })
        .with_description("Close from disconnected"),

        Transition::new(
            ConnectionState::Reconnecting,
            ConnectionState::Closed,
            ConnectionEvent::Close,
        )
        .with_action(|_from, _to, _event| {
            println!("  Cancelling reconnection, closing");
            Ok(())
        })
        .with_description("Close during reconnection"),
    ]);

    // Display the hierarchy
    println!("State Machine Hierarchy:");
    println!("{}", hsm.format_hierarchy());
    println!();

    // === Demo 1: Successful connection lifecycle ===
    println!("--- Demo 1: Successful Connection Lifecycle ---");
    let mut sm1 = HStateMachine::new(HState::simple(ConnectionState::Disconnected))
        .with_history_capacity(50);

    sm1.add_transitions(vec![
        Transition::new(
            ConnectionState::Disconnected,
            ConnectionState::Connecting,
            ConnectionEvent::Connect,
        )
        .with_action(|_from, _to, _event| {
            println!("  [ACTION] Connecting...");
            Ok(())
        }),
        Transition::new(
            ConnectionState::Connecting,
            ConnectionState::Connected,
            ConnectionEvent::Connected,
        )
        .with_guard(|_from, _to, _event| {
            println!("  [GUARD] Authentication successful");
            true
        })
        .with_action(|_from, _to, _event| {
            println!("  [ACTION] Connection established with TLS");
            Ok(())
        }),
        Transition::new(
            ConnectionState::Connected,
            ConnectionState::Disconnected,
            ConnectionEvent::Disconnect,
        )
        .with_action(|_from, _to, _event| {
            println!("  [ACTION] Disconnecting gracefully");
            Ok(())
        }),
    ]);

    println!("\n1. Connecting...");
    sm1.process_event(ConnectionEvent::Connect).unwrap();
    println!("   State: {:?}", sm1.as_simple_state().unwrap());

    println!("\n2. Connected!");
    sm1.process_event(ConnectionEvent::Connected).unwrap();
    println!("   State: {:?}", sm1.as_simple_state().unwrap());

    println!("\n3. Sending data...");
    sm1.process_event(ConnectionEvent::SendData).unwrap_or_else(|e| {
        println!("   (No transition for SendData in flat state)");
    });

    println!("\n4. Disconnecting...");
    sm1.process_event(ConnectionEvent::Disconnect).unwrap();
    println!("   State: {:?}", sm1.as_simple_state().unwrap());

    println!("\nHistory:");
    for entry in sm1.history().entries() {
        println!("  {}", entry.format());
    }

    // === Demo 2: Connection with retry ===
    println!("\n\n--- Demo 2: Connection with Timeout & Retry ---");
    let mut sm2 = HStateMachine::new(HState::simple(ConnectionState::Disconnected))
        .with_history_capacity(50);

    sm2.add_transitions(vec![
        Transition::new(
            ConnectionState::Disconnected,
            ConnectionState::Connecting,
            ConnectionEvent::Connect,
        )
        .with_action(|_from, _to, _event| {
            println!("  [ACTION] Connecting...");
            Ok(())
        }),
        Transition::new(
            ConnectionState::Connecting,
            ConnectionState::Timeout,
            ConnectionEvent::TimedOut,
        )
        .with_action(|_from, _to, _event| {
            println!("  [ACTION] Connection timed out after 30s");
            Ok(())
        }),
        Transition::new(
            ConnectionState::Timeout,
            ConnectionState::Reconnecting,
            ConnectionEvent::Retry,
        )
        .with_action(|_from, _to, _event| {
            println!("  [ACTION] Attempting automatic retry...");
            Ok(())
        }),
        Transition::new(
            ConnectionState::Reconnecting,
            ConnectionState::Connecting,
            ConnectionEvent::Connect,
        )
        .with_action(|_from, _to, _event| {
            println!("  [ACTION] Reconnecting...");
            Ok(())
        }),
        Transition::new(
            ConnectionState::Connecting,
            ConnectionState::Connected,
            ConnectionEvent::Connected,
        )
        .with_guard(|_from, _to, _event| {
            println!("  [GUARD] Reconnection successful!");
            true
        })
        .with_action(|_from, _to, _event| {
            println!("  [ACTION] Reconnected with TLS");
            Ok(())
        }),
        Transition::new(
            ConnectionState::Connected,
            ConnectionState::Disconnected,
            ConnectionEvent::Disconnect,
        )
        .with_action(|_from, _to, _event| {
            println!("  [ACTION] Disconnecting");
            Ok(())
        }),
    ]);

    println!("\n1. First connection attempt...");
    sm2.process_event(ConnectionEvent::Connect).unwrap();
    println!("   State: {:?}", sm2.as_simple_state().unwrap());

    println!("\n2. Timeout!");
    sm2.process_event(ConnectionEvent::TimedOut).unwrap();
    println!("   State: {:?}", sm2.as_simple_state().unwrap());

    println!("\n3. Auto-retrying...");
    sm2.process_event(ConnectionEvent::Retry).unwrap();
    println!("   State: {:?}", sm2.as_simple_state().unwrap());

    println!("\n4. Reconnecting...");
    sm2.process_event(ConnectionEvent::Connect).unwrap();
    println!("   State: {:?}", sm2.as_simple_state().unwrap());

    println!("\n5. Reconnected!");
    sm2.process_event(ConnectionEvent::Connected).unwrap();
    println!("   State: {:?}", sm2.as_simple_state().unwrap());

    println!("\n6. Disconnecting...");
    sm2.process_event(ConnectionEvent::Disconnect).unwrap();
    println!("   State: {:?}", sm2.as_simple_state().unwrap());

    println!("\nHistory:");
    for entry in sm2.history().entries() {
        println!("  {}", entry.format());
    }

    // === Demo 3: Auth error and recovery ===
    println!("\n\n--- Demo 3: Authentication Error & Recovery ---");
    let mut sm3 = HStateMachine::new(HState::simple(ConnectionState::Disconnected))
        .with_history_capacity(50);

    sm3.add_transitions(vec![
        Transition::new(
            ConnectionState::Disconnected,
            ConnectionState::Connecting,
            ConnectionEvent::Connect,
        ),
        Transition::new(
            ConnectionState::Connecting,
            ConnectionState::AuthError,
            ConnectionEvent::AuthFailed,
        )
        .with_action(|_from, _to, _event| {
            println!("  [ACTION] Authentication failed - invalid credentials");
            Ok(())
        }),
        Transition::new(
            ConnectionState::AuthError,
            ConnectionState::Reconnecting,
            ConnectionEvent::Retry,
        )
        .with_action(|_from, _to, _event| {
            println!("  [ACTION] Updating credentials and retrying...");
            Ok(())
        }),
        Transition::new(
            ConnectionState::Reconnecting,
            ConnectionState::Connecting,
            ConnectionEvent::Connect,
        ),
        Transition::new(
            ConnectionState::Connecting,
            ConnectionState::Connected,
            ConnectionEvent::Connected,
        )
        .with_action(|_from, _to, _event| {
            println!("  [ACTION] Authenticated successfully with new credentials");
            Ok(())
        }),
        Transition::new(
            ConnectionState::Connected,
            ConnectionState::Closed,
            ConnectionEvent::Close,
        )
        .with_action(|_from, _to, _event| {
            println!("  [ACTION] Connection closed");
            Ok(())
        }),
    ]);

    println!("\n1. Connecting with invalid credentials...");
    sm3.process_event(ConnectionEvent::Connect).unwrap();

    println!("\n2. Auth failed!");
    sm3.process_event(ConnectionEvent::AuthFailed).unwrap();
    println!("   State: {:?}", sm3.as_simple_state().unwrap());

    println!("\n3. Updating credentials and retrying...");
    sm3.process_event(ConnectionEvent::Retry).unwrap();
    sm3.process_event(ConnectionEvent::Connect).unwrap();

    println!("\n4. Authenticated with new credentials!");
    sm3.process_event(ConnectionEvent::Connected).unwrap();
    println!("   State: {:?}", sm3.as_simple_state().unwrap());

    println!("\n5. Closing connection...");
    sm3.process_event(ConnectionEvent::Close).unwrap();
    println!("   State: {:?}", sm3.as_simple_state().unwrap());

    // Summary
    println!("\n\n=== Hierarchical State Machine Summary ===");
    println!("Demo 1 transitions: {}", sm1.history().len());
    println!("Demo 2 transitions: {}", sm2.history().len());
    println!("Demo 3 transitions: {}", sm3.history().len());

    println!("\nSuccessful: {}", sm1.history().successful_entries().len());
    println!("Failed: {}", sm1.history().failed_entries().len());
}

fn main() {
    create_hierarchical_connection();
}
