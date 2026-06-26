"""
Example 5: Complete ISA Comparison Demo
示例5：完整ISA对比演示

This script runs a comprehensive comparison of all four ISAs,
covering encoding, registers, addressing modes, and performance.

This is the main demonstration script for the project.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from instruction_encoding import InstructionEncoder
from register_file import RegisterFileComparator
from addressing_modes import AddressingModeComparator
from performance_simulation import PerformanceSimulator


def run_comprehensive_comparison():
    """Run a comprehensive ISA comparison."""
    print("=" * 80)
    print("COMPREHENSIVE ISA COMPARISON")
    print("全面ISA对比")
    print("=" * 80)

    # Section 1: Architecture Overview
    print("\n" + "=" * 80)
    print("1. ARCHITECTURE OVERVIEW")
    print("1. 架构概览")
    print("=" * 80)

    arch_data = [
        {
            "ISA": "RISC-V",
            "Type": "RISC",
            "Origin": "UC Berkeley (2010)",
            "License": "Open (BSD)",
            "Design": "Simple, modular, extensible"
        },
        {
            "ISA": "ARM",
            "Type": "RISC",
            "Origin": "Acorn (1983)",
            "License": "Proprietary (licensed)",
            "Design": "Power-efficient, mobile-focused"
        },
        {
            "ISA": "x86",
            "Type": "CISC",
            "Origin": "Intel (1978)",
            "License": "Proprietary",
            "Design": "Backward compatible, feature-rich"
        },
        {
            "ISA": "MIPS",
            "Type": "RISC",
            "Origin": "Stanford (1984)",
            "License": "Proprietary (now open)",
            "Design": "Educational, embedded systems"
        },
    ]

    print(f"\n{'ISA':<10} {'Type':<8} {'Origin':<20} {'License':<20} {'Design Philosophy':<25}")
    print("-" * 90)
    for row in arch_data:
        print(f"{row['ISA']:<10} {row['Type']:<8} {row['Origin']:<20} "
              f"{row['License']:<20} {row['Design']:<25}")

    # Section 2: Design Philosophy
    print("\n" + "=" * 80)
    print("2. DESIGN PHILOSOPHY COMPARISON")
    print("2. 设计哲学对比")
    print("=" * 80)

    philosophy = [
        ("Instruction Set", "RISC: Simple, orthogonal", "RISC: Simple, optimized",
         "CISC: Complex, legacy", "RISC: Simple, educational"),
        ("Encoding", "Fixed 32-bit", "Fixed 32-bit (AArch64)",
         "Variable 1-15 bytes", "Fixed 32-bit"),
        ("Memory Access", "Load/Store only", "Load/Store only",
         "Memory-to-memory", "Load/Store only"),
        ("Register File", "32 GPRs", "31 GPRs", "16 GPRs", "32 GPRs"),
        ("Condition Codes", "Implicit (flags)", "Explicit (NZCV)",
         "Explicit (RFLAGS)", "Implicit (zero flag)"),
        ("Endianness", "Configurable", "Configurable",
         "Little-endian", "Configurable"),
        ("Addressing", "Minimal (5 modes)", "Rich (7 modes)",
         "Complex (7+ modes)", "Minimal (5 modes)"),
        ("Pipeline", "5 stages", "13 stages", "15+ stages", "5 stages"),
    ]

    print(f"\n{'Aspect':<20} {'RISC-V':<25} {'ARM':<25} {'x86':<25} {'MIPS':<25}")
    print("-" * 105)
    for row in philosophy:
        print(f"{row[0]:<20} {row[1]:<25} {row[2]:<25} {row[3]:<25} {row[4]:<25}")

    # Section 3: ISA Comparison Tables
    print("\n" + "=" * 80)
    print("3. ISA COMPARISON TABLES")
    print("3. ISA对比表")
    print("=" * 80)

    # Register comparison
    print("\n--- Register Comparison ---")
    registrar = RegisterFileComparator()
    register_table = registrar.compare_registers()
    print(f"{'ISA':<10} {'GPRs':>6} {'Width':>12} {'FP':>6} {'Vector':>8} {'Cond':>8}")
    print("-" * 55)
    for row in register_table:
        print(f"{row['ISA']:<10} {row['GPRs']:>6} {row['Width']:>12} "
              f"{row['FP']:>6} {row['Vector']:>8} {row['Condition Codes']:>8}")

    # Addressing mode comparison
    print("\n--- Addressing Mode Comparison ---")
    addr_comp = AddressingModeComparator()
    addr_table = addr_comp.compare_addressing_modes()
    print(f"{'ISA':<10} {'Modes':>8} {'Complexity':>14} {'Max Disp':>14}")
    print("-" * 50)
    for row in addr_table:
        print(f"{row['ISA']:<10} {row['Modes']:>8} {row['Complex']:>14} "
              f"{row['MaxDisplacement']:>14}")

    # Section 4: Performance Comparison
    print("\n" + "=" * 80)
    print("4. PERFORMANCE COMPARISON")
    print("4. 性能对比")
    print("=" * 80)

    # Create a simple benchmark
    benchmark_instructions = {
        "RISC-V": [
            {"name": "addi x1, x0, 10", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "addi x2, x0, 20", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "add x3, x1, x2", "type": "arith", "regs_read": 2, "regs_write": 1},
            {"name": "li x4, 100", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "sw x3, 0(x4)", "type": "store", "regs_read": 2, "regs_write": 0},
            {"name": "lw x5, 0(x4)", "type": "load", "regs_read": 1, "regs_write": 1},
            {"name": "sub x6, x5, x3", "type": "arith", "regs_read": 2, "regs_write": 1},
            {"name": "beq x6, x0, end", "type": "branch", "regs_read": 2, "regs_write": 0},
            {"name": "addi x7, x0, 1", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "end:", "type": "label", "regs_read": 0, "regs_write": 0},
        ],
        "ARM": [
            {"name": "mov x1, #10", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "mov x2, #20", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "add x3, x1, x2", "type": "arith", "regs_read": 2, "regs_write": 1},
            {"name": "mov x4, #100", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "str x3, [x4]", "type": "store", "regs_read": 2, "regs_write": 0},
            {"name": "ldr x5, [x4]", "type": "load", "regs_read": 1, "regs_write": 1},
            {"name": "sub x6, x5, x3", "type": "arith", "regs_read": 2, "regs_write": 1},
            {"name": "cbz x6, end", "type": "branch", "regs_read": 1, "regs_write": 0},
            {"name": "mov x7, #1", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "end:", "type": "label", "regs_read": 0, "regs_write": 0},
        ],
        "x86": [
            {"name": "mov eax, 10", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "mov ebx, 20", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "add ecx, eax", "type": "arith", "regs_read": 2, "regs_write": 1},
            {"name": "mov edx, 100", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "mov [edx], ecx", "type": "store", "regs_read": 2, "regs_write": 0},
            {"name": "mov eax, [edx]", "type": "load", "regs_read": 1, "regs_write": 1},
            {"name": "sub eax, ecx", "type": "arith", "regs_read": 2, "regs_write": 1},
            {"name": "je end", "type": "branch", "regs_read": 0, "regs_write": 0},
            {"name": "mov edi, 1", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "end:", "type": "label", "regs_read": 0, "regs_write": 0},
        ],
        "MIPS": [
            {"name": "li $t0, 10", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "li $t1, 20", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "add $t2, $t0, $t1", "type": "arith", "regs_read": 2, "regs_write": 1},
            {"name": "li $t3, 100", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "sw $t2, 0($t3)", "type": "store", "regs_read": 2, "regs_write": 0},
            {"name": "lw $t4, 0($t3)", "type": "load", "regs_read": 1, "regs_write": 1},
            {"name": "sub $t5, $t4, $t2", "type": "arith", "regs_read": 2, "regs_write": 1},
            {"name": "beq $t5, $zero, end", "type": "branch", "regs_read": 2, "regs_write": 0},
            {"name": "li $t6, 1", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "end:", "type": "label", "regs_read": 0, "regs_write": 0},
        ],
    }

    simulator = PerformanceSimulator(seed=42)
    result = simulator.run_benchmark(benchmark_instructions)
    simulator.print_benchmark_result(result)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("总结")
    print("=" * 80)
    print("""
  RISC-V:
  - Best for: Open-source hardware, education, embedded systems
  - Strengths: Simple, modular, extensible, no licensing fees
  - Weaknesses: Young ecosystem, less software support

  ARM:
  - Best for: Mobile, embedded, power-efficient computing
  - Strengths: Power efficiency, large ecosystem, mature toolchain
  - Weaknesses: Proprietary, licensing costs, complexity

  x86:
  - Best for: Desktop, server, high-performance computing
  - Strengths: Massive software ecosystem, backward compatibility
  - Weaknesses: Complex decode, power consumption, legacy baggage

  MIPS:
  - Best for: Education, embedded systems (historically)
  - Strengths: Simple, well-documented, educational value
  - Weaknesses: Declining adoption, limited modern support

  Key Takeaway (关键结论):
  - No single ISA is "best" for all use cases
  - Design trade-offs reflect different priorities
  - Modern implementations blur traditional RISC/CISC lines
""")

    print("=" * 80)


if __name__ == "__main__":
    run_comprehensive_comparison()
