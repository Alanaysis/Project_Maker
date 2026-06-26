#!/usr/bin/env python3
"""
加法器/减法器仿真演示
Adder/Subtractor Simulation Demo

展示加法器和减法器的基本工作原理。
Demonstrates basic principles of adders and subtractors.
"""

from src.adders import HalfAdder, FullAdder, RippleCarryAdder, Subtracter


def demo_half_adder():
    """演示半加器"""
    print("=" * 60)
    print("半加器仿真 (Half Adder Simulation)")
    print("=" * 60)
    print("真值表 (Truth Table):")
    print("-" * 40)
    print("A | B | Sum | Carry")
    print("-" * 40)

    ha = HalfAdder()
    for a in [0, 1]:
        for b in [0, 1]:
            s, c = ha.add(a, b)
            print(f"{a} | {b} |   {s}   |   {c}")
    print()


def demo_full_adder():
    """演示全加器"""
    print("=" * 60)
    print("全加器仿真 (Full Adder Simulation)")
    print("=" * 60)
    print("真值表 (Truth Table):")
    print("-" * 50)
    print("A | B | Cin | Sum | Cout")
    print("-" * 50)

    fa = FullAdder()
    for a in [0, 1]:
        for b in [0, 1]:
            for cin in [0, 1]:
                s, cout = fa.add(a, b, cin)
                print(f"{a} | {b} |  {cin}  |   {s}   |   {cout}")
    print()


def demo_ripple_carry_adder():
    """演示行波进位加法器"""
    print("=" * 60)
    print("4位行波进位加法器仿真 (4-bit Ripple Carry Adder)")
    print("=" * 60)
    print("-" * 50)
    print("A   | B   | Sum | Carry Out")
    print("-" * 50)

    adder = RippleCarryAdder(4)

    test_cases = [
        (0, 0), (1, 0), (0, 1), (1, 1),
        (5, 3), (7, 8), (15, 1), (10, 5)
    ]

    for a, b in test_cases:
        result, carry = adder.add(a, b)
        print(f"{a:3d} | {b:3d} | {result:3d} |   {carry}")
    print()


def demo_signed_addition():
    """演示有符号数加法"""
    print("=" * 60)
    print("4位有符号数加法 (4-bit Signed Addition)")
    print("=" * 60)
    print("-" * 60)
    print("A   | B   | Sum | Carry | Overflow")
    print("-" * 60)

    adder = RippleCarryAdder(4)

    test_cases = [
        (3, 2), (-3, 2), (3, -2), (-3, -2),
        (7, 1), (-8, -1), (4, 4), (-4, -4)
    ]

    for a, b in test_cases:
        result, carry, overflow = adder.add_signed(a, b)
        ov_str = "Yes" if overflow else "No"
        print(f"{a:4d} | {b:4d} | {result:3d} |   {carry}    |    {ov_str}")
    print()


def demo_subtractor():
    """演示减法器"""
    print("=" * 60)
    print("4位减法器仿真 (4-bit Subtracter Simulation)")
    print("=" * 60)
    print("-" * 50)
    print("A   | B   | A-B | Signed(A-B)")
    print("-" * 50)

    sub = Subtracter(4)

    test_cases = [
        (5, 3), (7, 0), (10, 5), (15, 1),
        (-3, 2), (3, -2), (-3, -2)
    ]

    for a, b in test_cases:
        try:
            result = sub.subtract(a, b)
            signed_result = sub.subtract_signed(a, b)
            print(f"{a:4d} | {b:4d} | {result:3d} |    {signed_result:5d}")
        except ValueError as e:
            print(f"{a:4d} | {b:4d} |  N/A  |    {e}")
    print()


def demo_large_addition():
    """演示大数加法"""
    print("=" * 60)
    print("8位行波进位加法器 (8-bit Ripple Carry Adder)")
    print("=" * 60)
    print("-" * 55)
    print("A    | B    | Sum  | Carry Out | Expected")
    print("-" * 55)

    adder = RippleCarryAdder(8)

    test_cases = [
        (255, 1), (128, 127), (100, 50), (200, 100),
        (0, 0), (1, 1)
    ]

    for a, b in test_cases:
        result, carry = adder.add(a, b)
        expected = a + b
        ov = f"+{expected}" if expected > 255 else str(expected)
        print(f"{a:4d} | {b:4d} | {result:4d} |    {carry}      |    {ov}")
    print()


if __name__ == "__main__":
    demo_half_adder()
    demo_full_adder()
    demo_ripple_carry_adder()
    demo_signed_addition()
    demo_subtractor()
    demo_large_addition()
    print("加法器/减法器仿真演示完成！")
