"""
Example 4: Build and test a simple 4-bit adder circuit.

Run: python examples/four_bit_adder.py
"""

from src.circuits import add_n_bit
from src.multi_bit import bit_to_list, list_to_bit


def demo_4bit_adder():
    """Demonstrate 4-bit addition with all meaningful combinations."""
    print("=" * 60)
    print("  4-Bit Adder (4位加法器) Demonstration")
    print("=" * 60)
    print("\n  A    | B    | A (dec) | B (dec) | Sum (dec) | Sum (bin) | Cout")
    print("  -----|------|---------|---------|-----------|-----------|------")

    test_cases = [
        (0, 0), (0, 1), (1, 2), (3, 5), (7, 8),
        (15, 0), (15, 1), (15, 15), (8, 7), (1, 14),
    ]

    n = 4
    for a, b in test_cases:
        # Ensure values fit in 4 bits
        a = a & 0xF
        b = b & 0xF
        result, carry = add_n_bit(a, b, n)
        a_bits = bit_to_list(a, n)
        b_bits = bit_to_list(b, n)
        sum_bits = bit_to_list(result, n)

        a_bin = "".join(str(x) for x in a_bits)
        b_bin = "".join(str(x) for x in b_bits)
        sum_bin = "".join(str(x) for x in sum_bits)

        print(f"  {a_bin} | {b_bin} |    {a}      |    {b}      |     {result}      |     {sum_bin}      |   {carry}")

    print()


def verify_addition():
    """Verify that our adder produces correct results for all 4-bit combinations."""
    print("Verifying 4-bit adder correctness (验证4位加法器正确性)...")
    print("-" * 40)

    n = 4
    errors = 0
    total = 0

    for a in range(1 << n):
        for b in range(1 << n):
            expected = a + b
            result, carry = add_n_bit(a, b, n)
            # The result should be (a + b) mod 2^n, and carry should be (a + b) >= 2^n
            expected_sum = expected & ((1 << n) - 1)
            expected_carry = 1 if expected >= (1 << n) else 0

            total += 1
            if result != expected_sum or carry != expected_carry:
                errors += 1
                print(f"  ERROR: {a} + {b} = expected {expected_sum}+{expected_carry}, "
                      f"got {result}+{carry}")

    print(f"  Tested {total} combinations.")
    if errors == 0:
        print("  All tests passed! (所有测试通过!)")
    else:
        print(f"  {errors} errors found! (发现 {errors} 个错误!)")
    print()


if __name__ == "__main__":
    demo_4bit_adder()
    verify_addition()

    print("=" * 60)
    print("  4-bit Adder Architecture (4位加法器架构):")
    print("  +-------+    +-------+    +-------+    +-------+")
    print("  | FA 0  | -> | FA 1  | -> | FA 2  | -> | FA 3  |")
    print("  | (LSB) |    |       |    |       |    | (MSB) |")
    print("  +-------+    +-------+    +-------+    +-------+")
    print("     |            |            |            |")
    print("     v            v            v            v")
    print("   Sum0         Sum1         Sum2         Sum3")
    print()
    print("  This is a ripple carry adder (行波进位加法器):")
    print("  - Each full adder passes carry to the next")
    print("  - Carry propagates from LSB to MSB")
    print("  - Simple but carry delay limits speed")
    print("  - 每个全加器将进位传递给下一级")
    print("  - 进位从最低位传播到最高位")
    print("  - 简单但进位延迟限制了速度")
    print("=" * 60)
