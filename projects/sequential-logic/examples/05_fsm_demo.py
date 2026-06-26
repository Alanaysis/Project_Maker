"""
Finite State Machine Demo / 有限状态机演示

Demonstrates FSM applications: sequence detection, traffic lights, vending machine.
演示状态机应用：序列检测、交通灯、售货机。

Run with: python examples/05_fsm_demo.py
"""

from src.fsm import FiniteStateMachine, FSMType, SequenceDetector, TrafficLightFSM, VendingMachineFSM


def demo_sequence_detector():
    """Demonstrate sequence detector FSM / 演示序列检测器状态机"""
    print("=" * 60)
    print("Sequence Detector FSM / 序列检测器状态机")
    print("=" * 60)

    # Detect sequence "101"
    detector = SequenceDetector(sequence="101")
    print(detector.get_state_diagram())
    print()

    # Test with various input sequences
    test_sequences = [
        [1, 0, 1, 0, 1],      # Should detect at positions 3 and 5
        [1, 1, 0, 0, 1],       # Should detect at position 5
        [0, 0, 0, 0, 0],       # No detection
        [1, 0, 1, 0, 1, 0, 1], # Multiple detections
    ]

    for seq in test_sequences:
        detector.reset()
        print(f"Input: {seq}")
        for i, bit in enumerate(seq):
            output, state = detector.step(bit)
            detected = " ** DETECTED **" if output == "YES" else ""
            print(f"  Step {i+1}: input={bit}, state={state}, output={output}{detected}")
        print()


def demo_traffic_light():
    """Demonstrate traffic light FSM / 演示交通灯状态机"""
    print("=" * 60)
    print("Traffic Light FSM / 交通灯状态机")
    print("=" * 60)

    light = TrafficLightFSM()
    print(light.get_state_diagram())
    print()

    # Run the traffic light cycle
    print("Traffic light cycle (tick = timer expiry):")
    print("-" * 40)

    light.reset()
    num_steps = 8

    for i in range(num_steps):
        output, state = light.step("tick")
        color_map = {
            "GREEN": "🟢",
            "YELLOW": "🟡",
            "RED": "🔴",
            "RED_YELLOW": "🔴🟡",
        }
        emoji = color_map.get(state, "")
        print(f"  Step {i+1}: {emoji} {state:12s} | Output: {output}")

    print()
    print("Cycle: GREEN -> YELLOW -> RED -> RED+YELLOW -> GREEN (repeat)")
    print("循环：绿 -> 黄 -> 红 -> 红+黄 -> 绿（重复）")
    print()


def demo_vending_machine():
    """Demonstrate vending machine FSM / 演示售货机状态机"""
    print("=" * 60)
    print("Vending Machine FSM / 售货机状态机")
    print("=" * 60)

    machine = VendingMachineFSM()
    print(machine.get_state_diagram())
    print()

    # Test different payment scenarios
    scenarios = [
        ("Insert quarters", [["0.25", "0.25", "0.25", "0.25"]]),
        ("Insert mixed coins", [["0.50", "0.25", "0.25"]]),
        ("Overpay", [["1.00", "0.25"]]),
        ("Insert half then quarters", [["0.50", "0.50"]]),
    ]

    for desc, coins in scenarios:
        machine.reset()
        print(f"Scenario: {desc}")
        print(f"  {'Coin':10s} | {'State':10s} | {'Output':30s}")
        print("  " + "-" * 50)

        for coin in coins:
            output, state = machine.step(coin)
            print(f"  {coin:10s} | {state:10s} | {output}")
        print()


def demo_custom_fsm():
    """Demonstrate building a custom FSM / 演示构建自定义状态机"""
    print("=" * 60)
    print("Custom FSM - Even Parity Checker / 自定义状态机 - 偶校验检查器")
    print("=" * 60)

    print("This FSM checks if a bit stream has even parity (even number of 1s).")
    print("此状态机检查位流是否具有偶校验（偶数个1）。")
    print()

    # Build even parity checker
    parity_fsm = FiniteStateMachine(FSMType.MOORE)
    parity_fsm.add_state("EVEN", is_start=True, is_final=True)  # Even number of 1s seen
    parity_fsm.add_state("ODD", is_final=False)  # Odd number of 1s seen

    # Transitions
    parity_fsm.add_transition("EVEN", "ODD", "1", output="EVEN")
    parity_fsm.add_transition("EVEN", "EVEN", "0", output="EVEN")
    parity_fsm.add_transition("ODD", "EVEN", "1", output="ODD")
    parity_fsm.add_transition("ODD", "ODD", "0", output="ODD")

    print(parity_fsm.get_state_diagram())
    print()

    # Test
    test_bits = [
        ([0, 0, 0], "No 1s -> even parity"),
        ([1, 0, 0], "One 1 -> odd parity"),
        ([1, 1, 0], "Two 1s -> even parity"),
        ([1, 1, 1], "Three 1s -> odd parity"),
        ([1, 0, 1, 0, 1, 0], "Three 1s -> odd parity"),
    ]

    for bits, desc in test_bits:
        parity_fsm.reset()
        parity_fsm.run(bits)
        is_even = parity_fsm.is_accepted(bits)
        status = "Even" if is_even else "Odd"
        print(f"  {bits} -> {status} parity | {desc}")

    print()


def demo_fsm_comparison():
    """Compare Moore and Mealy machines / 比较摩尔型和米利型状态机"""
    print("=" * 60)
    print("Moore vs Mealy State Machines / 摩尔型 vs 米利型状态机")
    print("=" * 60)

    print()
    print("Key differences / 主要区别:")
    print("-" * 40)
    print("  Property          | Moore              | Mealy")
    print("  ------------------+--------------------+--------------------")
    print("  Output location   | States             | Transitions")
    print("  输出位置           | 状态               | 转换")
    print("  Response speed    | Slower (1 cycle)   | Faster (immediate)")
    print("  响应速度           | 较慢（1周期）       | 更快（即时）")
    print("  Number of states  | More               | Fewer")
    print("  状态数             | 更多               | 更少")
    print("  Complexity        | Simpler            | More complex")
    print("  复杂度             | 更简单             | 更复杂")
    print()

    print("When to use / 使用场景:")
    print("  Moore: When output stability is critical (outputs don't change during clock)")
    print("         当输出稳定性至关重要时（输出在时钟期间不变化）")
    print("  Mealy: When faster response is needed with fewer states")
    print("         当需要更快响应且状态更少时")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Sequential Logic Circuit - Finite State Machine Demo")
    print("时序逻辑电路 - 有限状态机演示")
    print("=" * 60 + "\n")

    demo_sequence_detector()
    demo_traffic_light()
    demo_vending_machine()
    demo_custom_fsm()
    demo_fsm_comparison()

    print("Done! / 完成!")
