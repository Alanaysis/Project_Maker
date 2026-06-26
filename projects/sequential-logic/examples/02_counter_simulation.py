"""
Counter Simulation Demo / 计数器仿真演示

Demonstrates ripple counters, synchronous counters, and up/down counters.
演示纹波计数器、同步计数器和加减计数器。

Run with: python examples/02_counter_simulation.py
"""

from src.counter import RippleCounter, SynchronousCounter, UpDownCounter, CounterMode
from src.timing_diagram import ClockSignal, TimingDiagramGenerator


def demo_ripple_counter():
    """Demonstrate asynchronous ripple counter / 演示异步纹波计数器"""
    print("=" * 60)
    print("Asynchronous (Ripple) Counter / 异步（纹波）计数器")
    print("=" * 60)

    counter = RippleCounter(num_bits=4, initial_value=0, mode=CounterMode.UP)
    print(f"Initial: {counter.get_binary_output()} (decimal: {counter.value})")
    print()

    print("Counting up (0 to 15):")
    print(f"  Cycle | Value | Binary")
    print("  " + "-" * 30)

    for i in range(16):
        val = counter.step()
        print(f"  {i+1:5d} | {val:5d} | {counter.get_binary_output()}")

    print()
    print("Notice: Each bit toggles when the previous bit transitions 1->0.")
    print("注意：每个位在前一个位从1变为0时翻转。")
    print("This creates a 'ripple' effect - hence the name.")
    print("这产生了'纹波'效应——因此得名。")
    print()


def demo_down_counter():
    """Demonstrate down counting / 演示递减计数"""
    print("=" * 60)
    print("Down Counter / 递减计数器")
    print("=" * 60)

    counter = RippleCounter(num_bits=4, initial_value=15, mode=CounterMode.DOWN)
    print(f"Initial: {counter.get_binary_output()} (decimal: {counter.value})")
    print()

    print("Counting down (15 to 0):")
    print(f"  Cycle | Value | Binary")
    print("  " + "-" * 30)

    for i in range(16):
        val = counter.step()
        print(f"  {i+1:5d} | {val:5d} | {counter.get_binary_output()}")

    print()


def demo_sync_counter():
    """Demonstrate synchronous counter / 演示同步计数器"""
    print("=" * 60)
    print("Synchronous Counter / 同步计数器")
    print("=" * 60)

    counter = SynchronousCounter(num_bits=4, initial_value=0, mode=CounterMode.UP)
    print(f"Initial: {counter.get_binary_output()} (decimal: {counter.value})")
    print()

    print("Counting up (0 to 15):")
    print(f"  Cycle | Value | Binary")
    print("  " + "-" * 30)

    for i in range(16):
        val = counter.step()
        print(f"  {i+1:5d} | {val:5d} | {counter.get_binary_output()}")

    print()
    print("Key difference from ripple counter: All bits change simultaneously.")
    print("与纹波计数器的关键区别：所有位同时变化。")
    print("No ripple delay = faster operation.")
    print("无纹波延迟 = 更快的操作。")
    print()


def demo_modulus_counter():
    """Demonstrate modulus (mod-N) counter / 演示模数计数器"""
    print("=" * 60)
    print("Modulus (Mod-N) Counter / 模数计数器")
    print("=" * 60)

    # Mod-10 counter (counts 0-9, then resets)
    mod_counter = SynchronousCounter(num_bits=4, initial_value=0, modulus=10, mode=CounterMode.UP)
    print(f"Mod-10 counter (counts 0-9):")
    print(f"  Cycle | Value | Binary")
    print("  " + "-" * 30)

    for i in range(12):
        val = mod_counter.step()
        print(f"  {i+1:5d} | {val:5d} | {mod_counter.get_binary_output()}")

    print()
    print("Notice: After reaching 9, it resets to 0.")
    print("注意：达到9后重置为0。")
    print()

    # Mod-6 counter
    mod6 = SynchronousCounter(num_bits=3, initial_value=0, modulus=6, mode=CounterMode.UP)
    print(f"Mod-6 counter (counts 0-5):")
    print(f"  Cycle | Value | Binary")
    print("  " + "-" * 30)

    for i in range(8):
        val = mod6.step()
        print(f"  {i+1:5d} | {val:5d} | {mod6.get_binary_output()}")

    print()


def demo_up_down_counter():
    """Demonstrate up/down counter / 演示加减计数器"""
    print("=" * 60)
    print("Up/Down Counter / 加减计数器")
    print("=" * 60)

    counter = UpDownCounter(num_bits=4, initial_value=8)
    print(f"Initial: {counter.get_binary_output()} (decimal: {counter.value})")
    print()

    # Count up
    print("Counting up:")
    print(f"  Cycle | Value | Direction")
    print("  " + "-" * 35)

    counter.set_direction(True)
    for i in range(5):
        val = counter.step()
        print(f"  {i+1:5d} | {val:5d} | UP")

    # Count down
    print()
    print("Counting down:")
    counter.set_direction(False)
    for i in range(5):
        val = counter.step()
        print(f"  {i+6:5d} | {val:5d} | DOWN")

    # Count up again
    print()
    print("Counting up again:")
    counter.set_direction(True)
    for i in range(5):
        val = counter.step()
        print(f"  {i+11:5d} | {val:5d} | UP")

    print()


def demo_counter_as_frequency_divider():
    """Demonstrate counter as frequency divider / 演示计数器作为分频器"""
    print("=" * 60)
    print("Counter as Frequency Divider / 计数器作为分频器")
    print("=" * 60)

    # A 4-bit counter divides frequency by 16
    counter = RippleCounter(num_bits=4, initial_value=0, mode=CounterMode.UP)

    print("4-bit binary counter as frequency divider:")
    print("4位二进制计数器作为分频器:")
    print()
    print(f"  Bit | Divider | Frequency (relative)")
    print("  " + "-" * 38)

    for i in range(4):
        divider = 2 ** (i + 1)
        print(f"  Q{i}  | /{divider:2d}    | f_clk / {divider}")

    print()
    print("Each bit has half the frequency of the previous bit.")
    print("每个位的频率是前一位的一半。")
    print()


def generate_counter_timing_diagram():
    """Generate timing diagram for counters / 生成计数器时序图"""
    from src.timing_diagram import TimingDiagramGenerator, ClockSignal

    print("Generating counter timing diagram...")
    print("生成计数器时序图...")

    counter = RippleCounter(num_bits=4, initial_value=0)
    num_cycles = 8

    gen = TimingDiagramGenerator(figsize=(14, 6))

    # Add clock
    clock = ClockSignal.generate(num_cycles)
    gen.add_signal('CLK', clock, "CLK", "clock")

    # Add counter outputs
    for i in range(num_cycles):
        counter.step()

    # Re-run to collect values
    counter.reset(0)
    bit_values = [[] for _ in range(4)]
    for i in range(num_cycles):
        counter.step()
        for j in range(4):
            bit_values[j].append((counter.value >> j) & 1)

    for j in range(4):
        gen.add_signal(f'Q{j}', bit_values[j], f"Q{j}", "output")

    try:
        gen.generate(
            title="Ripple Counter Timing Diagram / 纹波计数器时序图",
            save_path="examples/output/counter_timing_diagram.png"
        )
        print("Timing diagram saved: examples/output/counter_timing_diagram.png")
    except Exception as e:
        print(f"Note: Timing diagram generation skipped ({e})")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Sequential Logic Circuit - Counter Simulation")
    print("时序逻辑电路 - 计数器仿真")
    print("=" * 60 + "\n")

    demo_ripple_counter()
    demo_down_counter()
    demo_sync_counter()
    demo_modulus_counter()
    demo_up_down_counter()
    demo_counter_as_frequency_divider()
    generate_counter_timing_diagram()

    print("Done! / 完成!")
