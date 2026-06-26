"""
Register Operations Demo / 寄存器操作演示

Demonstrates SIPO, PISO, PIPO, and bidirectional shift registers.
演示SIPO、PISO、PIPO和双向移位寄存器。

Run with: python examples/03_register_operations.py
"""

from src.register import SIPORegister, PISOResister, PIPORegister, BidirectionalShiftRegister


def demo_sipo_register():
    """Demonstrate Serial-In Parallel-Out register / 演示串行输入并行输出寄存器"""
    print("=" * 60)
    print("SIPO Register / 串行输入并行输出寄存器")
    print("=" * 60)

    sipo = SIPORegister(width=8)
    print(f"Initial state: {sipo.get_binary_string()}")
    print()

    # Shift in a byte serially
    data = 0b10110011
    bits = [(data >> i) & 1 for i in range(7, -1, -1)]  # MSB first
    print(f"Shifting in: {data} (binary: {format(data, '08b')})")
    print()
    print(f"  Step | Data In | Register Value")
    print("  " + "-" * 38)

    for i, bit in enumerate(bits):
        sipo.shift_in(bit)
        print(f"  {i+1:5d} |   {bit}     | {sipo.get_binary_string()}")

    print()
    print("Parallel output:", sipo.get_parallel_output())
    print()
    print("Use case: Converting serial data to parallel for processing.")
    print("用途：将串行数据转换为并行进行处理。")
    print()


def demo_piso_register():
    """Demonstrate Parallel-In Serial-Out register / 演示并行输入串行输出寄存器"""
    print("=" * 60)
    print("PISO Register / 并行输入串行输出寄存器")
    print("=" * 60)

    piso = PISOResister(width=8)
    print(f"Initial state: {piso.get_binary_string()}")
    print()

    # Parallel load
    data = 0b11010101
    piso.parallel_load(data)
    print(f"Parallel loaded: {data} (binary: {format(data, '08b')})")
    print()

    # Shift out
    print("Shifting out bits:")
    print(f"  Step | Shift Out | Remaining Value")
    print("  " + "-" * 40)

    for i in range(8):
        bit = piso.shift_out()
        print(f"  {i+1:5d} |    {bit}     | {piso.get_binary_string()}")

    print()
    print("Serial output:", piso.get_serial_output())
    print()
    print("Use case: Converting parallel data to serial for transmission.")
    print("用途：将并行数据转换为串行进行传输。")
    print()


def demo_pipo_register():
    """Demonstrate Parallel-In Parallel-Out register / 演示并行输入并行输出寄存器"""
    print("=" * 60)
    print("PIPO Register / 并行输入并行输出寄存器")
    print("=" * 60)

    pipo = PIPORegister(width=8)
    print(f"Initial state: {pipo.get_binary_string()}")
    print()

    # Load and read multiple values
    test_values = [0b10101010, 0b11001100, 0b11110000, 0b00001111]

    print(f"  Step | Load Value    | Read Value    | Bits (MSB first)")
    print("  " + "-" * 55)

    for i, val in enumerate(test_values):
        pipo.parallel_load(val)
        read_val = pipo.parallel_read()
        bits = pipo.get_bits()
        print(f"  {i+1:5d} | {format(val, '08b')} | {format(read_val, '08b')} | {bits}")

    print()
    print("Use case: Temporary data storage, data buffering.")
    print("用途：临时数据存储、数据缓冲。")
    print()


def demo_bidirectional_shift_register():
    """Demonstrate bidirectional shift register / 演示双向移位寄存器"""
    print("=" * 60)
    print("Bidirectional Shift Register / 双向移位寄存器")
    print("=" * 60)

    reg = BidirectionalShiftRegister(width=8)

    # Parallel load initial value
    initial = 0b10000000
    reg.parallel_load(initial)
    print(f"Initial (parallel load): {reg.get_binary_string()}")
    print()

    # Shift right
    print("Shifting right (serial_in=1):")
    print(f"  Step | Value        | Direction")
    print("  " + "-" * 35)

    reg.set_direction("right")
    for i in range(4):
        reg.shift(1)
        print(f"  {i+1:5d} | {reg.get_binary_string()} | RIGHT")

    print()

    # Shift left
    print("Shifting left (serial_in=0):")
    reg.set_direction("left")
    for i in range(4):
        reg.shift(0)
        print(f"  {i+5:5d} | {reg.get_binary_string()} | LEFT")

    print()
    print("Use case: Universal shift operations, data manipulation.")
    print("用途：通用移位操作、数据操纵。")
    print()


def demo_register_as_delay_line():
    """Demonstrate register as delay line / 演示寄存器作为延迟线"""
    print("=" * 60)
    print("Register as Delay Line / 寄存器作为延迟线")
    print("=" * 60)

    print("A shift register can delay a signal by N clock cycles.")
    print("移位寄存器可以将信号延迟N个时钟周期。")
    print()

    sipo = SIPORegister(width=8)

    # Shift in a single '1' bit
    for i in range(8):
        sipo.shift_in(0)

    # Now shift in a '1'
    sipo.shift_in(1)

    # Shift out and observe the delay
    print("Observing the '1' bit as it shifts through:")
    print(f"  Step | Output | Description")
    print("  " + "-" * 35)

    for i in range(10):
        if i < 8:
            bit = 0
        else:
            bit = sipo.shift_out()

        desc = "Moving through register" if i < 8 else "Exiting" if bit == 1 else "Empty"
        print(f"  {i+1:5d} |   {bit}    | {desc}")

    print()
    print("The '1' appears at the output after 8 clock cycles.")
    print("'1'在8个时钟周期后出现在输出端。")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Sequential Logic Circuit - Register Operations")
    print("时序逻辑电路 - 寄存器操作")
    print("=" * 60 + "\n")

    demo_sipo_register()
    demo_piso_register()
    demo_pipo_register()
    demo_bidirectional_shift_register()
    demo_register_as_delay_line()

    print("Done! / 完成!")
