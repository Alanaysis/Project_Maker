"""
Workflow Engine State Machine Example

Demonstrates:
- Complex workflow with multiple paths
- Guard conditions for branching
- Context-based decisions
- Error handling and recovery
"""

import sys
from typing import Any, Dict, List

sys.path.insert(0, ".")

from src import (
    Event,
    State,
    StateMachine,
    Transition,
    FunctionGuard,
    FunctionAction,
)


# Define Workflow States
DRAFT = State("Draft")
REVIEW = State("Review")
APPROVED = State("Approved")
REJECTED = State("Rejected")
PUBLISHED = State("Published")
ARCHIVED = State("Archived")
REVISION = State("Revision")


# Define Workflow Events
SUBMIT = Event("submit")
APPROVE = Event("approve")
REJECT = Event("reject")
PUBLISH = Event("publish")
ARCHIVE = Event("archive")
REVISE = Event("revise")
RESUBMIT = Event("resubmit")


# Define Guards
def has_reviewer(from_state, to_state, event, context):
    """Check if reviewer is assigned."""
    if context is None:
        return False
    return "reviewer" in context


def has_content(from_state, to_state, event, context):
    """Check if content exists."""
    if context is None:
        return False
    content = context.get("content", "")
    return len(content.strip()) > 0


def is_approved(from_state, to_state, event, context):
    """Check if approval status is approved."""
    if context is None:
        return False
    return context.get("approval_status") == "approved"


def can_publish(from_state, to_state, event, context):
    """Check if can publish."""
    if context is None:
        return False
    return context.get("approval_status") == "approved" and context.get("content_ready", False)


def has_revision_notes(from_state, to_state, event, context):
    """Check if revision notes exist."""
    if context is None:
        return False
    notes = context.get("revision_notes", "")
    return len(notes.strip()) > 0


# Define Actions
def on_submit(from_state, to_state, event, context):
    """Action on submit."""
    if context:
        context["submitted_at"] = "2024-01-15"
        context["status"] = "submitted"
    print("  Content submitted for review")


def on_approve(from_state, to_state, event, context):
    """Action on approve."""
    if context:
        context["approval_status"] = "approved"
        context["approved_at"] = "2024-01-16"
    print("  Content approved!")


def on_reject(from_state, to_state, event, context):
    """Action on reject."""
    if context:
        context["approval_status"] = "rejected"
        context["rejected_at"] = "2024-01-16"
    print("  Content rejected")


def on_publish(from_state, to_state, event, context):
    """Action on publish."""
    if context:
        context["published_at"] = "2024-01-17"
        context["status"] = "published"
    print("  Content published!")


def on_archive(from_state, to_state, event, context):
    """Action on archive."""
    if context:
        context["archived_at"] = "2024-01-18"
        context["status"] = "archived"
    print("  Content archived")


def on_revise(from_state, to_state, event, context):
    """Action on revise."""
    if context:
        context["revision_count"] = context.get("revision_count", 0) + 1
        context["status"] = "in_revision"
    print("  Content sent for revision")


def on_resubmit(from_state, to_state, event, context):
    """Action on resubmit."""
    if context:
        context["status"] = "resubmitted"
    print("  Content resubmitted")


def log_transition(from_state, to_state, event, context):
    """Log transition."""
    print(f"  Transition: {from_state} -> {to_state}")


def create_workflow_engine() -> StateMachine:
    """
    Create a workflow engine state machine.

    Returns:
        Configured StateMachine instance
    """
    sm = StateMachine(DRAFT, enable_history=True)

    # Draft -> Review (requires content and reviewer)
    sm.add_transition(Transition(
        from_state=DRAFT,
        to_state=REVIEW,
        event=SUBMIT,
        guard=FunctionGuard(has_content, "has_content") & FunctionGuard(has_reviewer, "has_reviewer"),
        action=FunctionAction(on_submit, "submit"),
        description="Submit for review"
    ))

    # Review -> Approved
    sm.add_transition(Transition(
        from_state=REVIEW,
        to_state=APPROVED,
        event=APPROVE,
        action=FunctionAction(on_approve, "approve"),
        description="Approve content"
    ))

    # Review -> Rejected
    sm.add_transition(Transition(
        from_state=REVIEW,
        to_state=REJECTED,
        event=REJECT,
        action=FunctionAction(on_reject, "reject"),
        description="Reject content"
    ))

    # Review -> Revision
    sm.add_transition(Transition(
        from_state=REVIEW,
        to_state=REVISION,
        event=REVISE,
        guard=FunctionGuard(has_revision_notes, "has_revision_notes"),
        action=FunctionAction(on_revise, "revise"),
        description="Request revision"
    ))

    # Revision -> Review (resubmit)
    sm.add_transition(Transition(
        from_state=REVISION,
        to_state=REVIEW,
        event=RESUBMIT,
        action=FunctionAction(on_resubmit, "resubmit"),
        description="Resubmit after revision"
    ))

    # Rejected -> Revision (can revise rejected content)
    sm.add_transition(Transition(
        from_state=REJECTED,
        to_state=REVISION,
        event=REVISE,
        action=FunctionAction(on_revise, "revise"),
        description="Revise rejected content"
    ))

    # Approved -> Published
    sm.add_transition(Transition(
        from_state=APPROVED,
        to_state=PUBLISHED,
        event=PUBLISH,
        guard=FunctionGuard(can_publish, "can_publish"),
        action=FunctionAction(on_publish, "publish"),
        description="Publish content"
    ))

    # Published -> Archived
    sm.add_transition(Transition(
        from_state=PUBLISHED,
        to_state=ARCHIVED,
        event=ARCHIVE,
        action=FunctionAction(on_archive, "archive"),
        description="Archive content"
    ))

    # Add entry actions
    DRAFT.add_entry_action(lambda s, c: print(f"  Entering {s.name} state"))
    REVIEW.add_entry_action(lambda s, c: print(f"  Entering {s.name} state"))
    APPROVED.add_entry_action(lambda s, c: print(f"  Entering {s.name} state"))
    PUBLISHED.add_entry_action(lambda s, c: print(f"  Entering {s.name} state"))

    return sm


def demo_happy_path():
    """Demo successful workflow."""
    print("=" * 60)
    print("Workflow Engine - Happy Path Demo")
    print("=" * 60)

    sm = create_workflow_engine()

    context = {
        "title": "My Article",
        "content": "This is the article content...",
        "author": "John Doe",
        "reviewer": "Jane Smith",
        "content_ready": True,
    }

    print(f"\nInitial state: {sm.current_state}")
    print(f"Title: {context['title']}")

    # Submit for review
    print("\n--- Submit for Review ---")
    sm.process_event(SUBMIT, context)
    print(f"State: {sm.current_state}")

    # Approve
    print("\n--- Approve Content ---")
    sm.process_event(APPROVE, context)
    print(f"State: {sm.current_state}")

    # Publish
    print("\n--- Publish Content ---")
    sm.process_event(PUBLISH, context)
    print(f"State: {sm.current_state}")

    # Archive
    print("\n--- Archive Content ---")
    sm.process_event(ARCHIVE, context)
    print(f"State: {sm.current_state}")

    # Show final context
    print("\n--- Final Context ---")
    for key, value in context.items():
        print(f"  {key}: {value}")


def demo_rejection():
    """Demo rejection and revision workflow."""
    print("\n" + "=" * 60)
    print("Workflow Engine - Rejection & Revision Demo")
    print("=" * 60)

    sm = create_workflow_engine()

    context = {
        "title": "Draft Article",
        "content": "Initial draft content...",
        "author": "John Doe",
        "reviewer": "Jane Smith",
        "content_ready": False,
    }

    print(f"\nInitial state: {sm.current_state}")

    # Submit
    print("\n--- Submit for Review ---")
    sm.process_event(SUBMIT, context)
    print(f"State: {sm.current_state}")

    # Reject
    print("\n--- Reject Content ---")
    sm.process_event(REJECT, context)
    print(f"State: {sm.current_state}")

    # Revise
    print("\n--- Request Revision ---")
    context["revision_notes"] = "Please add more details"
    sm.process_event(REVISE, context)
    print(f"State: {sm.current_state}")

    # Resubmit
    print("\n--- Resubmit ---")
    sm.process_event(RESUBMIT, context)
    print(f"State: {sm.current_state}")

    # Approve
    print("\n--- Approve Content ---")
    sm.process_event(APPROVE, context)
    print(f"State: {sm.current_state}")

    # Publish (will fail - content not ready)
    print("\n--- Try to Publish (content not ready) ---")
    result = sm.process_event(PUBLISH, context)
    print(f"State: {sm.current_state}")
    print(f"Publish succeeded: {result}")

    # Mark content ready and publish
    print("\n--- Mark Content Ready & Publish ---")
    context["content_ready"] = True
    sm.process_event(PUBLISH, context)
    print(f"State: {sm.current_state}")


def demo_validation():
    """Demo validation failures."""
    print("\n" + "=" * 60)
    print("Workflow Engine - Validation Demo")
    print("=" * 60)

    sm = create_workflow_engine()

    # Try to submit without content
    context = {
        "title": "Empty Article",
        "content": "",
        "author": "John Doe",
        "reviewer": "Jane Smith",
    }

    print(f"\nInitial state: {sm.current_state}")
    print("Content: (empty)")

    print("\n--- Try to Submit (no content) ---")
    result = sm.process_event(SUBMIT, context)
    print(f"State: {sm.current_state}")
    print(f"Submit succeeded: {result}")

    # Add content but no reviewer
    context["content"] = "Some content..."
    del context["reviewer"]

    print("\n--- Try to Submit (no reviewer) ---")
    result = sm.process_event(SUBMIT, context)
    print(f"State: {sm.current_state}")
    print(f"Submit succeeded: {result}")

    # Add reviewer and submit
    context["reviewer"] = "Jane Smith"

    print("\n--- Submit with all requirements ---")
    result = sm.process_event(SUBMIT, context)
    print(f"State: {sm.current_state}")
    print(f"Submit succeeded: {result}")


def demo_possible_events():
    """Demo checking possible events."""
    print("\n" + "=" * 60)
    print("Workflow Engine - Possible Events Demo")
    print("=" * 60)

    sm = create_workflow_engine()

    context = {
        "title": "Article",
        "content": "Content here...",
        "reviewer": "Jane Smith",
    }

    print(f"\nState: {sm.current_state}")
    print(f"Possible events: {[str(e) for e in sm.possible_events()]}")

    # Move to review
    sm.process_event(SUBMIT, context)
    print(f"\nState: {sm.current_state}")
    print(f"Possible events: {[str(e) for e in sm.possible_events()]}")

    # Check specific events
    print(f"\nCan approve? {sm.can_process_event(APPROVE)}")
    print(f"Can reject? {sm.can_process_event(REJECT)}")
    print(f"Can publish? {sm.can_process_event(PUBLISH)}")


if __name__ == "__main__":
    demo_happy_path()
    demo_rejection()
    demo_validation()
    demo_possible_events()
