"""
Example 3: Build and demonstrate half adder and full adder circuits.

Run: python examples/adder_circuits.py
"""

from src.circuits import HalfAdder, FullAdder, build_half_adder_circuit
from src.gates import Wire


def demo_half_adder():
    """Demonstrate half adder with all input combinations."""
    print("=" * 50)
    print("  Half Adder (半加器) Demonstration")
    print("=" * 50)
    print("\nA half adder adds two single bits.")
    print("半加器对两个单比特进行加法运算。")
    print("\n  A | B | Sum | Carry")
    print("  ---|---|-----|-------")

    ha = HalfAdder()
    for a in [0, 1]:
        for b in [0, 1]:
            w_a = Wire("A", a)
            w_b = Wire("B", b)
            ha.set_inputs(w_a, w_b)
            ha.evaluate()
            s, c = ha.get_result()
            print(f"  {a}  | {b}  |   {s}   |   {c}")

    print("\n  Key formulas (关键公式):")
    print("    Sum = A XOR B")
    print("    Carry = A AND B")
    print()


def demo_full_adder():
    """Demonstrate full adder with all input combinations."""
    print("=" * 50)
    print("  Full Adder (全加器) Demonstration")
    print("=" * 50)
    print("\nA full adder adds three bits (A, B, Carry-in).")
    print("全加器对三个比特进行加法运算（A, B, 进位输入）。")
    print("\n  A | B | Cin | Sum | Cout")
    print("  ---|---|-----|-----|-------")

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
                print(f"  {a}  | {b}  |  {cin}  |   {s}   |   {cout}")

    print("\n  Key formulas (关键公式):")
    print("    Sum = A XOR B XOR Cin")
    print("    Cout = (A AND B) OR (Cin AND (A XOR B))")
    print()


def demo_circuit_building():
    """Show how to build a half adder from basic gates."""
    print("=" * 50)
    print("  Building Half Adder from Basic Gates (从基本门构建半加器)")
    print("=" * 50)

    ha, desc = build_half_adder_circuit()
    print(desc)
    print()


if __name__ == "__main__":
    demo_half_adder()
    demo_full_adder()
    demo_circuit_building()

    print("=" * 50)
    print("  Summary (总结):")
    print("  - Half Adder: Adds 2 bits, produces Sum and Carry")
    print("  - Full Adder: Adds 3 bits (includes carry-in), produces Sum and Carry-out")
    print("  - Multiple full adders can be chained to build multi-bit adders")
    print("  - 半加器：加2个比特，产生和与进位")
    print("  - 全加器：加3个比特（含进位输入），产生和与进位输出")
    print("  - 多个全加器可以级联构建多位加法器")
    print("=" * 50)
