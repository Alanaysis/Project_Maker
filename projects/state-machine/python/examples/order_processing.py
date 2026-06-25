"""
Order Processing State Machine Example

Demonstrates a complete order lifecycle with:
- Multiple states (Created, Paid, Shipped, Delivered, etc.)
- Guard conditions (payment validation)
- Entry/Exit actions
- Error handling
"""

import sys
from datetime import datetime
from typing import Any, Dict

sys.path.insert(0, ".")

from src import (
    Event,
    State,
    StateMachine,
    Transition,
    TransitionBuilder,
    FunctionGuard,
    FunctionAction,
)


# Define Order States
class OrderState(State):
    """Base class for order states."""
    pass


CREATED = OrderState("Created")
VALIDATED = OrderState("Validated")
PAYMENT_PENDING = OrderState("PaymentPending")
PAID = OrderState("Paid")
SHIPPING = OrderState("Shipping")
SHIPPED = OrderState("Shipped")
DELIVERED = OrderState("Delivered")
CANCELLED = OrderState("Cancelled")
REFUNDED = OrderState("Refunded")


# Define Order Events
class OrderEvent(Event):
    """Base class for order events."""
    pass


SUBMIT = OrderEvent("submit")
VALIDATE = OrderEvent("validate")
REQUEST_PAYMENT = OrderEvent("request_payment")
CONFIRM_PAYMENT = OrderEvent("confirm_payment")
REJECT_PAYMENT = OrderEvent("reject_payment")
SHIP = OrderEvent("ship")
DELIVER = OrderEvent("deliver")
CANCEL = OrderEvent("cancel")
REFUND = OrderEvent("refund")


# Define Guards
def has_valid_items(from_state, to_state, event, context):
    """Check if order has valid items."""
    if context is None:
        return False
    items = context.get("items", [])
    return len(items) > 0 and all(item.get("quantity", 0) > 0 for item in items)


def has_sufficient_payment(from_state, to_state, event, context):
    """Check if payment is sufficient."""
    if context is None:
        return False
    total = context.get("total", 0)
    payment = context.get("payment_amount", 0)
    return payment >= total


def is_valid_address(from_state, to_state, event, context):
    """Check if shipping address is valid."""
    if context is None:
        return False
    address = context.get("shipping_address", {})
    return bool(address.get("street") and address.get("city") and address.get("zip"))


# Define Actions
def calculate_total(from_state, to_state, event, context):
    """Calculate order total."""
    if context and "items" in context:
        total = sum(item.get("price", 0) * item.get("quantity", 0) for item in context["items"])
        context["total"] = total
        print(f"  Order total calculated: ${total:.2f}")


def process_payment(from_state, to_state, event, context):
    """Process the payment."""
    if context:
        amount = context.get("payment_amount", 0)
        context["payment_processed"] = True
        context["payment_time"] = datetime.now().isoformat()
        print(f"  Payment of ${amount:.2f} processed successfully")


def send_confirmation(from_state, to_state, event, context):
    """Send order confirmation."""
    print(f"  Order confirmation sent to customer")


def notify_warehouse(from_state, to_state, event, context):
    """Notify warehouse to prepare shipment."""
    print(f"  Warehouse notified to prepare shipment")


def create_shipping_label(from_state, to_state, event, context):
    """Create shipping label."""
    if context:
        context["tracking_number"] = f"TRK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"  Shipping label created: {context['tracking_number']}")


def notify_delivery(from_state, to_state, event, context):
    """Notify customer of delivery."""
    print(f"  Customer notified of delivery")


def process_refund(from_state, to_state, event, context):
    """Process refund."""
    if context:
        amount = context.get("payment_amount", 0)
        context["refund_amount"] = amount
        context["refund_time"] = datetime.now().isoformat()
        print(f"  Refund of ${amount:.2f} processed")


def log_transition(from_state, to_state, event, context):
    """Log the transition."""
    print(f"  Transition: {from_state} -> {to_state} on {event}")


def create_order_state_machine() -> StateMachine:
    """
    Create and configure the order processing state machine.

    Returns:
        Configured StateMachine instance
    """
    sm = StateMachine(CREATED, enable_history=True)

    # Created -> Validated (when items are valid)
    sm.add_transition(
        Transition(
            from_state=CREATED,
            to_state=VALIDATED,
            event=VALIDATE,
            guard=FunctionGuard(has_valid_items, "has_valid_items"),
            action=FunctionAction(calculate_total, "calculate_total"),
            description="Validate order items"
        )
    )

    # Validated -> PaymentPending
    sm.add_transition(
        Transition(
            from_state=VALIDATED,
            to_state=PAYMENT_PENDING,
            event=REQUEST_PAYMENT,
            action=FunctionAction(log_transition, "log"),
            description="Request payment"
        )
    )

    # PaymentPending -> Paid (when payment is sufficient)
    sm.add_transition(
        Transition(
            from_state=PAYMENT_PENDING,
            to_state=PAID,
            event=CONFIRM_PAYMENT,
            guard=FunctionGuard(has_sufficient_payment, "has_sufficient_payment"),
            action=FunctionAction(process_payment, "process_payment"),
            description="Confirm payment"
        )
    )

    # PaymentPending -> Validated (when payment is rejected)
    sm.add_transition(
        Transition(
            from_state=PAYMENT_PENDING,
            to_state=VALIDATED,
            event=REJECT_PAYMENT,
            action=FunctionAction(log_transition, "log"),
            description="Reject payment"
        )
    )

    # Paid -> Shipping
    sm.add_transition(
        Transition(
            from_state=PAID,
            to_state=SHIPPING,
            event=SHIP,
            guard=FunctionGuard(is_valid_address, "is_valid_address"),
            action=FunctionAction(create_shipping_label, "create_shipping_label"),
            description="Start shipping"
        )
    )

    # Shipping -> Shipped
    sm.add_transition(
        Transition(
            from_state=SHIPPING,
            to_state=SHIPPED,
            event=DELIVER,
            action=FunctionAction(log_transition, "log"),
            description="Mark as shipped"
        )
    )

    # Shipped -> Delivered
    sm.add_transition(
        Transition(
            from_state=SHIPPED,
            to_state=DELIVERED,
            event=DELIVER,
            action=FunctionAction(notify_delivery, "notify_delivery"),
            description="Confirm delivery"
        )
    )

    # Cancel transitions (from multiple states)
    for state in [CREATED, VALIDATED, PAYMENT_PENDING]:
        sm.add_transition(
            Transition(
                from_state=state,
                to_state=CANCELLED,
                event=CANCEL,
                action=FunctionAction(log_transition, "log"),
                description=f"Cancel from {state}"
            )
        )

    # Paid -> Refunded (can only refund if paid)
    sm.add_transition(
        Transition(
            from_state=PAID,
            to_state=REFUNDED,
            event=REFUND,
            action=FunctionAction(process_refund, "process_refund"),
            description="Process refund"
        )
    )

    # Add entry actions
    VALIDATED.add_entry_action(lambda s, c: print(f"  Entering {s.name} state"))
    PAID.add_entry_action(lambda s, c: print(f"  Entering {s.name} state"))
    SHIPPED.add_entry_action(lambda s, c: print(f"  Entering {s.name} state"))
    DELIVERED.add_entry_action(lambda s, c: print(f"  Entering {s.name} state"))

    return sm


def demo():
    """Run the order processing demo."""
    print("=" * 60)
    print("Order Processing State Machine Demo")
    print("=" * 60)

    # Create state machine
    sm = create_order_state_machine()

    # Set up callbacks
    def on_state_change(from_state, to_state, event):
        print(f"\n>> State changed: {from_state} -> {to_state}")

    def on_failure(from_state, event, error):
        print(f"\n!! Transition failed: {error}")

    sm.on_state_change(on_state_change)
    sm.on_transition_failed(on_failure)

    # Initial context
    context = {
        "order_id": "ORD-001",
        "customer_id": "CUST-123",
        "items": [
            {"name": "Widget", "price": 29.99, "quantity": 2},
            {"name": "Gadget", "price": 49.99, "quantity": 1},
        ],
        "shipping_address": {
            "street": "123 Main St",
            "city": "Anytown",
            "zip": "12345",
        },
        "payment_amount": 109.97,
    }

    print(f"\nInitial state: {sm.current_state}")
    print(f"Order ID: {context['order_id']}")
    print(f"Items: {len(context['items'])}")

    # Process events
    print("\n--- Step 1: Validate Order ---")
    sm.process_event(VALIDATE, context)

    print("\n--- Step 2: Request Payment ---")
    sm.process_event(REQUEST_PAYMENT, context)

    print("\n--- Step 3: Confirm Payment ---")
    sm.process_event(CONFIRM_PAYMENT, context)

    print("\n--- Step 4: Ship Order ---")
    sm.process_event(SHIP, context)

    print("\n--- Step 5: Mark as Shipped ---")
    sm.process_event(DELIVER, context)

    print("\n--- Step 6: Confirm Delivery ---")
    sm.process_event(DELIVER, context)

    # Show history
    print("\n" + "=" * 60)
    print("Transition History:")
    print("=" * 60)
    if sm.history:
        print(sm.history.format_all())

    # Show final state
    print(f"\nFinal state: {sm.current_state}")
    print(f"Tracking number: {context.get('tracking_number', 'N/A')}")

    # Show possible events
    print(f"Possible events: {sm.possible_events()}")


def demo_cancellation():
    """Demo order cancellation."""
    print("\n" + "=" * 60)
    print("Order Cancellation Demo")
    print("=" * 60)

    sm = create_order_state_machine()

    context = {
        "order_id": "ORD-002",
        "items": [{"name": "Widget", "price": 10.00, "quantity": 1}],
    }

    print(f"\nInitial state: {sm.current_state}")

    print("\n--- Validate Order ---")
    sm.process_event(VALIDATE, context)

    print("\n--- Cancel Order ---")
    sm.process_event(CANCEL, context)

    print(f"\nFinal state: {sm.current_state}")


def demo_refund():
    """Demo order refund."""
    print("\n" + "=" * 60)
    print("Order Refund Demo")
    print("=" * 60)

    sm = create_order_state_machine()

    context = {
        "order_id": "ORD-003",
        "items": [{"name": "Widget", "price": 10.00, "quantity": 1}],
        "payment_amount": 10.00,
        "shipping_address": {"street": "123 Main St", "city": "Anytown", "zip": "12345"},
    }

    print(f"\nInitial state: {sm.current_state}")

    # Process to paid state
    sm.process_event(VALIDATE, context)
    sm.process_event(REQUEST_PAYMENT, context)
    sm.process_event(CONFIRM_PAYMENT, context)

    print(f"\nCurrent state: {sm.current_state}")

    print("\n--- Request Refund ---")
    sm.process_event(REFUND, context)

    print(f"\nFinal state: {sm.current_state}")
    print(f"Refund amount: ${context.get('refund_amount', 0):.2f}")


if __name__ == "__main__":
    demo()
    demo_cancellation()
    demo_refund()
