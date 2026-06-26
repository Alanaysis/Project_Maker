"""
Example 3: Addressing Mode Comparison
示例3：寻址方式对比

This script demonstrates the addressing mode differences between ISAs.
Addressing modes determine how instructions specify their operands.

Key concepts:
- Simpler addressing modes enable faster decode
- Complex addressing modes reduce instruction count but increase decode complexity
- x86's complex addressing is a hallmark of CISC design philosophy
- RISC-V's minimal addressing enables simple, fast hardware
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from addressing_modes import AddressingModeComparator


def demonstrate_addressing_modes():
    """Demonstrate addressing mode comparison."""
    print("=" * 80)
    print("EXAMPLE 3: ADDRESSING MODE COMPARISON")
    print("示例3：寻址方式对比")
    print("=" * 80)

    comparator = AddressingModeComparator()

    # Show addressing modes for each ISA
    isas = ["RISC-V", "ARM", "x86", "MIPS"]
    for isa in isas:
        modes = comparator.get_addressing_modes(isa)
        complexity = comparator.get_complexity_rating(isa)
        scaled = comparator.is_scaled_index_supported(isa)

        print(f"\n--- {isa} (Complexity: {complexity}, Scaled Index: {scaled}) ---")
        print(f"  {'Mode':<30} {'Type':<25} {'Example':<30}")
        print(f"  {'-'*28} {'-'*23} {'-'*28}")
        for mode in modes:
            print(f"  {mode.name:<30} {mode.mode_type.value:<25} {mode.example:<30}")

    # Comparison summary
    print("\n" + "=" * 80)
    print("DESIGN PHILOSOPHY IMPLICATIONS")
    print("设计哲学影响")
    print("=" * 80)

    print("""
  RISC Philosophy (RISC-V, MIPS):
  - Minimal addressing modes reduce decode complexity
  - Load/Store architecture: only LOAD/STORE access memory
  - All registers are general-purpose
  - Simpler hardware = higher clock speeds possible
  - Compiler handles complex addressing via multiple instructions

  CISC Philosophy (x86):
  - Complex addressing modes reduce instruction count
  - Memory-to-memory operations possible
  - More compact code for certain operations
  - Complex decode hardware (micro-op translation in modern CPUs)
  - Hardware handles complexity that compiler would manage

  ARM (Hybrid):
  - AArch64: RISC-like fixed encoding
  - Thumb-2: Variable-length for code density
  - Balanced approach between simplicity and functionality
""")

    print("=" * 80)
    print("ADDRESSING MODE COMPLEXITY TRADE-OFFS")
    print("寻址方式复杂度权衡")
    print("=" * 80)

    tradeoffs = [
        ("Decode complexity", "Low (RISC-V)", "Medium (ARM)", "High (x86)", "Low (MIPS)"),
        ("Code density", "Medium", "High", "High", "Medium"),
        ("Pipeline simplicity", "Easy", "Medium", "Hard", "Easy"),
        ("Compiler complexity", "High", "Medium", "Low", "High"),
        ("Memory access flexibility", "Low", "Medium", "High", "Low"),
    ]

    print(f"\n{'Aspect':<30} {'RISC-V':<20} {'ARM':<20} {'x86':<20} {'MIPS':<20}")
    print("-" * 95)
    for aspect, riscv, arm, x86, mips in tradeoffs:
        print(f"{aspect:<30} {riscv:<20} {arm:<20} {x86:<20} {mips:<20}")

    print("=" * 80)


if __name__ == "__main__":
    demonstrate_addressing_modes()
