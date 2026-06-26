#!/usr/bin/env python3
"""
多路选择器演示
Multiplexer Demo

展示不同大小的多路选择器的工作原理。
Demonstrates how multiplexers of different sizes work.
"""

from src.mux_demux import Multiplexer2to1, Multiplexer4to1, Multiplexer8to1
from src.mux_demux import Demultiplexer1to2, Demultiplexer1to8


def demo_mux2to1():
    """演示2:1多路选择器"""
    print("=" * 60)
    print("2:1多路选择器仿真 (2:1 Multiplexer Simulation)")
    print("=" * 60)
    print("S | I0 | I1 | Output")
    print("-" * 35)

    mux = Multiplexer2to1()

    for s in [0, 1]:
        for i0 in [0, 1]:
            for i1 in [0, 1]:
                out = mux.select(i0, i1, s)
                print(f"{s} |  {i0}  |  {i1}  |   {out}")
    print()


def demo_mux4to1():
    """演示4:1多路选择器"""
    print("=" * 60)
    print("4:1多路选择器仿真 (4:1 Multiplexer Simulation)")
    print("=" * 60)
    print("S1 | S0 | Selected Input | Output")
    print("-" * 45)

    mux = Multiplexer4to1()

    # 设置输入
    inputs = [1, 0, 1, 1]  # I0=1, I1=0, I2=1, I3=1

    for s1 in [0, 1]:
        for s0 in [0, 1]:
            index = (s1 << 1) | s0
            out = mux.select(*inputs, s1, s0)
            print(f" {s1}  |  {s0}  |     I{index}      |   {out}")
    print()


def demo_mux8to1():
    """演示8:1多路选择器"""
    print("=" * 60)
    print("8:1多路选择器仿真 (8:1 Multiplexer Simulation)")
    print("=" * 60)
    print("S2 | S1 | S0 | Selected Input | Output")
    print("-" * 55)

    mux = Multiplexer8to1()

    # 设置输入
    inputs = [0, 1, 1, 0, 1, 0, 0, 1]

    for sel in range(8):
        s2 = (sel >> 2) & 1
        s1 = (sel >> 1) & 1
        s0 = sel & 1
        out = mux.select(inputs, s2, s1, s0)
        print(f" {s2}  |  {s1}  |  {s0}  |     I{sel}      |   {out}")
    print()


def demo_demux1to2():
    """演示1:2解复用器"""
    print("=" * 60)
    print("1:2解复用器仿真 (1:2 Demultiplexer Simulation)")
    print("=" * 60)
    print("Data | EN | Sel | Output")
    print("-" * 40)

    demux = Demultiplexer1to2()

    for data in [0, 1]:
        for en in [0, 1]:
            for sel in [0, 1]:
                out = demux.distribute(data, en, sel)
                print(f" {data}  |  {en}  |  {sel}  |   {out}")
    print()


def demo_demux1to8():
    """演示1:8解复用器"""
    print("=" * 60)
    print("1:8解复用器仿真 (1:8 Demultiplexer Simulation)")
    print("=" * 60)

    demux = Demultiplexer1to8()

    # 演示数据=1的情况
    print("Data = 1:")
    print("-" * 45)
    for sel in range(8):
        outputs = demux.distribute(1, 0, sel)
        # 显示选中输出的位置
        active = [i for i, v in enumerate(outputs) if v == 1]
        print(f"  Sel={sel}: outputs = [{', '.join(map(str, outputs))}] -> 输出线 {active[0]} 有效")
    print()

    # 演示使能禁用的情况
    print("Data = 1, EN = 1 (禁用):")
    outputs = demux.distribute(1, 1, 3)
    print(f"  outputs = [{', '.join(map(str, outputs))}] -> 所有输出为0")
    print()


def demo_mux_as_logic_gate():
    """演示使用MUX实现逻辑门"""
    print("=" * 60)
    print("使用4:1 MUX实现逻辑函数")
    print("Implementing Logic Functions with 4:1 MUX")
    print("=" * 60)
    print()

    mux = Multiplexer4to1()

    # 实现AND函数: f(A,B) = A AND B
    print("实现 AND 函数 (Implement AND function):")
    print("  真值表: f(0,0)=0, f(0,1)=0, f(1,0)=0, f(1,1)=1")
    and_table = [0, 0, 0, 1]
    for a in [0, 1]:
        for b in [0, 1]:
            index = (a << 1) | b
            out = and_table[index]
            print(f"  AND({a}, {b}) = {out}")
    print()

    # 实现OR函数: f(A,B) = A OR B
    print("实现 OR 函数 (Implement OR function):")
    print("  真值表: f(0,0)=0, f(0,1)=1, f(1,0)=1, f(1,1)=1")
    or_table = [0, 1, 1, 1]
    for a in [0, 1]:
        for b in [0, 1]:
            index = (a << 1) | b
            out = or_table[index]
            print(f"  OR({a}, {b}) = {out}")
    print()

    # 实现XOR函数: f(A,B) = A XOR B
    print("实现 XOR 函数 (Implement XOR function):")
    print("  真值表: f(0,0)=0, f(0,1)=1, f(1,0)=1, f(1,1)=0")
    xor_table = [0, 1, 1, 0]
    for a in [0, 1]:
        for b in [0, 1]:
            index = (a << 1) | b
            out = xor_table[index]
            print(f"  XOR({a}, {b}) = {out}")
    print()


if __name__ == "__main__":
    demo_mux2to1()
    demo_mux4to1()
    demo_mux8to1()
    demo_demux1to2()
    demo_demux1to8()
    demo_mux_as_logic_gate()
    print("多路选择器演示完成！")
