"""
Example 2: Register File Comparison
示例2：寄存器文件对比

This script demonstrates the register file differences between ISAs,
including register count, naming conventions, and calling conventions.

Key concepts:
- More registers reduce memory traffic (fewer loads/stores)
- Register naming affects compiler complexity
- Calling convention determines which registers must be saved/restored
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from register_file import RegisterFileComparator


def demonstrate_register_comparison():
    """Demonstrate register file comparison."""
    print("=" * 80)
    print("EXAMPLE 2: REGISTER FILE COMPARISON")
    print("示例2：寄存器文件对比")
    print("=" * 80)

    comparator = RegisterFileComparator()

    # Show register comparison table
    print("\n--- Register File Comparison Table ---")
    print("寄存器文件对比表")
    print("=" * 90)

    headers = ["ISA", "GPRs", "Width", "FP Regs", "Vector", "Cond Codes"]
    print(f"{headers[0]:<10} {headers[1]:>6} {headers[2]:>12} {headers[3]:>10} "
          f"{headers[4]:>10} {headers[5]:>12}")
    print("-" * 80)

    for row in comparator.compare_registers():
        print(f"{row['ISA']:<10} {row['GPRs']:>6} {row['Width']:>12} "
              f"{row['FP']:>10} {row['Vector']:>10} {row['Condition Codes']:>12}")

    # Show calling conventions
    print("\n" + "=" * 80)
    print("CALLING CONVENTION COMPARISON")
    print("调用约定对比")
    print("=" * 80)

    isas = ["RISC-V", "ARM", "x86", "MIPS"]
    for isa in isas:
        cc = comparator.get_calling_convention(isa)
        reg_file = comparator.get_register_file(isa)

        print(f"\n--- {isa} ---")
        print(f"  Total GPRs: {reg_file.gpr_count}")
        print(f"  Register width: {reg_file.gpr_width_bits}-bit")
        print(f"  Caller-saved ({len(cc['caller'])} regs): {', '.join(cc['caller'])}")
        print(f"  Callee-saved ({len(cc['callee'])} regs): {', '.join(cc['callee'])}")

        # Show argument/return register conventions
        if isa == "RISC-V":
            print(f"  Arguments: a0-a7 (8 registers)")
            print(f"  Return values: a0, a1")
            print(f"  Stack pointer: sp (x2)")
            print(f"  Return address: ra (x1)")
        elif isa == "ARM":
            print(f"  Arguments: x0-x7 (8 registers)")
            print(f"  Return values: x0, x1")
            print(f"  Stack pointer: SP")
            print(f"  Link register: LR (x30)")
        elif isa == "x86":
            print(f"  Arguments: rdi, rsi, rdx, rcx, r8, r9 (6 registers)")
            print(f"  Return values: rax, rdx")
            print(f"  Stack pointer: rsp")
            print(f"  Return address: on stack")
        elif isa == "MIPS":
            print(f"  Arguments: a0-a3 (4 registers)")
            print(f"  Return values: v0, v1")
            print(f"  Stack pointer: sp ($29)")
            print(f"  Return address: ra ($31)")

    # Register pressure analysis
    print("\n" + "=" * 80)
    print("REGISTER PRESSURE ANALYSIS")
    print("寄存器压力分析")
    print("=" * 80)

    # Simulate different scenarios
    scenarios = [
        ("Simple loop", 4),
        ("Function with locals", 8),
        ("Compiler intermediate", 16),
        ("Complex function", 24),
        ("Heavy compilation", 28),
    ]

    print(f"\n{'Scenario':<25} {'RISC-V':>10} {'ARM':>10} {'x86':>10} {'MIPS':>10}")
    print("-" * 65)

    for scenario, needed in scenarios:
        pressures = []
        for isa in ["RISC-V", "ARM", "x86", "MIPS"]:
            pressure = comparator.analyze_register_pressure(isa, needed)
            pressures.append(f"{pressure:.2f}")
        print(f"{scenario:<25} {pressures[0]:>10} {pressures[1]:>10} "
              f"{pressures[2]:>10} {pressures[3]:>10}")

    print("\nNote: Pressure > 1.0 means spilling to memory is necessary")
    print("注意：压力 > 1.0 表示需要向内存溢出寄存器")

    print("=" * 80)


if __name__ == "__main__":
    demonstrate_register_comparison()
