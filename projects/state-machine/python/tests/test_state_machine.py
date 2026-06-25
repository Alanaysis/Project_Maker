"""
Tests for the State Machine Framework.
"""

import sys
import unittest
from datetime import datetime

sys.path.insert(0, "..")

from src import (
    Event,
    State,
    HierarchicalState,
    StateMachine,
    HierarchicalStateMachine,
    Transition,
    TransitionBuilder,
    Guard,
    FunctionGuard,
    Action,
    FunctionAction,
    EntryAction,
    ExitAction,
    TransitionAction,
    HistoryManager,
    HistoryEntry,
    StateMachineError,
    TransitionError,
    GuardRejectedError,
    InvalidStateError,
    InvalidEventError,
)


class TestState(unittest.TestCase):
    """Test State class."""

    def test_create_state(self):
        """Test creating a state."""
        state = State("TestState")
        self.assertEqual(state.name, "TestState")

    def test_state_equality(self):
        """Test state equality."""
        state1 = State("Test")
        state2 = State("Test")
        state3 = State("Other")
        self.assertEqual(state1, state2)
        self.assertNotEqual(state1, state3)

    def test_state_hash(self):
        """Test state hashing."""
        state1 = State("Test")
        state2 = State("Test")
        self.assertEqual(hash(state1), hash(state2))

    def test_state_metadata(self):
        """Test state metadata."""
        state = State("Test", key="value", num=42)
        self.assertEqual(state.metadata["key"], "value")
        self.assertEqual(state.metadata["num"], 42)

    def test_entry_action(self):
        """Test entry action."""
        state = State("Test")
        action_called = []
        state.add_entry_action(lambda s, c: action_called.append(True))
        state.on_enter()
        self.assertEqual(len(action_called), 1)

    def test_exit_action(self):
        """Test exit action."""
        state = State("Test")
        action_called = []
        state.add_exit_action(lambda s, c: action_called.append(True))
        state.on_exit()
        self.assertEqual(len(action_called), 1)


class TestHierarchicalState(unittest.TestCase):
    """Test HierarchicalState class."""

    def test_create_hierarchical_state(self):
        """Test creating a hierarchical state."""
        state = HierarchicalState("Parent")
        self.assertEqual(state.name, "Parent")

    def test_add_sub_state(self):
        """Test adding sub-states."""
        parent = HierarchicalState("Parent")
        child1 = State("Child1")
        child2 = State("Child2")
        parent.add_sub_state(child1)
        parent.add_sub_state(child2)
        self.assertEqual(len(parent.sub_states), 2)

    def test_initial_state(self):
        """Test initial state setting."""
        parent = HierarchicalState("Parent")
        child1 = State("Child1")
        child2 = State("Child2")
        parent.add_sub_state(child1)
        parent.add_sub_state(child2)
        parent.initial_state = "Child2"
        self.assertEqual(parent.initial_state, "Child2")

    def test_activate(self):
        """Test state activation."""
        parent = HierarchicalState("Parent")
        child = State("Child")
        parent.add_sub_state(child)
        parent.initial_state = "Child"
        parent.activate()
        self.assertEqual(parent.current_sub_state, child)

    def test_history(self):
        """Test history state."""
        parent = HierarchicalState("Parent", use_history=True)
        child1 = State("Child1")
        child2 = State("Child2")
        parent.add_sub_state(child1)
        parent.add_sub_state(child2)
        parent.initial_state = "Child1"

        # Activate and transition
        parent.activate()
        parent.transition_to("Child2")
        parent.deactivate()

        # Check history
        self.assertEqual(parent.history_state, "Child2")


class TestEvent(unittest.TestCase):
    """Test Event class."""

    def test_create_event(self):
        """Test creating an event."""
        event = Event("TestEvent")
        self.assertEqual(event.name, "TestEvent")

    def test_event_equality(self):
        """Test event equality."""
        event1 = Event("Test")
        event2 = Event("Test")
        event3 = Event("Other")
        self.assertEqual(event1, event2)
        self.assertNotEqual(event1, event3)

    def test_event_data(self):
        """Test event data."""
        event = Event("Test", key="value", num=42)
        self.assertEqual(event.data["key"], "value")
        self.assertEqual(event.data["num"], 42)

    def test_event_with_data(self):
        """Test creating event with data."""
        event1 = Event("Test")
        event2 = event1.with_data(key="value")
        self.assertEqual(event2.data["key"], "value")


class TestGuard(unittest.TestCase):
    """Test Guard classes."""

    def test_function_guard(self):
        """Test function guard."""
        guard = FunctionGuard(lambda f, t, e, c: True)
        self.assertTrue(guard.check("A", "B", "E", {}))

    def test_and_guard(self):
        """Test AND guard combination."""
        guard1 = FunctionGuard(lambda f, t, e, c: True)
        guard2 = FunctionGuard(lambda f, t, e, c: True)
        combined = guard1 & guard2
        self.assertTrue(combined.check("A", "B", "E", {}))

    def test_or_guard(self):
        """Test OR guard combination."""
        guard1 = FunctionGuard(lambda f, t, e, c: True)
        guard2 = FunctionGuard(lambda f, t, e, c: False)
        combined = guard1 | guard2
        self.assertTrue(combined.check("A", "B", "E", {}))

    def test_not_guard(self):
        """Test NOT guard."""
        guard = FunctionGuard(lambda f, t, e, c: True)
        negated = ~guard
        self.assertFalse(negated.check("A", "B", "E", {}))


class TestAction(unittest.TestCase):
    """Test Action classes."""

    def test_function_action(self):
        """Test function action."""
        results = []
        action = FunctionAction(lambda f, t, e, c: results.append((f, t, e)))
        action.execute("A", "B", "E", {})
        self.assertEqual(results, [("A", "B", "E")])

    def test_entry_action(self):
        """Test entry action."""
        results = []
        action = EntryAction(lambda s, c: results.append(s))
        action.execute("A", "B", "E", {})
        self.assertEqual(results, ["B"])

    def test_exit_action(self):
        """Test exit action."""
        results = []
        action = ExitAction(lambda s, c: results.append(s))
        action.execute("A", "B", "E", {})
        self.assertEqual(results, ["A"])

    def test_transition_action(self):
        """Test transition action."""
        results = []
        action = TransitionAction(lambda f, t, e, c: results.append((f, t, e)))
        action.execute("A", "B", "E", {})
        self.assertEqual(results, [("A", "B", "E")])


class TestTransition(unittest.TestCase):
    """Test Transition class."""

    def test_create_transition(self):
        """Test creating a transition."""
        from_state = State("From")
        to_state = State("To")
        event = Event("Test")
        transition = Transition(from_state, to_state, event)
        self.assertEqual(transition.from_state, from_state)
        self.assertEqual(transition.to_state, to_state)
        self.assertEqual(transition.event, event)

    def test_can_transition(self):
        """Test transition guard check."""
        transition = Transition(
            State("From"),
            State("To"),
            Event("Test"),
            guard=FunctionGuard(lambda f, t, e, c: True)
        )
        self.assertTrue(transition.can_transition({}))

    def test_execute_action(self):
        """Test transition action execution."""
        results = []
        transition = Transition(
            State("From"),
            State("To"),
            Event("Test"),
            action=FunctionAction(lambda f, t, e, c: results.append(True))
        )
        transition.execute({})
        self.assertEqual(results, [True])

    def test_matches(self):
        """Test transition matching."""
        from_state = State("From")
        to_state = State("To")
        event = Event("Test")
        transition = Transition(from_state, to_state, event)
        self.assertTrue(transition.matches(from_state, event))
        self.assertFalse(transition.matches(to_state, event))


class TestTransitionBuilder(unittest.TestCase):
    """Test TransitionBuilder class."""

    def test_build_transition(self):
        """Test building a transition."""
        transition = (TransitionBuilder()
            .from_state(State("From"))
            .to_state(State("To"))
            .on(Event("Test"))
            .describe("Test transition")
            .build())
        self.assertEqual(transition.from_state, State("From"))
        self.assertEqual(transition.to_state, State("To"))
        self.assertEqual(transition.event, Event("Test"))
        self.assertEqual(transition.description, "Test transition")

    def test_build_with_guard(self):
        """Test building with guard."""
        transition = (TransitionBuilder()
            .from_state(State("From"))
            .to_state(State("To"))
            .on(Event("Test"))
            .when(lambda f, t, e, c: True)
            .build())
        self.assertTrue(transition.can_transition({}))

    def test_build_with_action(self):
        """Test building with action."""
        results = []
        transition = (TransitionBuilder()
            .from_state(State("From"))
            .to_state(State("To"))
            .on(Event("Test"))
            .do(lambda f, t, e, c: results.append(True))
            .build())
        transition.execute({})
        self.assertEqual(results, [True])

    def test_build_missing_fields(self):
        """Test build with missing fields."""
        builder = TransitionBuilder()
        with self.assertRaises(ValueError):
            builder.build()


class TestStateMachine(unittest.TestCase):
    """Test StateMachine class."""

    def test_create_state_machine(self):
        """Test creating a state machine."""
        sm = StateMachine(State("Initial"))
        self.assertEqual(sm.current_state, State("Initial"))

    def test_add_transition(self):
        """Test adding transitions."""
        sm = StateMachine(State("A"))
        sm.add_transition(Transition(State("A"), State("B"), Event("E")))
        self.assertEqual(len(sm.transitions), 1)

    def test_process_event(self):
        """Test processing events."""
        sm = StateMachine(State("A"))
        sm.add_transition(Transition(State("A"), State("B"), Event("E")))
        result = sm.process_event(Event("E"))
        self.assertTrue(result)
        self.assertEqual(sm.current_state, State("B"))

    def test_process_event_no_transition(self):
        """Test processing event with no transition."""
        sm = StateMachine(State("A"))
        result = sm.process_event(Event("E"))
        self.assertFalse(result)
        self.assertEqual(sm.current_state, State("A"))

    def test_guard_rejection(self):
        """Test guard rejection."""
        sm = StateMachine(State("A"))
        sm.add_transition(Transition(
            State("A"),
            State("B"),
            Event("E"),
            guard=FunctionGuard(lambda f, t, e, c: False)
        ))
        result = sm.process_event(Event("E"))
        self.assertFalse(result)
        self.assertEqual(sm.current_state, State("A"))

    def test_transition_action(self):
        """Test transition action execution."""
        results = []
        sm = StateMachine(State("A"))
        sm.add_transition(Transition(
            State("A"),
            State("B"),
            Event("E"),
            action=FunctionAction(lambda f, t, e, c: results.append(True))
        ))
        sm.process_event(Event("E"))
        self.assertEqual(results, [True])

    def test_entry_exit_actions(self):
        """Test entry and exit actions."""
        results = []
        state_a = State("A")
        state_b = State("B")
        state_a.add_exit_action(lambda s, c: results.append("exit_A"))
        state_b.add_entry_action(lambda s, c: results.append("enter_B"))

        sm = StateMachine(state_a)
        sm.add_transition(Transition(state_a, state_b, Event("E")))
        sm.process_event(Event("E"))
        self.assertEqual(results, ["exit_A", "enter_B"])

    def test_can_process_event(self):
        """Test checking if event can be processed."""
        sm = StateMachine(State("A"))
        sm.add_transition(Transition(State("A"), State("B"), Event("E")))
        self.assertTrue(sm.can_process_event(Event("E")))
        self.assertFalse(sm.can_process_event(Event("F")))

    def test_possible_events(self):
        """Test getting possible events."""
        sm = StateMachine(State("A"))
        sm.add_transition(Transition(State("A"), State("B"), Event("E1")))
        sm.add_transition(Transition(State("A"), State("C"), Event("E2")))
        events = sm.possible_events()
        self.assertEqual(len(events), 2)

    def test_history(self):
        """Test history recording."""
        sm = StateMachine(State("A"), enable_history=True)
        sm.add_transition(Transition(State("A"), State("B"), Event("E")))
        sm.process_event(Event("E"))
        self.assertIsNotNone(sm.history)
        self.assertEqual(sm.history.len(), 1)

    def test_context(self):
        """Test context handling."""
        sm = StateMachine(State("A"))
        sm.context = {"key": "value"}
        self.assertEqual(sm.context["key"], "value")

    def test_callbacks(self):
        """Test callbacks."""
        state_changes = []
        sm = StateMachine(State("A"))
        sm.on_state_change(lambda f, t, e: state_changes.append((f, t, e)))
        sm.add_transition(Transition(State("A"), State("B"), Event("E")))
        sm.process_event(Event("E"))
        self.assertEqual(len(state_changes), 1)

    def test_reset(self):
        """Test resetting state machine."""
        sm = StateMachine(State("A"))
        sm.add_transition(Transition(State("A"), State("B"), Event("E")))
        sm.process_event(Event("E"))
        sm.reset()
        self.assertEqual(sm.current_state, State("A"))


class TestHierarchicalStateMachine(unittest.TestCase):
    """Test HierarchicalStateMachine class."""

    def test_create_hsm(self):
        """Test creating a hierarchical state machine."""
        hsm = HierarchicalStateMachine(State("Initial"))
        self.assertEqual(hsm.current_state, State("Initial"))

    def test_hierarchical_transitions(self):
        """Test transitions with hierarchical states."""
        idle = State("Idle")
        active = HierarchicalState("Active")
        processing = State("Processing")
        active.add_sub_state(processing)
        active.initial_state = "Processing"

        hsm = HierarchicalStateMachine(idle)
        hsm.add_transition(Transition(idle, active, Event("Activate")))

        hsm.process_event(Event("Activate"))
        self.assertEqual(hsm.current_state, processing)

    def test_state_stack(self):
        """Test state stack."""
        idle = State("Idle")
        active = HierarchicalState("Active")
        processing = State("Processing")
        active.add_sub_state(processing)
        active.initial_state = "Processing"

        hsm = HierarchicalStateMachine(idle)
        hsm.add_transition(Transition(idle, active, Event("Activate")))
        hsm.process_event(Event("Activate"))

        self.assertEqual(len(hsm.state_stack), 2)
        self.assertEqual(hsm.state_stack[0], active)
        self.assertEqual(hsm.state_stack[1], processing)

    def test_event_bubbling(self):
        """Test event bubbling."""
        parent = HierarchicalState("Parent")
        child = State("Child")
        parent.add_sub_state(child)
        parent.initial_state = "Child"

        target = State("Target")

        hsm = HierarchicalStateMachine(parent)
        hsm.add_transition(Transition(parent, target, Event("E")))
        hsm.process_event(Event("E"))

        self.assertEqual(hsm.current_state, target)


class TestHistoryManager(unittest.TestCase):
    """Test HistoryManager class."""

    def test_create_history(self):
        """Test creating history manager."""
        manager = HistoryManager(max_entries=100)
        self.assertEqual(manager.max_entries, 100)

    def test_push_entry(self):
        """Test pushing entries."""
        manager = HistoryManager()
        entry = HistoryEntry(
            timestamp=datetime.now(),
            from_state=State("A"),
            to_state=State("B"),
            event=Event("E"),
            success=True
        )
        manager.push(entry)
        self.assertEqual(manager.len(), 1)

    def test_last_entry(self):
        """Test getting last entry."""
        manager = HistoryManager()
        entry = HistoryEntry(
            timestamp=datetime.now(),
            from_state=State("A"),
            to_state=State("B"),
            event=Event("E"),
            success=True
        )
        manager.push(entry)
        self.assertEqual(manager.last(), entry)

    def test_filter_by_state(self):
        """Test filtering by state."""
        manager = HistoryManager()
        state_a = State("A")
        state_b = State("B")
        entry1 = HistoryEntry(datetime.now(), state_a, state_b, Event("E"), True)
        entry2 = HistoryEntry(datetime.now(), state_b, state_a, Event("E"), True)
        manager.push(entry1)
        manager.push(entry2)

        entries = manager.entries_for_state(state_a)
        self.assertEqual(len(entries), 2)

    def test_filter_by_event(self):
        """Test filtering by event."""
        manager = HistoryManager()
        event1 = Event("E1")
        event2 = Event("E2")
        entry1 = HistoryEntry(datetime.now(), State("A"), State("B"), event1, True)
        entry2 = HistoryEntry(datetime.now(), State("B"), State("A"), event2, True)
        manager.push(entry1)
        manager.push(entry2)

        entries = manager.entries_for_event(event1)
        self.assertEqual(len(entries), 1)

    def test_successful_failed_entries(self):
        """Test filtering successful/failed entries."""
        manager = HistoryManager()
        entry1 = HistoryEntry(datetime.now(), State("A"), State("B"), Event("E"), True)
        entry2 = HistoryEntry(datetime.now(), State("B"), State("A"), Event("E"), False)
        manager.push(entry1)
        manager.push(entry2)

        self.assertEqual(len(manager.successful_entries()), 1)
        self.assertEqual(len(manager.failed_entries()), 1)


if __name__ == "__main__":
    unittest.main()
