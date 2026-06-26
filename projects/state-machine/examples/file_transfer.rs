//! File Transfer State Machine Example
//!
//! This example demonstrates a file transfer state machine with:
//! - Complex state transitions with error handling
//! - Guard conditions for validation
//! - Actions for state-specific behavior
//! - Retry logic with state history

use state_machine::{StateMachine, State, Event, Transition};

// Define file transfer states
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum FileState {
    Idle,
    Preparing,
    Ready,
    Transferring,
    Paused,
    Complete,
    Error,
    Cancelled,
}

// Define file transfer events
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum FileEvent {
    // Preparation events
    Prepare,
    PrepareDone,
    CancelPrepare,

    // Transfer events
    StartTransfer,
    DataChunkReceived,
    TransferComplete,
    PauseTransfer,
    ResumeTransfer,
    TransferError,

    // Final events
    Cancel,
    Retry,
    Reset,
}

impl State for FileState {}
impl Event for FileEvent {}

/// Create the file transfer transition table
fn create_file_transitions() -> Vec<Transition<FileState, FileEvent>> {
    vec![
        // === Idle state transitions ===
        Transition::new(FileState::Idle, FileState::Preparing, FileEvent::Prepare)
            .with_action(|_from, _to, _event| {
                println!("  Preparing file for transfer...");
                Ok(())
            })
            .with_description("Start preparation"),

        Transition::new(FileState::Idle, FileState::Error, FileEvent::TransferError)
            .with_guard(|_from, _to, _event| {
                println!("  [WARN] Cannot transfer from idle state");
                false
            })
            .with_description("Invalid: error from idle"),

        // === Preparing state transitions ===
        Transition::new(FileState::Preparing, FileState::Ready, FileEvent::PrepareDone)
            .with_action(|_from, _to, _event| {
                println!("  File prepared successfully, ready to transfer");
                Ok(())
            })
            .with_description("Preparation complete"),

        Transition::new(FileState::Preparing, FileState::Cancelled, FileEvent::Cancel)
            .with_action(|_from, _to, _event| {
                println!("  File preparation cancelled");
                Ok(())
            })
            .with_description("Cancel preparation"),

        Transition::new(FileState::Preparing, FileState::Error, FileEvent::TransferError)
            .with_action(|_from, _to, _event| {
                println!("  Error during preparation");
                Ok(())
            })
            .with_description("Error during preparation"),

        // === Ready state transitions ===
        Transition::new(FileState::Ready, FileState::Transferring, FileEvent::StartTransfer)
            .with_guard(|_from, _to, _event| {
                println!("  Checking file integrity...");
                println!("  Verifying network connection...");
                true
            })
            .with_action(|_from, _to, _event| {
                println!("  Starting file transfer...");
                Ok(())
            })
            .with_description("Begin transfer"),

        Transition::new(FileState::Ready, FileState::Cancelled, FileEvent::Cancel)
            .with_action(|_from, _to, _event| {
                println!("  File transfer cancelled before start");
                Ok(())
            })
            .with_description("Cancel before transfer"),

        // === Transferring state transitions ===
        Transition::new(FileState::Transferring, FileState::Transferring, FileEvent::DataChunkReceived)
            .with_action(|_from, _to, _event| {
                println!("  Data chunk received (progress: ...%)");
                Ok(())
            })
            .with_description("Receive data chunk"),

        Transition::new(FileState::Transferring, FileState::Complete, FileEvent::TransferComplete)
            .with_action(|_from, _to, _event| {
                println!("  File transfer complete!");
                Ok(())
            })
            .with_description("Transfer complete"),

        Transition::new(FileState::Transferring, FileState::Paused, FileEvent::PauseTransfer)
            .with_action(|_from, _to, _event| {
                println!("  Transfer paused");
                Ok(())
            })
            .with_description("Pause transfer"),

        Transition::new(FileState::Transferring, FileState::Error, FileEvent::TransferError)
            .with_guard(|_from, _to, _event| {
                println!("  Transfer error detected!");
                true
            })
            .with_action(|_from, _to, _event| {
                println!("  Saving partial transfer state...");
                Ok(())
            })
            .with_description("Transfer error"),

        // === Paused state transitions ===
        Transition::new(FileState::Paused, FileState::Transferring, FileEvent::ResumeTransfer)
            .with_action(|_from, _to, _event| {
                println!("  Resuming transfer...");
                Ok(())
            })
            .with_description("Resume transfer"),

        Transition::new(FileState::Paused, FileState::Cancelled, FileEvent::Cancel)
            .with_action(|_from, _to, _event| {
                println!("  Transfer cancelled while paused");
                Ok(())
            })
            .with_description("Cancel while paused"),

        Transition::new(FileState::Paused, FileState::Error, FileEvent::TransferError)
            .with_action(|_from, _to, _event| {
                println!("  Error while paused, saving state...");
                Ok(())
            })
            .with_description("Error while paused"),

        // === Complete state transitions ===
        Transition::new(FileState::Complete, FileState::Idle, FileEvent::Reset)
            .with_action(|_from, _to, _event| {
                println!("  Resetting to idle state");
                Ok(())
            })
            .with_description("Reset after completion"),

        // === Error state transitions ===
        Transition::new(FileState::Error, FileState::Transferring, FileEvent::Retry)
            .with_guard(|_from, _to, _event| {
                println!("  Attempting retry...");
                true
            })
            .with_action(|_from, _to, _event| {
                println!("  Retrying transfer from saved state");
                Ok(())
            })
            .with_description("Retry transfer"),

        Transition::new(FileState::Error, FileState::Cancelled, FileEvent::Cancel)
            .with_action(|_from, _to, _event| {
                println!("  Transfer cancelled after error");
                Ok(())
            })
            .with_description("Cancel after error"),

        Transition::new(FileState::Error, FileState::Idle, FileEvent::Reset)
            .with_action(|_from, _to, _event| {
                println!("  Resetting after error");
                Ok(())
            })
            .with_description("Reset after error"),

        // === Cancelled state transitions ===
        Transition::new(FileState::Cancelled, FileState::Idle, FileEvent::Reset)
            .with_action(|_from, _to, _event| {
                println!("  Reset after cancellation");
                Ok(())
            })
            .with_description("Reset after cancellation"),
    ]
}

fn main() {
    println!("=== File Transfer State Machine ===\n");

    // Demo 1: Successful file transfer
    println!("--- Demo 1: Successful Transfer ---");
    let mut sm = StateMachine::new(FileState::Idle)
        .with_history_capacity(50)
        .on_state_change(|from, to, event| {
            println!("[{}] {:?} -> {:?} (event: {:?})",
                chrono_lite::format_time(), from, to, event);
        });

    sm.add_transitions(create_file_transitions());

    // Simulate successful transfer
    println!("\n1. Preparing file...");
    sm.process_event(FileEvent::Prepare).unwrap();
    sm.process_event(FileEvent::PrepareDone).unwrap();

    println!("\n2. Starting transfer...");
    sm.process_event(FileEvent::StartTransfer).unwrap();

    println!("\n3. Receiving data chunks...");
    for i in 1..=5 {
        sm.process_event(FileEvent::DataChunkReceived).unwrap();
        println!("   Chunk {} received", i);
    }

    println!("\n4. Transfer complete!");
    sm.process_event(FileEvent::TransferComplete).unwrap();

    println!("\n5. Resetting...");
    sm.process_event(FileEvent::Reset).unwrap();

    println!("\nFinal state: {:?}", sm.current_state());

    // Demo 2: Transfer with error and retry
    println!("\n\n--- Demo 2: Transfer with Error & Retry ---");
    let mut sm2 = StateMachine::new(FileState::Idle)
        .with_history_capacity(50)
        .on_state_change(|from, to, event| {
            println!("[{}] {:?} -> {:?} (event: {:?})",
                chrono_lite::format_time(), from, to, event);
        });

    sm2.add_transitions(create_file_transitions());

    println!("\n1. Preparing and starting...");
    sm2.process_event(FileEvent::Prepare).unwrap();
    sm2.process_event(FileEvent::PrepareDone).unwrap();
    sm2.process_event(FileEvent::StartTransfer).unwrap();

    println!("\n2. Error during transfer!");
    sm2.process_event(FileEvent::TransferError).unwrap();

    println!("\n3. Retrying...");
    sm2.process_event(FileEvent::Retry).unwrap();

    println!("\n4. Receiving chunks after retry...");
    for i in 1..=3 {
        sm2.process_event(FileEvent::DataChunkReceived).unwrap();
        println!("   Chunk {} received", i);
    }

    println!("\n5. Transfer complete!");
    sm2.process_event(FileEvent::TransferComplete).unwrap();

    println!("\nFinal state: {:?}", sm2.current_state());

    // Demo 3: Transfer paused and resumed
    println!("\n\n--- Demo 3: Pause & Resume ---");
    let mut sm3 = StateMachine::new(FileState::Idle)
        .with_history_capacity(50);

    sm3.add_transitions(create_file_transitions());

    println!("\n1. Starting transfer...");
    sm3.process_event(FileEvent::Prepare).unwrap();
    sm3.process_event(FileEvent::PrepareDone).unwrap();
    sm3.process_event(FileEvent::StartTransfer).unwrap();

    println!("\n2. Pausing transfer...");
    sm3.process_event(FileEvent::PauseTransfer).unwrap();
    println!("   Current state: {:?}", sm3.current_state());

    println!("\n3. Resuming transfer...");
    sm3.process_event(FileEvent::ResumeTransfer).unwrap();
    println!("   Current state: {:?}", sm3.current_state());

    println!("\n4. Completing transfer...");
    for _ in 1..=3 {
        sm3.process_event(FileEvent::DataChunkReceived).unwrap();
    }
    sm3.process_event(FileEvent::TransferComplete).unwrap();

    println!("\nFinal state: {:?}", sm3.current_state());

    // Demo 4: Invalid transition attempt
    println!("\n\n--- Demo 4: Invalid Transitions ---");
    let mut sm4 = StateMachine::new(FileState::Idle);
    sm4.add_transitions(create_file_transitions());

    println!("\nAttempting to start transfer without preparation...");
    match sm4.process_event(FileEvent::StartTransfer) {
        Ok(_) => println!("  Unexpected success"),
        Err(e) => println!("  Expected error: {}", e),
    }

    println!("\nAttempting to cancel from idle...");
    match sm4.process_event(FileEvent::Cancel) {
        Ok(_) => println!("  Unexpected success"),
        Err(e) => println!("  Expected error: {}", e),
    }

    // Summary
    println!("\n\n=== Transfer Summary ===");
    println!("Demo 1 - History entries: {}", sm.history().len());
    println!("Demo 2 - History entries: {}", sm2.history().len());
    println!("Demo 3 - History entries: {}", sm3.history().len());
    println!("Demo 4 - History entries: {}", sm4.history().len());

    println!("\nSuccessful transitions: {}", sm.history().successful_entries().len());
    println!("Failed transitions: {}", sm.history().failed_entries().len());
}

/// Simple time formatting helper (since we don't want external deps)
mod chrono_lite {
    pub fn format_time() -> String {
        "now".to_string()
    }
}
