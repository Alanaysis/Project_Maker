#!/usr/bin/env python3
"""
译码器/编码器演示
Decoder/Encoder Demo

展示编码器和译码器的工作原理。
Demonstrates how encoders and decoders work.
"""

from src.encoder_decoder import BinaryEncoder, BCDToBinaryEncoder
from src.encoder_decoder import BinaryDecoder, BCDDecoder, SevenSegmentDecoder


def demo_binary_encoder():
    """演示二进制优先编码器"""
    print("=" * 60)
    print("8线-3线优先编码器仿真 (8-to-3 Priority Encoder)")
    print("=" * 60)
    print("Input (I7..I0)     | Output (CBA) | Active Input")
    print("-" * 55)

    encoder = BinaryEncoder()

    test_cases = [
        [0, 0, 0, 0, 0, 0, 0, 0],  # 所有输入为0
        [0, 0, 0, 0, 0, 0, 0, 1],  # I0有效
        [0, 1, 0, 0, 0, 0, 0, 1],  # I0和I1有效（I1优先）
        [1, 0, 1, 0, 1, 0, 1, 0],  # 多个输入有效（最高优先I7）
        [1, 1, 1, 1, 1, 1, 1, 1],  # 所有输入有效
        [0, 0, 0, 1, 0, 0, 0, 0],  # I3有效
    ]

    for inputs in test_cases:
        output = encoder.encode(inputs)
        active = [i for i, v in enumerate(reversed(inputs)) if v == 1]
        binary_str = f"{output:03b}"
        print(f"  {inputs}  |   {binary_str}    | I{active if active else 'none'}")
    print()


def demo_bcd_encoder():
    """演示BCD编码器"""
    print("=" * 60)
    print("BCD编码器仿真 (BCD Encoder)")
    print("=" * 60)
    print("Decimal | BCD (4-bit)")
    print("-" * 30)

    encoder = BCDToBinaryEncoder()

    for i in range(10):
        bcd = encoder.encode(i)
        print(f"  {i}       |   {bcd:04b}")
    print()


def demo_binary_decoder():
    """演示二进制译码器"""
    print("=" * 60)
    print("3线-8线译码器仿真 (3-to-8 Line Decoder)")
    print("=" * 60)
    print("Input (CBA) | Output (Y7..Y0)")
    print("-" * 45)

    decoder = BinaryDecoder()

    for i in range(8):
        c = (i >> 2) & 1
        b = (i >> 1) & 1
        a = i & 1
        outputs = decoder.decode([c, b, a])
        print(f"  {c}{b}{a}       |   {outputs}")
    print()


def demo_bcd_decoder():
    """演示BCD译码器"""
    print("=" * 60)
    print("BCD译码器仿真 (BCD Decoder)")
    print("=" * 60)
    print("BCD Input | Decimal Output")
    print("-" * 35)

    decoder = BCDDecoder()

    for i in range(10):
        outputs = decoder.decode(i)
        active = [idx for idx, v in enumerate(outputs) if v == 1]
        print(f"  {i:04b}      |   Line {active[0]} active")
    print()


def demo_seven_segment():
    """演示7段译码器"""
    print("=" * 60)
    print("7段译码器仿真 (7-Segment Decoder)")
    print("=" * 60)
    print("Digit | Segments (a-g) | Display")
    print("-" * 45)

    decoder = SevenSegmentDecoder()

    for i in range(10):
        segments = decoder.decode(i)
        display = decoder.display_char(i)
        print(f"  {i}   |     {segments}     |   {display}")
    print()

    # 显示字符可视化
    print("字符显示示例 (Character Display Example):")
    print("-" * 45)
    for i in range(10):
        segments = decoder.decode(i)
        # a
        top = " --- "
        # f   g   b
        mid1 = "|     |"
        mid2 = "  --- "
        # e   d   c
        mid3 = "|     |"
        bot = " --- "

        # 根据段值修改显示
        if segments[0]:  # a
            top = " --- "
        else:
            top = "     "

        fg_b = ""
        if segments[5]:  # f
            fg_b += "|"
        else:
            fg_b += " "
        fg_b += "     "
        if segments[6]:  # g
            fg_b += " --- "
        else:
            fg_b += "     "
        if segments[1]:  # b
            fg_b += "|"
        else:
            fg_b += " "

        mid1 = fg_b

        if segments[6]:  # g
            mid2 = " --- "
        else:
            mid2 = "     "

        ed_c = ""
        if segments[4]:  # e
            ed_c += "|"
        else:
            ed_c += " "
        ed_c += "     "
        if segments[3]:  # d
            ed_c += " --- "
        else:
            ed_c += "     "
        if segments[2]:  # c
            ed_c += "|"
        else:
            ed_c += " "

        mid3 = ed_c

        if segments[3]:  # d
            bot = " --- "
        else:
            bot = "     "

        print(f"  Digit {i}:")
        print(f"    {top}")
        print(f"    {mid1}{mid2}")
        print(f"    {mid3}{bot}")
        print()


if __name__ == "__main__":
    demo_binary_encoder()
    demo_bcd_encoder()
    demo_binary_decoder()
    demo_bcd_decoder()
    demo_seven_segment()
    print("译码器/编码器演示完成！")
