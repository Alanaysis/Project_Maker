"""
Addressing Mode Comparison Module
寻址方式对比模块

This module compares addressing modes across different ISAs.
Key concepts:
- Immediate: The value is encoded directly in the instruction.
- Register: The value is in a register.
- Direct/Absolute: The address is encoded directly.
- Register Indirect: The register contains the address.
- Displacement/Base+Offset: A register plus a constant offset.
- PC-relative: Offset from the program counter (used in branches).
- Scaled index: Base + index*scale (common in x86).
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional


class AddressingModeType(Enum):
    """Classification of addressing modes."""
    IMMEDIATE = "immediate"
    REGISTER = "register"
    DIRECT = "direct"
    REGISTER_INDIRECT = "register_indirect"
    BASE_INDIRECT = "base_indirect"
    PC_RELATIVE = "pc_relative"
    SCALED_INDEX = "scaled_index"
    STACK = "stack"


@dataclass
class AddressingMode:
    """Represents an addressing mode supported by an ISA."""
    name: str
    mode_type: AddressingModeType
    description: str
    example: str  # Assembly example
    encoded_size: int  # Average encoded size in bytes


class AddressingModeComparator:
    """
    Compares addressing modes across different ISAs.

    This module analyzes how each ISA handles memory addressing,
    which significantly impacts:
    - Instruction complexity
    - Memory access patterns
    - Code density
    - Compiler optimization opportunities
    """

    # RISC-V addressing modes
    RISC_V_MODES = [
        AddressingMode(
            name="Immediate",
            mode_type=AddressingModeType.IMMEDIATE,
            description="Constant value encoded in instruction",
            example="li x1, 0x1234",
            encoded_size=4,
        ),
        AddressingMode(
            name="Register",
            mode_type=AddressingModeType.REGISTER,
            description="Value from a register",
            example="add x1, x2, x3",
            encoded_size=4,
        ),
        AddressingMode(
            name="Base + Displacement",
            mode_type=AddressingModeType.BASE_INDIRECT,
            description="Memory access: base register + signed offset",
            example="lw x1, 16(x2)",
            encoded_size=4,
        ),
        AddressingMode(
            name="PC-relative",
            mode_type=AddressingModeType.PC_RELATIVE,
            description="Offset from current PC (branches)",
            example="beq x1, x2, label",
            encoded_size=4,
        ),
        AddressingMode(
            name="Pseudo-immediate (LUI/AUIPC)",
            mode_type=AddressingModeType.IMMEDIATE,
            description="Load upper immediate + add upper immediate",
            example="auipc x1, 0x12345",
            encoded_size=8,  # Two instructions needed for 64-bit
        ),
    ]

    # ARM AArch64 addressing modes
    ARM_MODES = [
        AddressingMode(
            name="Immediate",
            mode_type=AddressingModeType.IMMEDIATE,
            description="Constant value in instruction",
            example="mov x1, #0x1234",
            encoded_size=4,
        ),
        AddressingMode(
            name="Register",
            mode_type=AddressingModeType.REGISTER,
            description="Value from a register",
            example="add x1, x2, x3",
            encoded_size=4,
        ),
        AddressingMode(
            name="Base + Offset",
            mode_type=AddressingModeType.BASE_INDIRECT,
            description="Memory access: base + 12-bit offset",
            example="ldr x1, [x2, #16]",
            encoded_size=4,
        ),
        AddressingMode(
            name="Base + Register offset",
            mode_type=AddressingModeType.BASE_INDIRECT,
            description="Memory access: base + register offset",
            example="ldr x1, [x2, x3]",
            encoded_size=4,
        ),
        AddressingMode(
            name="PC-relative",
            mode_type=AddressingModeType.PC_RELATIVE,
            description="Address relative to PC",
            example="adr x1, label",
            encoded_size=4,
        ),
        AddressingMode(
            name="Pre-indexed",
            mode_type=AddressingModeType.BASE_INDIRECT,
            description="Base updated after access",
            example="ldr x1, [x2], #8",
            encoded_size=4,
        ),
        AddressingMode(
            name="Post-indexed",
            mode_type=AddressingModeType.BASE_INDIRECT,
            description="Base updated before access",
            example="ldr x1, [x2, #8]!",
            encoded_size=4,
        ),
    ]

    # x86-64 addressing modes
    X86_MODES = [
        AddressingMode(
            name="Immediate",
            mode_type=AddressingModeType.IMMEDIATE,
            description="Constant value in instruction",
            example="mov eax, 0x1234",
            encoded_size=5,
        ),
        AddressingMode(
            name="Register",
            mode_type=AddressingModeType.REGISTER,
            description="Value from a register",
            example="add eax, ebx",
            encoded_size=2,
        ),
        AddressingMode(
            name="Direct (absolute)",
            mode_type=AddressingModeType.DIRECT,
            description="Absolute memory address",
            example="mov eax, [0x12345678]",
            encoded_size=6,
        ),
        AddressingMode(
            name="Base + Displacement",
            mode_type=AddressingModeType.BASE_INDIRECT,
            description="Base register + 8/32-bit displacement",
            example="mov eax, [rbx + 16]",
            encoded_size=3,
        ),
        AddressingMode(
            name="Base + Index + Displacement",
            mode_type=AddressingModeType.SCALED_INDEX,
            description="Base + index*scale + displacement",
            example="mov eax, [rbx + rcx*4 + 16]",
            encoded_size=6,
        ),
        AddressingMode(
            name="PC-relative",
            mode_type=AddressingModeType.PC_RELATIVE,
            description="Address relative to RIP",
            example="mov rax, [rip + label]",
            encoded_size=5,
        ),
        AddressingMode(
            name="Stack (push/pop)",
            mode_type=AddressingModeType.STACK,
            description="Implicit stack operations",
            example="push rax / pop rax",
            encoded_size=1,
        ),
    ]

    # MIPS addressing modes
    MIPS_MODES = [
        AddressingMode(
            name="Immediate",
            mode_type=AddressingModeType.IMMEDIATE,
            description="16-bit signed constant",
            example="li $t0, 0x1234",
            encoded_size=4,
        ),
        AddressingMode(
            name="Register",
            mode_type=AddressingModeType.REGISTER,
            description="Value from a register",
            example="add $t0, $t1, $t2",
            encoded_size=4,
        ),
        AddressingMode(
            name="Base + Displacement",
            mode_type=AddressingModeType.BASE_INDIRECT,
            description="Memory access: base + 16-bit signed offset",
            example="lw $t0, 16($t1)",
            encoded_size=4,
        ),
        AddressingMode(
            name="PC-relative",
            mode_type=AddressingModeType.PC_RELATIVE,
            description="Offset from PC (branches)",
            example="beq $t0, $t1, label",
            encoded_size=4,
        ),
        AddressingMode(
            name="J-type (jump)",
            mode_type=AddressingModeType.DIRECT,
            description="26-bit target address",
            example="j label",
            encoded_size=4,
        ),
    ]

    # Comparison summary
    ADDRESSING_MODES_TABLE = [
        {"ISA": "RISC-V", "Modes": "5", "Complex": "Low", "MaxDisplacement": "12-bit"},
        {"ISA": "ARM", "Modes": "7", "Complex": "Medium", "MaxDisplacement": "12-bit"},
        {"ISA": "x86", "Modes": "7", "Complex": "High", "MaxDisplacement": "32-bit"},
        {"ISA": "MIPS", "Modes": "5", "Complex": "Low", "MaxDisplacement": "16-bit"},
    ]

    def get_addressing_modes(self, isa: str) -> List[AddressingMode]:
        """
        Get the addressing modes for a specific ISA.

        Args:
            isa: ISA name ("RISC-V", "ARM", "x86", "MIPS")

        Returns:
            List of AddressingMode objects
        """
        modes_map = {
            "RISC-V": self.RISC_V_MODES,
            "ARM": self.ARM_MODES,
            "x86": self.X86_MODES,
            "MIPS": self.MIPS_MODES,
        }
        return modes_map.get(isa, [])

    def get_complexity_rating(self, isa: str) -> str:
        """
        Get the addressing mode complexity rating for an ISA.

        Args:
            isa: ISA name

        Returns:
            Complexity rating string ("Low", "Medium", "High")
        """
        complexity = {
            "RISC-V": "Low",
            "ARM": "Medium",
            "x86": "High",
            "MIPS": "Low",
        }
        return complexity.get(isa, "Unknown")

    def compare_addressing_modes(self) -> List[Dict]:
        """
        Get the addressing mode comparison table.

        Returns:
            List of dictionaries with addressing mode information
        """
        return self.ADDRESSING_MODES_TABLE

    def print_addressing_mode_comparison(self):
        """Print a detailed addressing mode comparison."""
        print("=" * 100)
        print("ADDRESSING MODE COMPARISON")
        print("寻址方式对比")
        print("=" * 100)

        isas = ["RISC-V", "ARM", "x86", "MIPS"]
        for isa in isas:
            modes = self.get_addressing_modes(isa)
            complexity = self.get_complexity_rating(isa)
            print(f"\n--- {isa} (Complexity: {complexity}) ---")
            print(f"  {'Mode':<30} {'Type':<25} {'Example':<30}")
            print(f"  {'-'*28} {'-'*23} {'-'*28}")
            for mode in modes:
                print(f"  {mode.name:<30} {mode.mode_type.value:<25} {mode.example:<30}")

        print("\n" + "=" * 100)
        print("COMPARISON SUMMARY")
        print("对比总结")
        print("=" * 100)
        print(f"{'ISA':<10} {'Modes':>8} {'Complexity':>14} {'Max Disp':>14}")
        print("-" * 55)

        for row in self.ADDRESSING_MODES_TABLE:
            print(f"{row['ISA']:<10} {row['Modes']:>8} {row['Complex']:>14} "
                  f"{row['MaxDisplacement']:>14}")

        print("=" * 100)

    def get_addressing_mode_count(self, isa: str) -> int:
        """
        Get the number of addressing modes for an ISA.

        Args:
            isa: ISA name

        Returns:
            Number of addressing modes
        """
        return len(self.get_addressing_modes(isa))

    def is_scaled_index_supported(self, isa: str) -> bool:
        """
        Check if scaled index addressing is supported.

        Args:
            isa: ISA name

        Returns:
            True if scaled index addressing is supported
        """
        modes = self.get_addressing_modes(isa)
        return any(m.mode_type == AddressingModeType.SCALED_INDEX for m in modes)
