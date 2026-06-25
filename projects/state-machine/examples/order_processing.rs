//! Order Processing Example
//!
//! This example demonstrates an order processing state machine with:
//! - Complex state transitions
//! - Guard conditions
//! - Actions on transitions
//! - Error handling

use state_machine::{StateMachine, State, Event, Transition};
use std::sync::atomic::{AtomicU32, Ordering};

// Define order states
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum OrderState {
    Created,
    Validated,
    Paid,
    Shipped,
    Delivered,
    Cancelled,
    Refunded,
}

// Define order events
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum OrderEvent {
    Validate,
    Pay,
    Ship,
    Deliver,
    Cancel,
    Refund,
}

impl State for OrderState {}
impl Event for OrderEvent {}

// Global counter for demo purposes
static PAYMENT_ATTEMPTS: AtomicU32 = AtomicU32::new(0);

fn create_order_transitions() -> Vec<Transition<OrderState, OrderEvent>> {
    vec![
        // Created -> Validated
        Transition::new(OrderState::Created, OrderState::Validated, OrderEvent::Validate)
            .with_guard(|_from, _to, _event| {
                // In real app, validate order details
                println!("  Validating order...");
                true
            })
            .with_action(|_from, _to, _event| {
                println!("  Order validated successfully");
                Ok(())
            })
            .with_description("Validate order details"),

        // Validated -> Paid
        Transition::new(OrderState::Validated, OrderState::Paid, OrderEvent::Pay)
            .with_guard(|_from, _to, _event| {
                // Simulate payment validation
                PAYMENT_ATTEMPTS.fetch_add(1, Ordering::SeqCst);
                let success = PAYMENT_ATTEMPTS.load(Ordering::SeqCst) <= 3;
                println!("  Processing payment... (success: {})", success);
                success
            })
            .with_action(|_from, _to, _event| {
                println!("  Payment processed");
                Ok(())
            })
            .with_description("Process payment"),

        // Paid -> Shipped
        Transition::new(OrderState::Paid, OrderState::Shipped, OrderEvent::Ship)
            .with_guard(|_from, _to, _event| {
                println!("  Checking inventory...");
                true
            })
            .with_action(|_from, _to, _event| {
                println!("  Order shipped");
                Ok(())
            })
            .with_description("Ship order"),

        // Shipped -> Delivered
        Transition::new(OrderState::Shipped, OrderState::Delivered, OrderEvent::Deliver)
            .with_action(|_from, _to, _event| {
                println!("  Order delivered");
                Ok(())
            })
            .with_description("Confirm delivery"),

        // Cancel transitions
        Transition::new(OrderState::Created, OrderState::Cancelled, OrderEvent::Cancel)
            .with_description("Cancel order"),
        Transition::new(OrderState::Validated, OrderState::Cancelled, OrderEvent::Cancel)
            .with_description("Cancel order"),
        Transition::new(OrderState::Paid, OrderState::Refunded, OrderEvent::Cancel)
            .with_action(|_from, _to, _event| {
                println!("  Processing refund...");
                Ok(())
            })
            .with_description("Cancel and refund"),

        // Refund from paid state
        Transition::new(OrderState::Paid, OrderState::Refunded, OrderEvent::Refund)
            .with_action(|_from, _to, _event| {
                println!("  Processing refund...");
                Ok(())
            })
            .with_description("Refund order"),
    ]
}

fn main() {
    println!("=== Order Processing State Machine ===\n");

    // Create state machine
    let mut sm = StateMachine::new(OrderState::Created)
        .with_history_capacity(100)
        .on_state_change(|from, to, event| {
            println!("[ORDER] {:?} -> {:?} (event: {:?})", from, to, event);
        });

    sm.add_transitions(create_order_transitions());

    // Display transition graph
    println!("Order Processing Flow:");
    println!("{}", sm.format_graph());

    // Simulate successful order
    println!("--- Successful Order ---");
    sm.process_event(OrderEvent::Validate).unwrap();
    sm.process_event(OrderEvent::Pay).unwrap();
    sm.process_event(OrderEvent::Ship).unwrap();
    sm.process_event(OrderEvent::Deliver).unwrap();

    println!("\nFinal state: {:?}", sm.current_state());

    // Reset for next simulation
    let mut sm2 = StateMachine::new(OrderState::Created)
        .with_history_capacity(100)
        .on_state_change(|from, to, event| {
            println!("[ORDER] {:?} -> {:?} (event: {:?})", from, to, event);
        });

    // Add same transitions
    sm2.add_transitions(create_order_transitions());

    // Simulate cancelled order
    println!("\n--- Cancelled Order ---");
    sm2.process_event(OrderEvent::Validate).unwrap();
    sm2.process_event(OrderEvent::Cancel).unwrap();

    println!("\nFinal state: {:?}", sm2.current_state());

    // Display history
    println!("\nOrder 1 History:");
    println!("{}", sm.history().format_all());

    println!("\nOrder 2 History:");
    println!("{}", sm2.history().format_all());

    // Demonstrate error handling
    println!("\n--- Error Handling ---");
    let mut sm3 = StateMachine::new(OrderState::Created);
    sm3.add_transition(
        Transition::new(OrderState::Created, OrderState::Paid, OrderEvent::Pay)
            .with_guard(|_from, _to, _event| false),
    );

    match sm3.process_event(OrderEvent::Pay) {
        Ok(_) => println!("Unexpected success"),
        Err(e) => println!("Expected error: {}", e),
    }
}
