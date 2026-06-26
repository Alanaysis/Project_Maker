"""
Sequential Logic Circuit - Unit Tests / 时序逻辑电路 - 单元测试

Run with: pytest tests/ -v
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.flip_flops import SRLatch, LatchState, JKFlipFlop
from src.d_and_t_ff import DFlipFlop, TFlipFlop
from src.counter import RippleCounter, SynchronousCounter, UpDownCounter, CounterMode
from src.register import SIPORegister, PISOResister, PIPORegister, BidirectionalShiftRegister
from src.fsm import FiniteStateMachine, FSMType, SequenceDetector, TrafficLightFSM, VendingMachineFSM


# ===== SR Latch Tests =====

class TestSRLatch:
    def test_initial_reset_state(self):
        latch = SRLatch(LatchState.RESET)
        assert latch.q == 0
        assert latch.q_bar == 1

    def test_initial_set_state(self):
        latch = SRLatch(LatchState.SET)
        assert latch.q == 1
        assert latch.q_bar == 0

    def test_set_operation(self):
        latch = SRLatch()
        latch.set()
        assert latch.q == 1
        assert latch.q_bar == 0
        assert latch.state == LatchState.SET

    def test_reset_operation(self):
        latch = SRLatch(LatchState.SET)
        latch.reset()
        assert latch.q == 0
        assert latch.q_bar == 1
        assert latch.state == LatchState.RESET

    def test_no_change(self):
        latch = SRLatch(LatchState.SET)
        latch.no_change()
        assert latch.q == 1
        assert latch.q_bar == 0

    def test_invalid_input(self):
        latch = SRLatch()
        latch.invalid_input()
        assert latch.state == LatchState.INVALID

    def test_pulse_operations(self):
        latch = SRLatch()
        assert latch.pulse(0, 0) == "保持: Q=0, Q_bar=1"
        assert latch.pulse(1, 0) == "置位: Q=1, Q_bar=0"
        assert latch.pulse(0, 1) == "复位: Q=0, Q_bar=1"
        assert "无效" in latch.pulse(1, 1)

    def test_history_tracking(self):
        latch = SRLatch()
        latch.set()
        latch.reset()
        latch.set()
        history = latch.get_history()
        assert len(history) == 3
        assert history[0] == (1, 0, 1, 0)
        assert history[1] == (0, 1, 0, 1)
        assert history[2] == (1, 0, 1, 0)


# ===== JK Flip-Flop Tests =====

class TestJKFlipFlop:
    def test_initial_state(self):
        jk = JKFlipFlop(initial_q=0)
        assert jk.q == 0
        assert jk.q_bar == 1

    def test_set(self):
        jk = JKFlipFlop()
        jk.clock_rising_edge(1, 0)
        assert jk.q == 1

    def test_reset(self):
        jk = JKFlipFlop(initial_q=1)
        jk.clock_rising_edge(0, 1)
        assert jk.q == 0

    def test_no_change(self):
        jk = JKFlipFlop(initial_q=1)
        jk.clock_rising_edge(0, 0)
        assert jk.q == 1

    def test_toggle(self):
        jk = JKFlipFlop(initial_q=0)
        jk.clock_rising_edge(1, 1)
        assert jk.q == 1
        jk.clock_rising_edge(1, 1)
        assert jk.q == 0

    def test_falling_edge(self):
        jk = JKFlipFlop()
        result = jk.clock_falling_edge(1, 1)
        assert jk.q == 1
        assert "翻转" in result

    def test_q_bar_consistency(self):
        jk = JKFlipFlop()
        jk.clock_rising_edge(1, 0)
        assert jk.q_bar == 1 - jk.q


# ===== D Flip-Flop Tests =====

class TestDFlipFlop:
    def test_initial_state(self):
        dff = DFlipFlop()
        assert dff.q == 0

    def test_capture_high(self):
        dff = DFlipFlop()
        result = dff.clock_rising_edge(1)
        assert dff.q == 1
        assert "更新" in result

    def test_capture_low(self):
        dff = DFlipFlop(initial_q=1)
        result = dff.clock_rising_edge(0)
        assert dff.q == 0
        assert "更新" in result

    def test_hold_same_value(self):
        dff = DFlipFlop(initial_q=1)
        result = dff.clock_rising_edge(1)
        assert dff.q == 1
        assert "保持" in result

    def test_q_bar_consistency(self):
        dff = DFlipFlop()
        dff.clock_rising_edge(1)
        assert dff.q_bar == 0
        dff.clock_rising_edge(0)
        assert dff.q_bar == 1


# ===== T Flip-Flop Tests =====

class TestTFlipFlop:
    def test_initial_state(self):
        tff = TFlipFlop()
        assert tff.q == 0

    def test_toggle(self):
        tff = TFlipFlop(initial_q=0)
        tff.clock_rising_edge(1)
        assert tff.q == 1
        tff.clock_rising_edge(1)
        assert tff.q == 0

    def test_hold(self):
        tff = TFlipFlop(initial_q=1)
        tff.clock_rising_edge(0)
        assert tff.q == 1

    def test_frequency_division(self):
        """T flip-flop divides frequency by 2 when T=1"""
        tff = TFlipFlop(initial_q=0)
        transitions = 0
        for _ in range(8):
            old_q = tff.q
            tff.clock_rising_edge(1)
            if tff.q != old_q:
                transitions += 1
        assert transitions == 8  # Should toggle every cycle

    def test_q_bar_consistency(self):
        tff = TFlipFlop()
        tff.clock_rising_edge(1)
        assert tff.q_bar == 1 - tff.q


# ===== Counter Tests =====

class TestRippleCounter:
    def test_initial_value(self):
        counter = RippleCounter(num_bits=4, initial_value=0)
        assert counter.value == 0

    def test_count_up(self):
        counter = RippleCounter(num_bits=4, initial_value=0)
        for expected in range(1, 16):
            counter.step()
            assert counter.value == expected

    def test_count_wrap(self):
        counter = RippleCounter(num_bits=4, initial_value=15)
        counter.step()
        assert counter.value == 0

    def test_binary_output(self):
        counter = RippleCounter(num_bits=4, initial_value=5)
        assert counter.get_binary_output() == "0101"

    def test_down_counting(self):
        counter = RippleCounter(num_bits=4, initial_value=5, mode=CounterMode.DOWN)
        counter.step()
        assert counter.value == 4

    def test_reset(self):
        counter = RippleCounter(num_bits=4, initial_value=0)
        for _ in range(5):
            counter.step()
        counter.reset(3)
        assert counter.value == 3


class TestSynchronousCounter:
    def test_initial_value(self):
        counter = SynchronousCounter(num_bits=4, initial_value=0)
        assert counter.value == 0

    def test_count_up(self):
        counter = SynchronousCounter(num_bits=4, initial_value=0)
        for expected in range(1, 16):
            counter.step()
            assert counter.value == expected

    def test_modulus(self):
        counter = SynchronousCounter(num_bits=4, initial_value=0, modulus=10)
        for _ in range(10):
            counter.step()
        assert counter.value == 0

    def test_parallel_load(self):
        counter = SynchronousCounter(num_bits=4, initial_value=0)
        counter.load(7)
        assert counter.value == 7

    def test_down_counting(self):
        counter = SynchronousCounter(num_bits=4, initial_value=0, mode=CounterMode.DOWN)
        counter.step()
        assert counter.value == 15  # Wrap around

    def test_binary_output(self):
        counter = SynchronousCounter(num_bits=4, initial_value=10)
        assert counter.get_binary_output() == "1010"


class TestUpDownCounter:
    def test_count_up(self):
        counter = UpDownCounter(num_bits=4, initial_value=0)
        counter.step()
        assert counter.value == 1

    def test_count_down(self):
        counter = UpDownCounter(num_bits=4, initial_value=1)
        counter.set_direction(False)
        counter.step()
        assert counter.value == 0

    def test_direction_switch(self):
        counter = UpDownCounter(num_bits=4, initial_value=5)
        counter.set_direction(True)
        counter.step()
        assert counter.value == 6
        counter.set_direction(False)
        counter.step()
        assert counter.value == 5

    def test_parallel_load(self):
        counter = UpDownCounter(num_bits=4, initial_value=0)
        counter.load(10)
        assert counter.value == 10

    def test_wrap_around(self):
        counter = UpDownCounter(num_bits=4, initial_value=0)
        counter.set_direction(False)
        counter.step()
        assert counter.value == 15


# ===== Register Tests =====

class TestSIPORegister:
    def test_initial_state(self):
        sipo = SIPORegister(width=8)
        assert sipo.value == 0

    def test_shift_in_bits(self):
        sipo = SIPORegister(width=8)
        sipo.shift_in(1)
        sipo.shift_in(0)
        sipo.shift_in(1)
        assert sipo.get_bits() == [0, 0, 0, 0, 0, 1, 0, 1]

    def test_shift_in_byte(self):
        sipo = SIPORegister(width=8)
        data = 0b10110011
        for i in range(7, -1, -1):
            sipo.shift_in((data >> i) & 1)
        assert sipo.value == data

    def test_reset(self):
        sipo = SIPORegister(width=8)
        sipo.shift_in(1)
        sipo.reset()
        assert sipo.value == 0

    def test_parallel_output(self):
        sipo = SIPORegister(width=4)
        sipo.shift_in(1)
        sipo.shift_in(0)
        sipo.shift_in(1)
        sipo.shift_in(1)
        assert sipo.get_parallel_output() == [1, 0, 1, 1]


class TestPISOResister:
    def test_parallel_load(self):
        piso = PISOResister(width=8)
        piso.parallel_load(0b10101010)
        assert piso.value == 0b10101010

    def test_shift_out(self):
        piso = PISOResister(width=4)
        piso.parallel_load(0b1101)
        # Shifts right (MSB first): 1101 -> 1, 0, 0, 0
        assert piso.shift_out() == 1  # MSB
        assert piso.shift_out() == 0
        assert piso.shift_out() == 0
        assert piso.shift_out() == 0

    def test_serial_output(self):
        piso = PISOResister(width=4)
        piso.parallel_load(0b1011)
        output = [piso.shift_out() for _ in range(4)]
        assert output == [1, 0, 0, 0]  # Shifts right (MSB first)

    def test_reset(self):
        piso = PISOResister(width=8)
        piso.parallel_load(0xFF)
        piso.reset()
        assert piso.value == 0


class TestPIPORegister:
    def test_parallel_load(self):
        pipo = PIPORegister(width=8)
        pipo.parallel_load(0b10101010)
        assert pipo.parallel_read() == 0b10101010

    def test_bits_output(self):
        pipo = PIPORegister(width=4)
        pipo.parallel_load(0b1010)
        assert pipo.get_bits() == [1, 0, 1, 0]

    def test_reset(self):
        pipo = PIPORegister(width=8)
        pipo.parallel_load(0xFF)
        pipo.reset()
        assert pipo.parallel_read() == 0

    def test_width_limit(self):
        pipo = PIPORegister(width=4)
        pipo.parallel_load(0xFF)  # Should be masked to 4 bits
        assert pipo.parallel_read() == 0b1111


class TestBidirectionalShiftRegister:
    def test_shift_right(self):
        reg = BidirectionalShiftRegister(width=8)
        reg.set_direction("right")
        reg.shift(1)
        assert reg.get_bits() == [1, 0, 0, 0, 0, 0, 0, 0]

    def test_shift_left(self):
        reg = BidirectionalShiftRegister(width=8)
        reg.set_direction("left")
        reg.shift(1)
        assert reg.get_bits() == [0, 0, 0, 0, 0, 0, 0, 1]

    def test_parallel_load(self):
        reg = BidirectionalShiftRegister(width=8)
        reg.parallel_load(0b10101010)
        assert reg.get_bits() == [1, 0, 1, 0, 1, 0, 1, 0]

    def test_serial_out(self):
        reg = BidirectionalShiftRegister(width=4)
        reg.parallel_load(0b1101)
        reg.set_direction("right")
        assert reg.get_serial_out() == 1  # LSB

    def test_reset(self):
        reg = BidirectionalShiftRegister(width=8)
        reg.parallel_load(0xFF)
        reg.reset()
        assert reg.get_bits() == [0, 0, 0, 0, 0, 0, 0, 0]


# ===== FSM Tests =====

class TestFiniteStateMachine:
    def test_add_state(self):
        fsm = FiniteStateMachine()
        state = fsm.add_state("S1", is_start=True)
        assert state.name == "S1"
        assert state.is_start is True

    def test_reset(self):
        fsm = FiniteStateMachine()
        fsm.add_state("S0", is_start=True)
        fsm.add_state("S1")
        fsm.add_transition("S0", "S1", "a")
        fsm.reset()
        assert fsm.current_state == "S0"

    def test_step(self):
        fsm = FiniteStateMachine()
        fsm.add_state("S0", is_start=True)
        fsm.add_state("S1")
        fsm.add_transition("S0", "S1", "a")
        fsm.reset()
        output, state = fsm.step("a")
        assert state == "S1"

    def test_invalid_transition(self):
        fsm = FiniteStateMachine()
        fsm.add_state("S0", is_start=True)
        fsm.add_state("S1")
        fsm.add_transition("S0", "S1", "a")
        fsm.reset()
        with pytest.raises(ValueError):
            fsm.step("b")

    def test_run_sequence(self):
        fsm = FiniteStateMachine()
        fsm.add_state("S0", is_start=True)
        fsm.add_state("S1")
        fsm.add_state("S2")
        fsm.add_transition("S0", "S1", "a")
        fsm.add_transition("S1", "S2", "b")
        fsm.reset()
        results = fsm.run(["a", "b"])
        assert len(results) == 2
        assert results[0][1] == "S1"
        assert results[1][1] == "S2"

    def test_is_accepted(self):
        fsm = FiniteStateMachine()
        fsm.add_state("S0", is_start=True, is_final=True)
        fsm.add_state("S1")
        fsm.add_transition("S0", "S1", "a")
        fsm.reset()
        assert fsm.is_accepted([]) is True
        assert fsm.is_accepted(["a"]) is False


class TestSequenceDetector:
    def test_detect_sequence(self):
        detector = SequenceDetector(sequence="101")
        detector.reset()
        detector.run(["1", "0", "1"])
        history = detector.get_history()
        # Should detect at the last step
        assert any(step[2] == "YES" for step in history)

    def test_no_detection(self):
        detector = SequenceDetector(sequence="101")
        detector.reset()
        detector.run(["0", "0", "0"])
        history = detector.get_history()
        assert all(step[2] != "YES" for step in history)

    def test_multiple_detection(self):
        detector = SequenceDetector(sequence="101")
        detector.reset()
        detector.run(["1", "0", "1", "0", "1"])
        history = detector.get_history()
        detections = sum(1 for step in history if step[2] == "YES")
        assert detections >= 2


class TestTrafficLightFSM:
    def test_cycle(self):
        light = TrafficLightFSM()
        light.reset()
        assert light.current_state == "GREEN"

        _, state = light.step("tick")
        assert state == "YELLOW"

        _, state = light.step("tick")
        assert state == "RED"

        _, state = light.step("tick")
        assert state == "RED_YELLOW"

        _, state = light.step("tick")
        assert state == "GREEN"

    def test_state_diagram(self):
        light = TrafficLightFSM()
        diagram = light.get_state_diagram()
        assert "GREEN" in diagram
        assert "YELLOW" in diagram
        assert "RED" in diagram


class TestVendingMachineFSM:
    def test_dispense_at_dollar(self):
        machine = VendingMachineFSM()
        machine.reset()
        machine.run(["0.25", "0.25", "0.25", "0.25"])
        assert machine.current_state == "$0.00"

    def test_no_dispense_below_dollar(self):
        machine = VendingMachineFSM()
        machine.reset()
        machine.run(["0.25", "0.25"])
        assert machine.current_state == "$0.50"

    def test_overpay(self):
        machine = VendingMachineFSM()
        machine.reset()
        machine.run(["1.00", "0.25"])
        assert machine.current_state == "$0.00"

    def test_mixed_coins(self):
        machine = VendingMachineFSM()
        machine.reset()
        machine.run(["0.50", "0.50"])
        assert machine.current_state == "$0.00"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
