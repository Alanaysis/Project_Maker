#!/usr/bin/env python3
"""
自定义组合逻辑电路设计
Custom Combinational Circuit Design Demo

展示如何设计和构建自定义组合逻辑电路。
Demonstrates how to design and build custom combinational circuits.
"""

from src.gates import AND, OR, NOT, XOR, NAND, NOR, XNOR
from src.adders import FullAdder, RippleCarryAdder
from src.multiplier import DirectMultiplier
from src.mux_demux import Multiplexer4to1, Multiplexer8to1
from src.encoder_decoder import BinaryEncoder, BinaryDecoder, SevenSegmentDecoder
from src.comparator import Comparator4Bit
from src.logic_synthesis import MuxLogicSynthesizer


def design_voting_circuit():
    """
    设计投票电路（多数表决器）
    Design a Voting Circuit (Majority Voter)

    3人投票：超过半数同意则通过
    3-person vote: passes if majority agrees
    F(A,B,C) = AB + BC + AC
    """
    print("=" * 60)
    print("设计1: 3人多数表决器 (Majority Voter)")
    print("=" * 60)
    print("真值表 (Truth Table):")
    print("-" * 40)
    print("A | B | C | Vote")
    print("-" * 40)

    # 使用逻辑门实现：F = AB + BC + AC
    ab_gate = AND()
    bc_gate = AND()
    ac_gate = AND()
    final_or = OR()

    for a in [0, 1]:
        for b in [0, 1]:
            for c in [0, 1]:
                ab = ab_gate.evaluate(a, b)
                bc = bc_gate.evaluate(b, c)
                ac = ac_gate.evaluate(a, c)
                result = final_or.evaluate(ab, bc, ac)
                print(f"{a} | {b} | {c} |  {result}")
    print()


def design_comparator_circuit():
    """
    设计比较电路
    Design a Comparison Circuit

    比较两个4位二进制数的大小
    Compare two 4-bit binary numbers
    """
    print("=" * 60)
    print("设计2: 4位数值比较器 (4-bit Comparator)")
    print("=" * 60)

    comp = Comparator4Bit()

    test_cases = [
        (10, 10), (15, 10), (10, 15), (0, 15),
        (7, 8), (12, 3), (5, 5), (1, 0)
    ]

    print("-" * 50)
    print("A   | B   | A>B | A=B | A<B")
    print("-" * 50)

    for a, b in test_cases:
        gt, eq, lt = comp.compare(a, b)
        print(f"{a:3d} | {b:3d} |  {gt}   |  {eq}   |  {lt}")
    print()


def design_seven_segment_display():
    """
    设计7段显示驱动电路
    Design a 7-Segment Display Driver

    将BCD码转换为7段数码管驱动信号
    Convert BCD code to 7-segment display drive signals
    """
    print("=" * 60)
    print("设计3: 7段数码管显示驱动 (7-Segment Display Driver)")
    print("=" * 60)

    decoder = SevenSegmentDecoder()

    print("数字 | 段(a,b,c,d,e,f,g) | 可视化")
    print("-" * 55)

    for digit in range(10):
        segments = decoder.decode(digit)
        # 简单可视化
        a, b, c, d, e, f, g = segments
        vis = []
        vis.append(f" {1 if a else ' '} ")
        vis.append(f"{1 if f else ' '}{1 if g else ' '}{1 if b else ' '}")
        vis.append(f" {1 if d else ' '} ")
        vis.append(f"{1 if e else ' '}{1 if c else ' '} ")
        vis.append(f" {1 if d else ' '} ")

        print(f"  {digit}  |   {segments}   |")
        for line in vis:
            print(f"       | {line} |")
        print()


def design_counter_display():
    """
    设计计数器-显示电路
    Design a Counter-Display Circuit

    模拟0-9计数并显示在7段数码管上
    Simulate 0-9 counting and display on 7-segment display
    """
    print("=" * 60)
    print("设计4: 0-9计数器显示 (0-9 Counter Display)")
    print("=" * 60)

    decoder = SevenSegmentDecoder()

    for i in range(10):
        segments = decoder.decode(i)
        char = decoder.display_char(i)
        print(f"  Count {i}: {char} | 段: {segments}")
    print()


def design_logic_synth():
    """
    演示基于MUX的逻辑综合
    Demonstrate MUX-based Logic Synthesis
    """
    print("=" * 60)
    print("设计5: 基于MUX的逻辑综合 (MUX-based Logic Synthesis)")
    print("=" * 60)

    synthesizer = MuxLogicSynthesizer()

    # 设计一个3变量函数: F(A,B,C) = Σm(1,2,4,7)
    # 即当输入中1的个数为奇数时输出1（奇偶校验）
    print("目标函数: F(A,B,C) = Σm(1,2,4,7)")
    print("即：当输入中1的个数为奇数时输出1（奇偶校验器）")
    print()

    # 真值表
    truth_table = [0] * 8
    for i in range(8):
        bits = bin(i).count('1')
        truth_table[i] = bits % 2  # 奇数个1时输出1

    print("真值表:")
    print("-" * 40)
    print("A | B | C | F")
    print("-" * 40)
    for i in range(8):
        a = (i >> 2) & 1
        b = (i >> 1) & 1
        c = i & 1
        print(f"{a} | {b} | {c} | {truth_table[i]}")
    print()

    # 使用MUX实现
    func = synthesizer.implement_from_truth_table(3, truth_table)
    print("使用8:1 MUX实现:")
    print("-" * 40)
    for i in range(8):
        a = (i >> 2) & 1
        b = (i >> 1) & 1
        c = i & 1
        result = func(a, b, c)
        print(f"  F({a},{b},{c}) = {result}")
    print()

    # 综合信息
    info = synthesizer.simplify_with_mux(func, 3)
    print(f"MUX配置:")
    print(f"  变量数: {info['num_variables']}")
    print(f"  MUX类型: {info['mux_type']}")
    print(f"  输入: {info['inputs']}")
    print(f"  真值表: {info['truth_table']}")
    print()


def design_priority_interrupt_controller():
    """
    设计优先级中断控制器
    Design a Priority Interrupt Controller

    8个中断请求，优先编码器输出中断号
    8 interrupt requests, priority encoder outputs interrupt number
    """
    print("=" * 60)
    print("设计6: 优先级中断控制器 (Priority Interrupt Controller)")
    print("=" * 60)

    encoder = BinaryEncoder()

    print("模拟中断请求:")
    print("-" * 45)
    print("中断请求(IRQ7..IRQ0) | 编码输出 | 响应中断")
    print("-" * 45)

    test_cases = [
        [0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 1, 0, 0, 0, 1],
        [1, 0, 0, 1, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
    ]

    for irq in test_cases:
        code = encoder.encode(irq)
        active = [i for i, v in enumerate(reversed(irq)) if v == 1]
        print(f"  {irq}  |    {code:03b}     | IRQ{max(active) if active else 'None'}")
    print()


def design_alu_stage():
    """
    设计ALU功能单元
    Design ALU Functional Unit

    简单的算术逻辑单元功能演示
    Simple ALU function demonstration
    """
    print("=" * 60)
    print("设计7: 简易ALU功能单元 (Simple ALU Unit)")
    print("=" * 60)

    adder = RippleCarryAdder(4)
    multiplier = DirectMultiplier(4, 4)

    print("操作码 | 操作      | A  | B  | 结果")
    print("-" * 55)

    a, b = 5, 3

    # 加法
    result, _ = adder.add(a, b)
    print(f"  ADD  |  A + B    | {a} | {b} | {result}")

    # 减法
    sub_result = a - b
    print(f"  SUB  |  A - B    | {a} | {b} | {sub_result}")

    # 乘法
    result = multiplier.multiply(a, b)
    print(f"  MUL  |  A * B    | {a} | {b} | {result}")

    # AND
    result = a & b
    print(f"  AND  |  A & B    | {a} | {b} | {result}")

    # OR
    result = a | b
    print(f"  OR   |  A | B    | {a} | {b} | {result}")

    # XOR
    result = a ^ b
    print(f"  XOR  |  A ^ B    | {a} | {b} | {result}")

    # NOT A
    result = (~a) & 0xF
    print(f"  NOT  |  ~A       | {a} | -  | {result}")
    print()


if __name__ == "__main__":
    design_voting_circuit()
    design_comparator_circuit()
    design_seven_segment_display()
    design_counter_display()
    design_logic_synth()
    design_priority_interrupt_controller()
    design_alu_stage()
    print("自定义组合逻辑电路设计演示完成！")
