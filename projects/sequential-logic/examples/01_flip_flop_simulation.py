"""
Flip-Flop Simulation Demo / 触发器仿真演示

Demonstrates the behavior of SR latch, JK, D, and T flip-flops.
演示SR锁存器、JK、D和T触发器的行为。

Run with: python examples/01_flip_flop_simulation.py
"""

from src.flip_flops import SRLatch, LatchState, JKFlipFlop
from src.d_and_t_ff import DFlipFlop, TFlipFlop
from src.timing_diagram import TimingDiagramGenerator, ClockSignal, generate_counter_timing_diagram


def demo_sr_latch():
    """Demonstrate SR Latch behavior / 演示SR锁存器行为"""
    print("=" * 60)
    print("SR Latch / SR锁存器")
    print("=" * 60)

    latch = SRLatch(LatchState.RESET)
    print(f"Initial state: {latch}")
    print()

    # Test all input combinations
    print("Testing all input combinations / 测试所有输入组合:")
    print("-" * 40)

    test_cases = [
        (0, 0, "No change / 保持"),
        (1, 0, "Set / 置位"),
        (0, 1, "Reset / 复位"),
        (1, 1, "Invalid / 无效"),
        (0, 0, "Still no change / 仍然保持"),
        (1, 0, "Set again / 再次置位"),
    ]

    for s, r, desc in test_cases:
        result = latch.pulse(s, r)
        print(f"  S={s}, R={r} | {desc:20s} | Q={latch.q}, Q_bar={latch.q_bar}")

    print()
    print(f"History ({len(latch.history)} entries):")
    for i, (s, r, q, qb) in enumerate(latch.history):
        print(f"  Step {i+1}: S={s}, R={r} -> Q={q}, Q_bar={qb}")
    print()


def demo_jk_flip_flop():
    """Demonstrate JK Flip-Flop behavior / 演示JK触发器行为"""
    print("=" * 60)
    print("JK Flip-Flop / JK触发器")
    print("=" * 60)

    jk = JKFlipFlop(initial_q=0)
    print(f"Initial state: Q={jk.q}, Q_bar={jk.q_bar}")
    print()

    # Test all input combinations on rising edge
    print("Rising edge transitions / 上升沿转换:")
    print("-" * 40)

    test_cases = [
        (0, 0, "No change"),
        (1, 0, "Set"),
        (0, 1, "Reset"),
        (1, 1, "Toggle"),
        (1, 1, "Toggle again"),
        (0, 0, "No change"),
    ]

    for j, k, desc in test_cases:
        result = jk.clock_rising_edge(j, k)
        print(f"  J={j}, K={k} | {desc:15s} | {result}")

    print()
    print(f"Final state: Q={jk.q}, Q_bar={jk.q_bar}")
    print(f"History ({len(jk.history)} entries):")
    for i, (j, k, clk, q, qb) in enumerate(jk.history):
        print(f"  Step {i+1}: J={j}, K={k}, CLK={clk} -> Q={q}, Q_bar={qb}")
    print()


def demo_d_flip_flop():
    """Demonstrate D Flip-Flop behavior / 演示D触发器行为"""
    print("=" * 60)
    print("D Flip-Flop / D触发器")
    print("=" * 60)

    dff = DFlipFlop(initial_q=0)
    print(f"Initial state: Q={dff.q}")
    print()

    # Simulate a data sequence
    data_sequence = [1, 0, 1, 1, 0, 0, 1, 0]
    print(f"Shifting in data: {data_sequence}")
    print("-" * 40)

    for i, d in enumerate(data_sequence):
        result = dff.clock_rising_edge(d)
        print(f"  Clock {i+1}: D={d} -> Q={dff.q} | {result}")

    print()
    print(f"Final value: {dff.get_binary_string() if hasattr(dff, 'get_binary_string') else dff.q}")
    print(f"History: {dff.get_history()}")
    print()


def demo_t_flip_flop():
    """Demonstrate T Flip-Flop behavior / 演示T触发器行为"""
    print("=" * 60)
    print("T Flip-Flop / T触发器")
    print("=" * 60)

    tff = TFlipFlop(initial_q=0)
    print(f"Initial state: Q={tff.q}")
    print()

    # T=1 always toggles
    print("T=1 (toggle on every clock):")
    print("-" * 40)
    for i in range(6):
        result = tff.clock_rising_edge(1)
        print(f"  Clock {i+1}: T=1 -> Q={tff.q} | {result}")

    print()
    print("T=0 (hold state):")
    print("-" * 40)
    for i in range(3):
        result = tff.clock_rising_edge(0)
        print(f"  Clock {i+1}: T=0 -> Q={tff.q} | {result}")

    print()
    print(f"Final state: Q={tff.q}")
    print()


def demo_flip_flop_chain():
    """Demonstrate flip-flop chaining (frequency divider) / 演示触发器级联（分频器）"""
    print("=" * 60)
    print("Flip-Flop Chain - Frequency Divider / 触发器级联 - 分频器")
    print("=" * 60)
    print()
    print("Connecting T flip-flops in series creates a divide-by-2^n counter.")
    print("将T触发器串联连接可创建2^n分频器。")
    print()

    # Create a chain of T flip-flops
    ff_count = 4
    flip_flops = [TFlipFlop(0) for _ in range(ff_count)]

    print(f"Chain of {ff_count} T flip-flops:")
    print(f"CLK | FF0 | FF1 | FF2 | FF3 | Output (binary)")
    print("-" * 55)

    for cycle in range(16):
        # Generate clock
        clk = (cycle % 2)  # 0, 1, 0, 1, ...

        # On rising edge (clk goes from 0 to 1)
        if cycle % 2 == 1:
            # First FF toggles on every rising edge
            flip_flops[0].clock_rising_edge(1)
            # Subsequent FFs toggle when previous FF transitions 1->0
            for i in range(1, ff_count):
                prev_q = (cycle >> (i - 1)) & 1
                curr_q = (cycle >> i) & 1
                if prev_q == 1 and curr_q == 0:
                    flip_flops[i].clock_rising_edge(1)

        # Read outputs
        output = sum((ff.q << i) for i, ff in enumerate(flip_flops))
        binary = format(output, f'0{ff_count}b')
        print(f" {cycle:3d} | {flip_flops[0].q:3d} | {flip_flops[1].q:3d} | {flip_flops[2].q:3d} | {flip_flops[3].q:3d} | {binary}")

    print()
    print("Notice: FF0 toggles every cycle (f/2), FF1 every 2 cycles (f/4), etc.")
    print("注意：FF0每个周期翻转（f/2），FF1每2个周期翻转（f/4），依此类推。")
    print()


def generate_flip_flop_timing_diagram():
    """Generate timing diagram for flip-flop demonstration / 生成触发器演示的时序图"""
    from src.timing_diagram import generate_counter_timing_diagram
    from src.counter import RippleCounter

    # Create a simple counter to demonstrate timing
    counter = RippleCounter(num_bits=4, initial_value=0)

    print("Generating timing diagram for ripple counter...")
    print("生成纹波计数器时序图...")

    try:
        gen = generate_counter_timing_diagram(
            counter,
            num_cycles=8,
            title="Ripple Counter Timing Diagram / 纹波计数器时序图",
            save_path="examples/output/counter_timing.png"
        )
        print("Timing diagram generated: examples/output/counter_timing.png")
    except Exception as e:
        print(f"Note: Timing diagram generation skipped ({e})")
        print("Install matplotlib to generate timing diagrams: pip install matplotlib")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Sequential Logic Circuit - Flip-Flop Simulation")
    print("时序逻辑电路 - 触发器仿真")
    print("=" * 60 + "\n")

    demo_sr_latch()
    demo_jk_flip_flop()
    demo_d_flip_flop()
    demo_t_flip_flop()
    demo_flip_flop_chain()
    generate_flip_flop_timing_diagram()

    print("Done! / 完成!")
