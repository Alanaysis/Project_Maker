"""
Example 1: Instruction Encoding Comparison
示例1：指令编码对比

This script demonstrates the differences in instruction encoding between
RISC-V, ARM, x86, and MIPS architectures.

Key concepts demonstrated:
- Fixed-length encoding (RISC-V, MIPS): All instructions are the same size
- Variable-length encoding (x86): Instructions vary from 1-15 bytes
- Code density implications for cache and memory
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from instruction_encoding import InstructionEncoder, CodeDensityAnalyzer


def demonstrate_encoding():
    """Demonstrate instruction encoding differences."""
    print("=" * 80)
    print("EXAMPLE 1: INSTRUCTION ENCODING COMPARISON")
    print("示例1：指令编码对比")
    print("=" * 80)

    encoder = InstructionEncoder()

    # Show instruction formats for each ISA
    print("\n--- RISC-V Instruction Formats ---")
    print("RISC-V uses fixed 32-bit encoding with 6 standard formats:")
    print("  R-type: Register operations (add, sub, and, etc.)")
    print("  I-type: Immediate and load operations")
    print("  S-type: Store operations")
    print("  B-type: Branch operations")
    print("  U-type: Upper immediate operations")
    print("  J-type: Jump operations")

    riscv_formats = encoder.get_instruction_formats("RISC-V")
    for fmt_name, fmt in riscv_formats.items():
        print(f"\n  Format: {fmt_name}")
        print(f"    Size: {fmt.total_bits} bits")
        print(f"    Fields: {' -> '.join(f['name'] for f in fmt.fields)}")

    print("\n--- ARM AArch64 Instruction Formats ---")
    print("ARM AArch64 uses fixed 32-bit encoding:")
    arm_formats = encoder.get_instruction_formats("ARM")
    for fmt_name, fmt in arm_formats.items():
        print(f"\n  Format: {fmt_name}")
        print(f"    Size: {fmt.total_bits} bits")

    print("\n--- MIPS Instruction Formats ---")
    print("MIPS uses fixed 32-bit encoding with 3 standard formats:")
    mips_formats = encoder.get_instruction_formats("MIPS")
    for fmt_name, fmt in mips_formats.items():
        print(f"\n  Format: {fmt_name}")
        print(f"    Size: {fmt.total_bits} bits")

    print("\n--- x86-64 Encoding ---")
    print("x86-64 uses variable-length encoding (1-15 bytes):")
    print("  Prefix bytes: Optional operand size, address size, lock, etc.")
    print("  Opcode: 1-3 bytes identifying the instruction")
    print("  ModR/M: Register/operand specification")
    print("  SIB: Scale-Index-Base addressing")
    print("  Displacement: 0, 1, 2, or 4 bytes")
    print("  Immediate: 0, 1, 2, or 4 bytes")

    # Show common instructions
    print("\n" + "=" * 80)
    print("COMMON INSTRUCTIONS COMPARISON")
    print("常用指令对比")
    print("=" * 80)

    isas = ["RISC-V", "ARM", "x86", "MIPS"]
    print(f"\n{'Instruction':<30} {'RISC-V':<20} {'ARM':<20} {'x86':<20} {'MIPS':<20}")
    print("-" * 110)

    # Common operations and their ISA equivalents
    operations = [
        ("Addition", "add rd, rs1, rs2", "add rd, rn, rm", "add r64, r/m64", "add $t0, $t1, $t2"),
        ("Load Word", "lw rd, offset(rs1)", "ldr rt, [rn, imm]", "mov r64, [mem]", "lw $t0, offset($s0)"),
        ("Store Word", "sw rs2, offset(rs1)", "str rt, [rn, imm]", "mov [mem], r64", "sw $t0, offset($s0)"),
        ("Branch Equal", "beq rs1, rs2, label", "cbz rn, label", "jmp label", "beq $t0, $t1, label"),
        ("Jump", "jal rd, label", "bl label", "call label", "j label"),
        ("Immediate Add", "addi rd, rs1, imm", "add rd, rn, #imm", "mov r64, imm", "addi $t0, $s0, imm"),
    ]

    for op, riscv, arm, x86, mips in operations:
        print(f"{op:<30} {riscv:<20} {arm:<20} {x86:<20} {mips:<20}")

    print("=" * 80)


def demonstrate_code_density():
    """Demonstrate code density differences."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1B: CODE DENSITY ANALYSIS")
    print("示例1B：代码密度分析")
    print("=" * 80)

    analyzer = CodeDensityAnalyzer()

    # Simulate a typical code mix
    code_mix = {
        "add": 20,
        "load": 15,
        "store": 10,
        "branch": 10,
        "jump": 5,
        "sub": 8,
        "and": 5,
        "or": 5,
    }

    code_sizes = analyzer.analyze_code_density(code_mix)

    print(f"\nCode mix analysis for a typical program:")
    print(f"  Total instructions: {sum(code_mix.values())}")
    print(f"  Instruction breakdown:")
    for instr, count in sorted(code_mix.items(), key=lambda x: -x[1]):
        print(f"    {instr}: {count} ({100*count/sum(code_mix.values()):.1f}%)")

    print(f"\n{'ISA':<12} {'Total Bytes':>14} {'Avg Bytes/Instr':>18} {'Density vs RISC-V':>18}")
    print("-" * 70)

    riscv_size = code_sizes["RISC-V"]
    for isa in ["RISC-V", "MIPS", "ARM", "x86"]:
        size = code_sizes[isa]
        avg = size / sum(code_mix.values())
        ratio = (riscv_size / size) * 100 if size > 0 else 0
        print(f"{isa:<12} {size:>14} {avg:>18.2f} {ratio:>17.1f}%")

    print("\nKey Insight (关键见解):")
    print("  - RISC-V and MIPS have predictable code size (4 bytes/instruction)")
    print("  - x86 achieves better code density for simple operations")
    print("  - ARM provides a balance with Thumb-2 encoding")
    print("  - Code density matters for: cache efficiency, ROM/flash size, download size")

    print("=" * 80)


if __name__ == "__main__":
    demonstrate_encoding()
    demonstrate_code_density()
