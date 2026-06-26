"""
Tests for addressing modes comparison module
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from addressing_modes import (
    AddressingModeComparator,
    AddressingModeType,
    AddressingMode,
)


def test_get_addressing_modes():
    """Test addressing mode retrieval for each ISA."""
    comparator = AddressingModeComparator()
    for isa in ["RISC-V", "ARM", "x86", "MIPS"]:
        modes = comparator.get_addressing_modes(isa)
        assert len(modes) > 0
        for mode in modes:
            assert isinstance(mode, AddressingMode)
            assert mode.name != ""
            assert mode.encoded_size > 0


def test_risc_v_modes():
    """Test RISC-V addressing modes."""
    comparator = AddressingModeComparator()
    modes = comparator.get_addressing_modes("RISC-V")
    assert len(modes) == 5
    mode_names = [m.name for m in modes]
    assert "Immediate" in mode_names
    assert "Register" in mode_names
    assert "Base + Displacement" in mode_names


def test_arm_modes():
    """Test ARM addressing modes."""
    comparator = AddressingModeComparator()
    modes = comparator.get_addressing_modes("ARM")
    assert len(modes) == 7
    mode_names = [m.name for m in modes]
    assert "Pre-indexed" in mode_names
    assert "Post-indexed" in mode_names


def test_x86_modes():
    """Test x86 addressing modes."""
    comparator = AddressingModeComparator()
    modes = comparator.get_addressing_modes("x86")
    assert len(modes) == 7
    mode_names = [m.name for m in modes]
    assert "Base + Index + Displacement" in mode_names
    assert "Stack (push/pop)" in mode_names


def test_mips_modes():
    """Test MIPS addressing modes."""
    comparator = AddressingModeComparator()
    modes = comparator.get_addressing_modes("MIPS")
    assert len(modes) == 5
    mode_names = [m.name for m in modes]
    assert "J-type (jump)" in mode_names


def test_complexity_rating():
    """Test complexity rating for each ISA."""
    comparator = AddressingModeComparator()
    assert comparator.get_complexity_rating("RISC-V") == "Low"
    assert comparator.get_complexity_rating("MIPS") == "Low"
    assert comparator.get_complexity_rating("ARM") == "Medium"
    assert comparator.get_complexity_rating("x86") == "High"


def test_compare_addressing_modes():
    """Test comparison table."""
    comparator = AddressingModeComparator()
    table = comparator.compare_addressing_modes()
    assert len(table) == 4
    for row in table:
        assert "ISA" in row
        assert "Modes" in row
        assert "Complex" in row


def test_scaled_index_support():
    """Test scaled index addressing detection."""
    comparator = AddressingModeComparator()
    assert comparator.is_scaled_index_supported("x86") == True
    assert comparator.is_scaled_index_supported("RISC-V") == False
    assert comparator.is_scaled_index_supported("ARM") == False
    assert comparator.is_scaled_index_supported("MIPS") == False


def test_addressing_mode_count():
    """Test addressing mode count retrieval."""
    comparator = AddressingModeComparator()
    assert comparator.get_addressing_mode_count("RISC-V") == 5
    assert comparator.get_addressing_mode_count("ARM") == 7
    assert comparator.get_addressing_mode_count("x86") == 7
    assert comparator.get_addressing_mode_count("MIPS") == 5


def test_enum_values():
    """Test enum has correct values."""
    assert AddressingModeType.IMMEDIATE.value == "immediate"
    assert AddressingModeType.REGISTER.value == "register"
    assert AddressingModeType.DIRECT.value == "direct"
    assert AddressingModeType.REGISTER_INDIRECT.value == "register_indirect"
    assert AddressingModeType.BASE_INDIRECT.value == "base_indirect"
    assert AddressingModeType.PC_RELATIVE.value == "pc_relative"
    assert AddressingModeType.SCALED_INDEX.value == "scaled_index"
    assert AddressingModeType.STACK.value == "stack"


def test_create_addressing_mode():
    """Test creating an addressing mode."""
    mode = AddressingMode(
        name="Test Mode", mode_type=AddressingModeType.IMMEDIATE,
        description="Test description", example="test x1, #0x1234",
        encoded_size=4,
    )
    assert mode.name == "Test Mode"
    assert mode.mode_type == AddressingModeType.IMMEDIATE
    assert mode.description == "Test description"
    assert mode.encoded_size == 4


if __name__ == "__main__":
    import traceback
    tests = [
        test_get_addressing_modes, test_risc_v_modes,
        test_arm_modes, test_x86_modes, test_mips_modes,
        test_complexity_rating, test_compare_addressing_modes,
        test_scaled_index_support, test_addressing_mode_count,
        test_enum_values, test_create_addressing_mode,
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
