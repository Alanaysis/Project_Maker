"""
Instruction Encoding Comparison Module
指令编码对比模块

This module compares instruction encoding between different ISAs.
Key concepts:
- Fixed-length encoding (RISC-V, MIPS): All instructions are the same size (32 bits).
  Benefits: Simple decode, single-cycle fetch, predictable memory access.
  Trade-off: Less flexible for complex instructions.

- Variable-length encoding (x86): Instructions range from 1 to 15 bytes.
  Benefits: Code density (complex instructions can be compact), backward compatibility.
  Trade-off: Complex decode, multi-cycle fetch, unpredictable execution.

- ARM (thumb/AArch64): Hybrid approach with fixed-length AArch64 and optional
  Thumb-2 variable-length encoding for code density.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional


class EncodingType(Enum):
    """Instruction encoding type classification."""
    FIXED_LENGTH = "fixed_length"
    VARIABLE_LENGTH = "variable_length"
    HYBRID = "hybrid"


@dataclass
class InstructionFormat:
    """Represents an instruction format definition for a specific ISA."""
    name: str              # Format name (e.g., "R-type", "I-type", "B-type")
    total_bits: int        # Total instruction width in bits
    fields: List[Dict[str, object]]  # List of {name: str, bits: int}
    encoding_type: EncodingType


@dataclass
class EncodingComparison:
    """Stores comparison data between two ISAs for a specific operation."""
    operation: str                      # e.g., "ADD", "LOAD", "BRANCH"
    risc_v_format: InstructionFormat
    arm_format: InstructionFormat
    x86_encoding: str                   # x86 uses different encoding notation
    mips_format: InstructionFormat
    code_size_riscv: int                # Code size in bytes for this operation
    code_size_arm: int
    code_size_x86: int
    code_size_mips: int


class InstructionEncoder:
    """
    Simulates instruction encoding for different ISAs.

    This class demonstrates how instructions are encoded in each architecture,
    showing the differences between fixed-length and variable-length encoding.
    """

    # Standard RISC-V instruction formats (all 32-bit)
    RISC_V_FORMATS = {
        "R-type": InstructionFormat(
            name="R-type",
            total_bits=32,
            encoding_type=EncodingType.FIXED_LENGTH,
            fields=[
                {"name": "opcode", "bits": 7, "offset": 0},
                {"name": "rd", "bits": 5, "offset": 7},
                {"name": "funct3", "bits": 3, "offset": 12},
                {"name": "rs1", "bits": 5, "offset": 15},
                {"name": "rs2", "bits": 5, "offset": 20},
                {"name": "funct7", "bits": 7, "offset": 25},
            ]
        ),
        "I-type": InstructionFormat(
            name="I-type",
            total_bits=32,
            encoding_type=EncodingType.FIXED_LENGTH,
            fields=[
                {"name": "opcode", "bits": 7, "offset": 0},
                {"name": "rd", "bits": 5, "offset": 7},
                {"name": "imm", "bits": 12, "offset": 12},
                {"name": "funct3", "bits": 3, "offset": 24},
                {"name": "rs1", "bits": 5, "offset": 27},
            ]
        ),
        "S-type": InstructionFormat(
            name="S-type",
            total_bits=32,
            encoding_type=EncodingType.FIXED_LENGTH,
            fields=[
                {"name": "opcode", "bits": 7, "offset": 0},
                {"name": "imm_lo", "bits": 5, "offset": 7},
                {"name": "funct3", "bits": 3, "offset": 12},
                {"name": "rs1", "bits": 5, "offset": 15},
                {"name": "rs2", "bits": 5, "offset": 20},
                {"name": "imm_hi", "bits": 7, "offset": 25},
            ]
        ),
        "B-type": InstructionFormat(
            name="B-type",
            total_bits=32,
            encoding_type=EncodingType.FIXED_LENGTH,
            fields=[
                {"name": "opcode", "bits": 7, "offset": 0},
                {"name": "imm_11|1|10:5", "bits": 6, "offset": 7},
                {"name": "funct3", "bits": 3, "offset": 12},
                {"name": "rs1", "bits": 5, "offset": 15},
                {"name": "rs2", "bits": 5, "offset": 20},
                {"name": "imm_4|11|7:6", "bits": 6, "offset": 25},
            ]
        ),
        "U-type": InstructionFormat(
            name="U-type",
            total_bits=32,
            encoding_type=EncodingType.FIXED_LENGTH,
            fields=[
                {"name": "opcode", "bits": 7, "offset": 0},
                {"name": "rd", "bits": 5, "offset": 7},
                {"name": "imm", "bits": 20, "offset": 12},
            ]
        ),
        "J-type": InstructionFormat(
            name="J-type",
            total_bits=32,
            encoding_type=EncodingType.FIXED_LENGTH,
            fields=[
                {"name": "opcode", "bits": 7, "offset": 0},
                {"name": "rd", "bits": 5, "offset": 7},
                {"name": "imm_20|10:1|11|19:12", "bits": 20, "offset": 12},
            ]
        ),
    }

    # MIPS instruction formats (all 32-bit)
    MIPS_FORMATS = {
        "R-type": InstructionFormat(
            name="R-type",
            total_bits=32,
            encoding_type=EncodingType.FIXED_LENGTH,
            fields=[
                {"name": "opcode", "bits": 6, "offset": 0},
                {"name": "rs", "bits": 5, "offset": 6},
                {"name": "rt", "bits": 5, "offset": 11},
                {"name": "rd", "bits": 5, "offset": 16},
                {"name": "shamt", "bits": 5, "offset": 21},
                {"name": "funct", "bits": 6, "offset": 26},
            ]
        ),
        "I-type": InstructionFormat(
            name="I-type",
            total_bits=32,
            encoding_type=EncodingType.FIXED_LENGTH,
            fields=[
                {"name": "opcode", "bits": 6, "offset": 0},
                {"name": "rt", "bits": 5, "offset": 6},
                {"name": "rs", "bits": 5, "offset": 11},
                {"name": "immediate", "bits": 16, "offset": 16},
            ]
        ),
        "J-type": InstructionFormat(
            name="J-type",
            total_bits=32,
            encoding_type=EncodingType.FIXED_LENGTH,
            fields=[
                {"name": "opcode", "bits": 6, "offset": 0},
                {"name": "target", "bits": 26, "offset": 6},
            ]
        ),
    }

    # ARM AArch64 instruction formats (all 32-bit)
    ARM_FORMATS = {
        "R-type": InstructionFormat(
            name="R-type",
            total_bits=32,
            encoding_type=EncodingType.FIXED_LENGTH,
            fields=[
                {"name": "opcode", "bits": 5, "offset": 0},
                {"name": "Q", "bits": 1, "offset": 5},
                {"name": "S", "bits": 1, "offset": 6},
                {"name": "R", "bits": 1, "offset": 7},
                {"name": "P", "bits": 1, "offset": 8},
                {"name": "op_0", "bits": 1, "offset": 9},
                {"name": "crc", "bits": 1, "offset": 10},
                {"name": "sf", "bits": 1, "offset": 11},
                {"name": "op_1", "bits": 4, "offset": 12},
                {"name": "Rm", "bits": 5, "offset": 16},
                {"name": "shift", "bits": 2, "offset": 22},
                {"name": "N", "bits": 1, "offset": 24},
                {"name": "imm12", "bits": 12, "offset": 25},
                {"name": "Rn", "bits": 5, "offset": 0},
                {"name": "Rd", "bits": 5, "offset": 0},
            ]
        ),
        "load/store": InstructionFormat(
            name="load/store",
            total_bits=32,
            encoding_type=EncodingType.FIXED_LENGTH,
            fields=[
                {"name": "opcode", "bits": 5, "offset": 0},
                {"name": "V", "bits": 1, "offset": 5},
                {"name": "size", "bits": 2, "offset": 6},
                {"name": "op", "bits": 1, "offset": 8},
                {"name": "u", "bits": 1, "offset": 9},
                {"name": "p", "bits": 1, "offset": 10},
                {"name": "Wn", "bits": 5, "offset": 11},
                {"name": "Rt", "bits": 5, "offset": 16},
                {"name": "Rt2", "bits": 5, "offset": 21},
                {"name": "imm7", "bits": 7, "offset": 26},
            ]
        ),
        "branch": InstructionFormat(
            name="branch",
            total_bits=32,
            encoding_type=EncodingType.FIXED_LENGTH,
            fields=[
                {"name": "opcode", "bits": 4, "offset": 0},
                {"name": "L", "bits": 1, "offset": 4},
                {"name": "imm19", "bits": 19, "offset": 5},
                {"name": "Op", "bits": 1, "offset": 24},
                {"name": "Rn", "bits": 5, "offset": 26},
            ]
        ),
    }

    def __init__(self):
        """Initialize the encoder with default instruction sets."""
        self.instructions: Dict[str, List[Dict]] = {}
        self._populate_common_instructions()

    def _populate_common_instructions(self):
        """Populate common instructions for each ISA."""
        # RISC-V common instructions
        self.instructions["RISC-V"] = [
            {"name": "add rd, rs1, rs2", "format": "R-type", "bytes": 4, "hex": "0x00000033"},
            {"name": "lw rd, offset(rs1)", "format": "I-type", "bytes": 4, "hex": "0x00000023"},
            {"name": "sw rs2, offset(rs1)", "format": "S-type", "bytes": 4, "hex": "0x00000023"},
            {"name": "beq rs1, rs2, label", "format": "B-type", "bytes": 4, "hex": "0x00000063"},
            {"name": "lui rd, imm", "format": "U-type", "bytes": 4, "hex": "0x00000037"},
            {"name": "jal rd, label", "format": "J-type", "bytes": 4, "hex": "0x0000006f"},
            {"name": "addi rd, rs1, imm", "format": "I-type", "bytes": 4, "hex": "0x00000013"},
            {"name": "lb rd, offset(rs1)", "format": "I-type", "bytes": 4, "hex": "0x00000003"},
            {"name": "slli rd, rs1, imm", "format": "I-type", "bytes": 4, "hex": "0x00000011"},
            {"name": "ld rd, offset(rs1)", "format": "I-type", "bytes": 4, "hex": "0x00000003"},
        ]

        # MIPS common instructions
        self.instructions["MIPS"] = [
            {"name": "add rd, rs, rt", "format": "R-type", "bytes": 4, "hex": "0x00000021"},
            {"name": "lw rt, offset(rs)", "format": "I-type", "bytes": 4, "hex": "0x8C000000"},
            {"name": "sw rt, offset(rs)", "format": "I-type", "bytes": 4, "hex": "0xAC000000"},
            {"name": "beq rs, rt, label", "format": "I-type", "bytes": 4, "hex": "0x10000000"},
            {"name": "j target", "format": "J-type", "bytes": 4, "hex": "0x08000000"},
            {"name": "addi rt, rs, imm", "format": "I-type", "bytes": 4, "hex": "0x20000000"},
            {"name": "sll rd, rt, shamt", "format": "R-type", "bytes": 4, "hex": "0x00000000"},
            {"name": "lb rt, offset(rs)", "format": "I-type", "bytes": 4, "hex": "0x8C000000"},
            {"name": "sd rt, offset(rs)", "format": "I-type", "bytes": 4, "hex": "0xAC000000"},
            {"name": "or rd, rs, rt", "format": "R-type", "bytes": 4, "hex": "0x00000025"},
        ]

        # ARM AArch64 common instructions
        self.instructions["ARM"] = [
            {"name": "add rd, rn, rm", "format": "R-type", "bytes": 4, "hex": "0x0B00001F"},
            {"name": "ldr rt, [rn, imm]", "format": "load/store", "bytes": 4, "hex": "0xF9400000"},
            {"name": "str rt, [rn, imm]", "format": "load/store", "bytes": 4, "hex": "0xF9000000"},
            {"name": "b label", "format": "branch", "bytes": 4, "hex": "0x14000000"},
            {"name": "add rd, rn, #imm", "format": "R-type", "bytes": 4, "hex": "0x11000000"},
            {"name": "sub rd, rn, #imm", "format": "R-type", "bytes": 4, "hex": "0xD1000000"},
            {"name": "ldr rt, [xn]", "format": "load/store", "bytes": 4, "hex": "0xF9400000"},
            {"name": "and rd, rn, #imm", "format": "R-type", "bytes": 4, "hex": "0x82000000"},
            {"name": "eor rd, rn, rm", "format": "R-type", "bytes": 4, "hex": "0xCA00001F"},
            {"name": "cbz rn, label", "format": "branch", "bytes": 4, "hex": "0x34000000"},
        ]

        # x86-64 common instructions (variable length)
        self.instructions["x86"] = [
            {"name": "add r64, r/m64", "format": "ModR/M", "bytes": 2, "hex": "0x03"},
            {"name": "mov r64, r/m64", "format": "ModR/M", "bytes": 2, "hex": "0x89"},
            {"name": "mov r/m64, r64", "format": "ModR/M", "bytes": 2, "hex": "0x8B"},
            {"name": "jmp rel32", "format": "Ev", "bytes": 5, "hex": "0xE9"},
            {"name": "cmp r64, r/m64", "format": "ModR/M", "bytes": 2, "hex": "0x39"},
            {"name": "push r64", "format": "Ev", "bytes": 1, "hex": "0x50"},
            {"name": "pop r64", "format": "Ev", "bytes": 1, "hex": "0x58"},
            {"name": "nop", "format": "1-byte", "bytes": 1, "hex": "0x90"},
            {"name": "lea r64, [disp32]", "format": "ModR/M", "bytes": 4, "hex": "0x8D"},
            {"name": "mov r64, imm64", "format": "7-byte", "bytes": 7, "hex": "0xB8"},
        ]

    def get_instruction_formats(self, isa: str) -> Dict[str, InstructionFormat]:
        """
        Get the instruction formats for a specific ISA.

        Args:
            isa: ISA name ("RISC-V", "MIPS", "ARM", "x86")

        Returns:
            Dictionary mapping format names to InstructionFormat objects
        """
        formats_map = {
            "RISC-V": self.RISC_V_FORMATS,
            "MIPS": self.MIPS_FORMATS,
            "ARM": self.ARM_FORMATS,
            "x86": {},  # x86 doesn't have named formats in the same way
        }
        return formats_map.get(isa, {})

    def get_encoding_type(self, isa: str) -> EncodingType:
        """
        Get the primary encoding type for an ISA.

        Args:
            isa: ISA name

        Returns:
            EncodingType enum value
        """
        encoding_types = {
            "RISC-V": EncodingType.FIXED_LENGTH,
            "MIPS": EncodingType.FIXED_LENGTH,
            "ARM": EncodingType.HYBRID,  # AArch64 is fixed, Thumb-2 is variable
            "x86": EncodingType.VARIABLE_LENGTH,
        }
        return encoding_types.get(isa, EncodingType.FIXED_LENGTH)

    def get_instructions(self, isa: str) -> List[Dict]:
        """
        Get common instructions for a specific ISA.

        Args:
            isa: ISA name

        Returns:
            List of instruction dictionaries
        """
        return self.instructions.get(isa, [])

    def compare_code_sizes(self) -> List[EncodingComparison]:
        """
        Compare code sizes across ISAs for common operations.

        Returns:
            List of EncodingComparison objects
        """
        comparisons = []

        # Compare ADD operation
        comparisons.append(EncodingComparison(
            operation="ADD",
            risc_v_format=self.RISC_V_FORMATS["R-type"],
            arm_format=self.ARM_FORMATS["R-type"],
            x86_encoding="2 bytes (ModR/M) - variable depending on operands",
            mips_format=self.MIPS_FORMATS["R-type"],
            code_size_riscv=4,
            code_size_arm=4,
            code_size_x86=2,
            code_size_mips=4,
        ))

        # Compare LOAD operation
        comparisons.append(EncodingComparison(
            operation="LOAD",
            risc_v_format=self.RISC_V_FORMATS["I-type"],
            arm_format=self.ARM_FORMATS["load/store"],
            x86_encoding="3-7 bytes depending on addressing mode",
            mips_format=self.MIPS_FORMATS["I-type"],
            code_size_riscv=4,
            code_size_arm=4,
            code_size_x86=5,
            code_size_mips=4,
        ))

        # Compare STORE operation
        comparisons.append(EncodingComparison(
            operation="STORE",
            risc_v_format=self.RISC_V_FORMATS["S-type"],
            arm_format=self.ARM_FORMATS["load/store"],
            x86_encoding="3-7 bytes depending on addressing mode",
            mips_format=self.MIPS_FORMATS["I-type"],
            code_size_riscv=4,
            code_size_arm=4,
            code_size_x86=5,
            code_size_mips=4,
        ))

        # Compare BRANCH operation
        comparisons.append(EncodingComparison(
            operation="BRANCH",
            risc_v_format=self.RISC_V_FORMATS["B-type"],
            arm_format=self.ARM_FORMATS["branch"],
            x86_encoding="2-5 bytes (short jump to near jump)",
            mips_format=self.MIPS_FORMATS["I-type"],
            code_size_riscv=4,
            code_size_arm=4,
            code_size_x86=3,
            code_size_mips=4,
        ))

        # Compare JUMP operation
        comparisons.append(EncodingComparison(
            operation="JUMP",
            risc_v_format=self.RISC_V_FORMATS["J-type"],
            arm_format=self.ARM_FORMATS["branch"],
            x86_encoding="2-6 bytes (near/far/jmp)",
            mips_format=self.MIPS_FORMATS["J-type"],
            code_size_riscv=4,
            code_size_arm=4,
            code_size_x86=5,
            code_size_mips=4,
        ))

        return comparisons

    def print_encoding_comparison(self):
        """Print a detailed encoding comparison table."""
        print("=" * 80)
        print("INSTRUCTION ENCODING COMPARISON")
        print("指令编码对比")
        print("=" * 80)

        isas = ["RISC-V", "MIPS", "ARM", "x86"]
        for isa in isas:
            enc_type = self.get_encoding_type(isa)
            print(f"\n--- {isa} ({enc_type.value}) ---")
            formats = self.get_instruction_formats(isa)
            for fmt_name, fmt in formats.items():
                print(f"  Format: {fmt_name}")
                print(f"    Total bits: {fmt.total_bits}")
                print(f"    Fields:")
                for field in fmt.fields:
                    print(f"      - {field['name']}: {field['bits']} bits")

        print("\n" + "=" * 80)
        print("CODE SIZE COMPARISON (bytes per instruction)")
        print("代码大小对比 (每条指令的字节数)")
        print("=" * 80)
        print(f"{'Operation':<12} {'RISC-V':>8} {'ARM':>8} {'x86':>8} {'MIPS':>8}")
        print("-" * 50)

        for comp in self.compare_code_sizes():
            print(f"{comp.operation:<12} {comp.code_size_riscv:>8} "
                  f"{comp.code_size_arm:>8} {comp.code_size_x86:>8} {comp.code_size_mips:>8}")

        print("=" * 80)


class CodeDensityAnalyzer:
    """
    Analyzes code density across different ISAs.

    Code density is the number of instructions needed to implement a given
    program. Higher code density means more instructions fit in the same
    amount of memory (cache, ROM, flash).

    Key insight: Variable-length ISAs (x86) can achieve better code density
    for simple operations, but fixed-length ISAs (RISC-V, MIPS) have more
    predictable performance.
    """

    def __init__(self):
        """Initialize the code density analyzer."""
        # Average bytes per instruction for common code patterns
        self.avg_bytes_per_instruction = {
            "RISC-V": 4.0,   # Always 32-bit
            "MIPS": 4.0,     # Always 32-bit
            "ARM": 3.6,      # Mix of 16-bit Thumb and 32-bit AArch64
            "x86": 2.7,      # Variable length, often compact for simple ops
        }

    def analyze_code_density(self, instruction_sequence: Dict[str, int]) -> Dict[str, float]:
        """
        Analyze the total code size for a given instruction mix.

        Args:
            instruction_sequence: Dictionary mapping instruction names to counts

        Returns:
            Dictionary mapping ISA to total code size in bytes
        """
        code_sizes = {}
        for isa in self.avg_bytes_per_instruction:
            total = 0
            for instr, count in instruction_sequence.items():
                # Each ISA handles instructions differently
                # This is a simplified model
                if isa == "x86":
                    # x86 can encode many operations in fewer bytes
                    if "load" in instr.lower() or "store" in instr.lower():
                        total += count * 4  # Typical load/store
                    elif "add" in instr.lower() or "sub" in instr.lower():
                        total += count * 2  # Simple arithmetic is compact
                    elif "branch" in instr.lower() or "jump" in instr.lower():
                        total += count * 3  # Typical branch
                    else:
                        total += count * 2.5
                else:
                    # Fixed-length ISAs always use 4 bytes per instruction
                    total += count * 4
            code_sizes[isa] = total
        return code_sizes

    def get_density_ratio(self, isa1: str, isa2: str) -> float:
        """
        Get the code density ratio between two ISAs.

        A ratio > 1 means isa1 has better code density (fewer bytes per instruction).

        Args:
            isa1: First ISA name
            isa2: Second ISA name

        Returns:
            Density ratio (isa1 density / isa2 density)
        """
        ratio = self.avg_bytes_per_instruction[isa2] / self.avg_bytes_per_instruction[isa1]
        return ratio
