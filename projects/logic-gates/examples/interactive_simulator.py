"""
Example 5: Interactive gate simulator.

Run: python examples/interactive_simulator.py
"""

from src.gates import AND, OR, NOT, NAND, NOR, XOR, XNOR
from src.truth_table import print_truth_table
from src.circuits import HalfAdder, FullAdder
from src.multi_bit import add_n_bit


GATES = {
    "1": ("AND", AND),
    "2": ("OR", OR),
    "3": ("NOT", NOT),
    "4": ("NAND", NAND),
    "5": ("NOR", NOR),
    "6": ("XOR", XOR),
    "7": ("XNOR", XNOR),
}


def simulate_gate():
    """Interactive gate simulation."""
    print("=" * 50)
    print("  Interactive Logic Gate Simulator")
    print("  交互式逻辑门模拟器")
    print("=" * 50)
    print("\nAvailable gates (可用门):")
    for key, (name, _) in GATES.items():
        print(f"  {key}: {name}")
    print("  8: Truth Tables (真值表)")
    print("  9: Exit (退出)")
    print()


def get_binary_input(prompt: str) -> int:
    """Get binary input from user."""
    while True:
        val = input(prompt).strip()
        if val in ("0", "1"):
            return int(val)
        print("  Please enter 0 or 1. (请输入 0 或 1)")


def interactive_mode():
    """Run interactive simulation loop."""
    while True:
        print("\nSelect a gate (选择门):")
        choice = input("> ").strip()

        if choice == "9":
            print("Goodbye! (再见!)")
            break

        if choice == "8":
            print("\nShowing all truth tables...")
            for name, func in GATES.values():
                print()
                if name == "NOT":
                    print("  A | Out")
                    print("  ---| ---")
                    for a in [0, 1]:
                        print(f"  {a}   |  {func(a)}")
                else:
                    print(print_truth_table(func, name, 2))
            continue

        if choice not in GATES:
            print("Invalid choice. (无效选择)")
            continue

        gate_name, gate_func = GATES[choice]

        if gate_name == "NOT":
            a = get_binary_input("  Input A: ")
            result = gate_func(a)
            print(f"\n  NOT({a}) = {result}")
            print(f"  输入: A={a}")
            print(f"  输出: {result}")
        else:
            a = get_binary_input("  Input A: ")
            b = get_binary_input("  Input B: ")
            result = gate_func(a, b)
            print(f"\n  {gate_name}({a}, {b}) = {result}")
            print(f"  输入: A={a}, B={b}")
            print(f"  输出: {result}")


def circuit_demo():
    """Demo half adder and full adder."""
    print("\n" + "=" * 50)
    print("  Circuit Demo (电路演示)")
    print("=" * 50)

    # Half adder
    print("\n--- Half Adder (半加器) ---")
    ha = HalfAdder()
    for a in [0, 1]:
        for b in [0, 1]:
            from src.gates import Wire
            w_a = Wire("A", a)
            w_b = Wire("B", b)
            ha.set_inputs(w_a, w_b)
            ha.evaluate()
            s, c = ha.get_result()
            print(f"  {a} + {b} = Sum:{s}, Carry:{c}")

    # Full adder
    print("\n--- Full Adder (全加器) ---")
    fa = FullAdder()
    for a in [0, 1]:
        for b in [0, 1]:
            for cin in [0, 1]:
                w_a = Wire("A", a)
                w_b = Wire("B", b)
                w_cin = Wire("Cin", cin)
                fa.set_inputs(w_a, w_b, w_cin)
                fa.evaluate()
                s, cout = fa.get_result()
                print(f"  {a} + {b} + {cin} = Sum:{s}, Cout:{cout}")

    # 4-bit adder
    print("\n--- 4-Bit Adder (4位加法器) ---")
    test_pairs = [(5, 3), (15, 1), (8, 7), (0, 0)]
    for a, b in test_pairs:
        result, carry = add_n_bit(a, b, 4)
        print(f"  {a} + {b} = {result}" + (f" (carry: {carry})" if carry else ""))


if __name__ == "__main__":
    simulate_gate()

    mode = input("Choose mode:\n  1: Interactive (交互式)\n  2: Circuit Demo (电路演示)\n  > ").strip()

    if mode == "1":
        interactive_mode()
    else:
        circuit_demo()
