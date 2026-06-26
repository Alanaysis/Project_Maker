"""
Tests for instruction encoding comparison module
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from instruction_encoding import (
    InstructionEncoder,
    CodeDensityAnalyzer,
    EncodingType,
    InstructionFormat,
    EncodingComparison,
)


def test_get_encoding_type():
    """Test encoding type detection for each ISA."""
    encoder = InstructionEncoder()
    assert encoder.get_encoding_type("RISC-V") == EncodingType.FIXED_LENGTH
    assert encoder.get_encoding_type("MIPS") == EncodingType.FIXED_LENGTH
    assert encoder.get_encoding_type("ARM") == EncodingType.HYBRID
    assert encoder.get_encoding_type("x86") == EncodingType.VARIABLE_LENGTH


def test_get_instruction_formats():
    """Test instruction format retrieval."""
    encoder = InstructionEncoder()
    riscv_formats = encoder.get_instruction_formats("RISC-V")
    assert len(riscv_formats) == 6
    assert "R-type" in riscv_formats
    assert "I-type" in riscv_formats

    mips_formats = encoder.get_instruction_formats("MIPS")
    assert len(mips_formats) == 3
    assert "R-type" in mips_formats

    arm_formats = encoder.get_instruction_formats("ARM")
    assert len(arm_formats) == 3
    assert "R-type" in arm_formats


def test_get_instructions():
    """Test instruction retrieval for each ISA."""
    encoder = InstructionEncoder()
    for isa in ["RISC-V", "MIPS", "ARM", "x86"]:
        instructions = encoder.get_instructions(isa)
        assert len(instructions) > 0
        for instr in instructions:
            assert "name" in instr
            assert "bytes" in instr


def test_riscv_format_fields():
    """Test RISC-V format field definitions."""
    encoder = InstructionEncoder()
    r_type = encoder.RISC_V_FORMATS["R-type"]
    assert r_type.total_bits == 32
    assert r_type.encoding_type == EncodingType.FIXED_LENGTH
    assert len(r_type.fields) == 6
    total_bits = sum(f["bits"] for f in r_type.fields)
    assert total_bits == 32


def test_mips_format_fields():
    """Test MIPS format field definitions."""
    encoder = InstructionEncoder()
    r_type = encoder.MIPS_FORMATS["R-type"]
    assert r_type.total_bits == 32
    assert len(r_type.fields) == 6
    total_bits = sum(f["bits"] for f in r_type.fields)
    assert total_bits == 32


def test_code_size_comparison():
    """Test code size comparison output."""
    encoder = InstructionEncoder()
    comparisons = encoder.compare_code_sizes()
    assert len(comparisons) == 5
    for comp in comparisons:
        assert comp.code_size_riscv == 4
        assert comp.code_size_mips == 4
        assert comp.code_size_arm == 4
        assert comp.code_size_x86 >= 1


def test_code_density_analysis():
    """Test code density analysis."""
    analyzer = CodeDensityAnalyzer()
    code_mix = {"add": 10, "load": 5, "store": 3}
    sizes = analyzer.analyze_code_density(code_mix)
    assert "RISC-V" in sizes
    assert "x86" in sizes
    assert sizes["x86"] < sizes["RISC-V"]


def test_density_ratio():
    """Test density ratio calculation."""
    analyzer = CodeDensityAnalyzer()
    ratio = analyzer.get_density_ratio("x86", "RISC-V")
    assert ratio > 1
    ratio_reverse = analyzer.get_density_ratio("RISC-V", "x86")
    assert ratio_reverse < 1


def test_enum_values():
    """Test enum has correct values."""
    assert EncodingType.FIXED_LENGTH.value == "fixed_length"
    assert EncodingType.VARIABLE_LENGTH.value == "variable_length"
    assert EncodingType.HYBRID.value == "hybrid"


def test_create_format():
    """Test creating an instruction format."""
    fmt = InstructionFormat(
        name="test", total_bits=32,
        fields=[{"name": "op", "bits": 7, "offset": 0}],
        encoding_type=EncodingType.FIXED_LENGTH,
    )
    assert fmt.name == "test"
    assert fmt.total_bits == 32
    assert len(fmt.fields) == 1


if __name__ == "__main__":
    import traceback
    tests = [
        test_get_encoding_type, test_get_instruction_formats,
        test_get_instructions, test_riscv_format_fields,
        test_mips_format_fields, test_code_size_comparison,
        test_code_density_analysis, test_density_ratio,
        test_enum_values, test_create_format,
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
