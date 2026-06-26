"""
Register File Comparison Module
寄存器文件对比模块

This module compares the register files of different ISAs.
Key concepts:
- Number of general-purpose registers (GPRs): More registers reduce
  memory traffic by keeping more values in fast storage.
- Register naming and calling conventions: How registers are used for
  function arguments, return values, and callee-saved registers.
- Special registers: Program counter, status registers, etc.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional


class RegisterType(Enum):
    """Type of register in an ISA."""
    GENERAL_PURPOSE = "general_purpose"
    FLOATING_POINT = "floating_point"
    VECTOR = "vector"
    SPECIAL = "special"
    CONDITION_CODE = "condition_code"


@dataclass
class RegisterFile:
    """Represents the register file of an ISA."""
    name: str                        # ISA name
    gpr_count: int                   # Number of general-purpose registers
    gpr_width_bits: int              # Width of GPRs in bits
    fp_register_count: int           # Number of floating-point registers
    vector_register_count: int       # Number of vector/SIMD registers
    has_condition_codes: bool        # Whether the ISA has explicit condition codes
    has_program_counter: bool        # Whether there's an explicit PC register
    has_status_register: bool        # Whether there's a status/flags register
    register_names: List[str]        # Names of general-purpose registers
    caller_saved: List[str]          # Registers saved by caller in calling convention
    callee_saved: List[str]          # Registers saved by callee in calling convention


class RegisterFileComparator:
    """
    Compares register files across different ISAs.

    This module provides detailed comparison of register files, including:
    - Register count and width
    - Naming conventions
    - Calling convention roles
    - Special-purpose registers
    """

    # RISC-V register file definition
    RISC_V = RegisterFile(
        name="RISC-V",
        gpr_count=32,
        gpr_width_bits=64,
        fp_register_count=32,
        vector_register_count=32,
        has_condition_codes=False,
        has_program_counter=True,
        has_status_register=False,
        register_names=[
            "x0 (zero)", "x1 (ra)", "x2 (sp)", "x3 (gp)", "x4 (tp)",
            "x5-x7 (t0-t2)", "x8 (fp)", "x9 (s11)", "x10-x11 (a0-a1)",
            "x12-x17 (a2-a7)", "x18-x27 (s1-s10)", "x28-x31 (t3-t6)"
        ],
        caller_saved=["x1", "x5-x7", "x10-x11", "x28-x31"],
        callee_saved=["x8-x9", "x18-x27"],
    )

    # ARM AArch64 register file definition
    ARM = RegisterFile(
        name="ARM (AArch64)",
        gpr_count=31,
        gpr_width_bits=64,
        fp_register_count=32,
        vector_register_count=32,
        has_condition_codes=True,
        has_program_counter=True,
        has_status_register=True,
        register_names=[
            "x0-x30 (GPRs)", "x31 (SP)",
            "z0-z31 (SIMD/FP)", "PC", "NZCV (condition flags)"
        ],
        caller_saved=["x0-x7", "x16-x18", "v0-v7"],
        callee_saved=["x19-x29", "v8-v15"],
    )

    # x86-64 register file definition
    X86 = RegisterFile(
        name="x86-64",
        gpr_count=16,
        gpr_width_bits=64,
        fp_register_count=16,
        vector_register_count=32,
        has_condition_codes=True,
        has_program_counter=True,
        has_status_register=True,
        register_names=[
            "rax, rbx, rcx, rdx, rsi, rdi, rbp, rsp,",
            "r8-r15 (extended GPRs)",
            "xmm0-xmm15 (SSE/FP)",
            "zmm0-zmm31 (AVX-512)",
            "RIP (PC), RFLAGS (status)"
        ],
        caller_saved=["rax", "rcx", "rdx", "rsi", "rdi", "r8-r11"],
        callee_saved=["rbx", "rbp", "r12-r15"],
    )

    # MIPS register file definition
    MIPS = RegisterFile(
        name="MIPS",
        gpr_count=32,
        gpr_width_bits=32,
        fp_register_count=32,
        vector_register_count=0,
        has_condition_codes=False,
        has_program_counter=True,
        has_status_register=False,
        register_names=[
            "$0 (zero)", "$1 (at)", "$2-$3 (v0-v1)", "$4-$7 (a0-a7)",
            "$8-$15 (t0-t7)", "$16-$23 (s0-s7)", "$24-$25 (t8-t9)",
            "$28 (gp)", "$29 (sp)", "$30 (fp/s8)", "$31 (ra)"
        ],
        caller_saved=["$1", "$2-$3", "$4-$7", "$10-$15", "$24-$25"],
        callee_saved=["$8-$9", "$16-$23", "$29-$30"],
    )

    # Register file comparison table
    REGISTERS_TABLE = [
        {"ISA": "RISC-V", "GPRs": 32, "Width": "32/64-bit", "FP": 32, "Vector": 32, "Condition Codes": "No"},
        {"ISA": "ARM", "GPRs": 31, "Width": "32/64-bit", "FP": 32, "Vector": 32, "Condition Codes": "Yes"},
        {"ISA": "x86", "GPRs": 16, "Width": "16/32/64-bit", "FP": 16, "Vector": 32, "Condition Codes": "Yes"},
        {"ISA": "MIPS", "GPRs": 32, "Width": "32-bit", "FP": 32, "Vector": "0 (MIPS32)", "Condition Codes": "No"},
    ]

    def get_register_file(self, isa: str) -> RegisterFile:
        """
        Get the register file definition for a specific ISA.

        Args:
            isa: ISA name ("RISC-V", "ARM", "x86", "MIPS")

        Returns:
            RegisterFile object for the ISA
        """
        register_files = {
            "RISC-V": self.RISC_V,
            "ARM": self.ARM,
            "x86": self.X86,
            "MIPS": self.MIPS,
        }
        return register_files.get(isa)

    def compare_registers(self) -> List[Dict]:
        """
        Get the register file comparison table.

        Returns:
            List of dictionaries with register information
        """
        return self.REGISTERS_TABLE

    def get_calling_convention(self, isa: str) -> Dict[str, List[str]]:
        """
        Get the calling convention for a specific ISA.

        Args:
            isa: ISA name

        Returns:
            Dictionary with caller-saved and callee-saved registers
        """
        files = {
            "RISC-V": {"caller": self.RISC_V.caller_saved, "callee": self.RISC_V.callee_saved},
            "ARM": {"caller": self.ARM.caller_saved, "callee": self.ARM.callee_saved},
            "x86": {"caller": self.X86.caller_saved, "callee": self.X86.callee_saved},
            "MIPS": {"caller": self.MIPS.caller_saved, "callee": self.MIPS.callee_saved},
        }
        return files.get(isa, {"caller": [], "callee": []})

    def print_register_comparison(self):
        """Print a detailed register file comparison table."""
        print("=" * 90)
        print("REGISTER FILE COMPARISON")
        print("寄存器文件对比")
        print("=" * 90)

        headers = ["ISA", "GPRs", "Width", "FP Regs", "Vector", "Cond Codes"]
        print(f"{headers[0]:<10} {headers[1]:>6} {headers[2]:>12} {headers[3]:>10} "
              f"{headers[4]:>10} {headers[5]:>12}")
        print("-" * 80)

        for row in self.REGISTERS_TABLE:
            print(f"{row['ISA']:<10} {row['GPRs']:>6} {row['Width']:>12} "
                  f"{row['FP']:>10} {row['Vector']:>10} {row['Condition Codes']:>12}")

        print("\n" + "=" * 90)
        print("CALLING CONVENTION COMPARISON")
        print("调用约定对比")
        print("=" * 90)

        isas = ["RISC-V", "ARM", "x86", "MIPS"]
        for isa in isas:
            cc = self.get_calling_convention(isa)
            print(f"\n--- {isa} ---")
            print(f"  Caller-saved: {', '.join(cc['caller'])}")
            print(f"  Callee-saved: {', '.join(cc['callee'])}")

        print("\n" + "=" * 90)

    def analyze_register_pressure(self, isa: str, needed_registers: int) -> float:
        """
        Analyze register pressure for a given number of needed registers.

        Register pressure measures how many registers are needed relative
        to the available count. High pressure (>0.7) often requires
        register spilling to memory.

        Args:
            isa: ISA name
            needed_registers: Number of registers needed by the program

        Returns:
            Register pressure ratio (0.0 to 1.0+)
        """
        reg_file = self.get_register_file(isa)
        if reg_file:
            return needed_registers / reg_file.gpr_count
        return 1.0

    def get_register_spill_threshold(self, isa: str) -> int:
        """
        Get the threshold at which register spilling typically occurs.

        Args:
            isa: ISA name

        Returns:
            Number of registers that can be used before spilling
        """
        reg_file = self.get_register_file(isa)
        if reg_file:
            # Reserve some registers for special purposes
            reserved = 4  # Stack pointer, return address, etc.
            return reg_file.gpr_count - reserved
        return 0
