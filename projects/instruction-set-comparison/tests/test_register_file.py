"""
Tests for register file comparison module
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from register_file import RegisterFileComparator, RegisterType, RegisterFile


def test_get_register_file():
    """Test register file retrieval for each ISA."""
    comparator = RegisterFileComparator()
    for isa in ["RISC-V", "ARM", "x86", "MIPS"]:
        reg_file = comparator.get_register_file(isa)
        assert reg_file is not None
        assert reg_file.name == isa
        assert reg_file.gpr_count > 0


def test_register_counts():
    """Test register count values."""
    comparator = RegisterFileComparator()
    assert comparator.RISC_V.gpr_count == 32
    assert comparator.ARM.gpr_count == 31
    assert comparator.X86.gpr_count == 16
    assert comparator.MIPS.gpr_count == 32


def test_register_widths():
    """Test register width values."""
    comparator = RegisterFileComparator()
    assert comparator.RISC_V.gpr_width_bits == 64
    assert comparator.ARM.gpr_width_bits == 64
    assert comparator.X86.gpr_width_bits == 64
    assert comparator.MIPS.gpr_width_bits == 32


def test_compare_registers():
    """Test register comparison table."""
    comparator = RegisterFileComparator()
    table = comparator.compare_registers()
    assert len(table) == 4
    for row in table:
        assert "ISA" in row
        assert "GPRs" in row
        assert "Width" in row


def test_calling_convention():
    """Test calling convention retrieval."""
    comparator = RegisterFileComparator()
    for isa in ["RISC-V", "ARM", "x86", "MIPS"]:
        cc = comparator.get_calling_convention(isa)
        assert "caller" in cc
        assert "callee" in cc
        assert len(cc["caller"]) > 0
        assert len(cc["callee"]) > 0


def test_register_spill_threshold():
    """Test register spill threshold calculation."""
    comparator = RegisterFileComparator()
    for isa in ["RISC-V", "ARM", "x86", "MIPS"]:
        threshold = comparator.get_register_spill_threshold(isa)
        assert threshold > 0
        assert threshold < comparator.get_register_file(isa).gpr_count


def test_register_pressure():
    """Test register pressure analysis."""
    comparator = RegisterFileComparator()
    pressure = comparator.analyze_register_pressure("RISC-V", 16)
    assert pressure < 1.0
    pressure = comparator.analyze_register_pressure("RISC-V", 40)
    assert pressure > 1.0
    pressure_riscv = comparator.analyze_register_pressure("RISC-V", 20)
    pressure_x86 = comparator.analyze_register_pressure("x86", 20)
    assert pressure_x86 > pressure_riscv


def test_condition_codes():
    """Test condition code support."""
    comparator = RegisterFileComparator()
    assert comparator.RISC_V.has_condition_codes == False
    assert comparator.ARM.has_condition_codes == True
    assert comparator.X86.has_condition_codes == True
    assert comparator.MIPS.has_condition_codes == False


def test_fp_register_counts():
    """Test floating-point register counts."""
    comparator = RegisterFileComparator()
    assert comparator.RISC_V.fp_register_count == 32
    assert comparator.ARM.fp_register_count == 32
    assert comparator.X86.fp_register_count == 16
    assert comparator.MIPS.fp_register_count == 32


def test_vector_register_counts():
    """Test vector register counts."""
    comparator = RegisterFileComparator()
    assert comparator.RISC_V.vector_register_count == 32
    assert comparator.ARM.vector_register_count == 32
    assert comparator.X86.vector_register_count == 32
    assert comparator.MIPS.vector_register_count == 0


def test_enum_values():
    """Test enum has correct values."""
    assert RegisterType.GENERAL_PURPOSE.value == "general_purpose"
    assert RegisterType.FLOATING_POINT.value == "floating_point"
    assert RegisterType.VECTOR.value == "vector"
    assert RegisterType.SPECIAL.value == "special"
    assert RegisterType.CONDITION_CODE.value == "condition_code"


def test_create_register_file():
    """Test creating a register file."""
    reg_file = RegisterFile(
        name="TestISA", gpr_count=16, gpr_width_bits=32,
        fp_register_count=8, vector_register_count=0,
        has_condition_codes=False, has_program_counter=True,
        has_status_register=False, register_names=["r0", "r1"],
        caller_saved=["r0"], callee_saved=["r1"],
    )
    assert reg_file.name == "TestISA"
    assert reg_file.gpr_count == 16
    assert reg_file.gpr_width_bits == 32
    assert len(reg_file.register_names) == 2


if __name__ == "__main__":
    import traceback
    tests = [
        test_get_register_file, test_register_counts,
        test_register_widths, test_compare_registers,
        test_calling_convention, test_register_spill_threshold,
        test_register_pressure, test_condition_codes,
        test_fp_register_counts, test_vector_register_counts,
        test_enum_values, test_create_register_file,
    ]
    total = len(tests)
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print(f"  PASS: {test.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL: {test.__name__}")
            traceback.print_exc()
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print(f"{'='*50}")
