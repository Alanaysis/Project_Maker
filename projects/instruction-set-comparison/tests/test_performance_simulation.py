"""
Tests for performance simulation module
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from performance_simulation import (
    PerformanceSimulator,
    PipelineSimulator,
    ExecutionStats,
    BenchmarkResult,
    PipelineStage,
    BranchPrediction,
)


def test_classify_instruction():
    """Test instruction classification."""
    simulator = PerformanceSimulator(seed=42)
    arith = simulator.classify_instruction({"name": "add", "type": "arith"})
    assert arith == "add"
    load = simulator.classify_instruction({"name": "lw", "type": "load"})
    assert load == "lw"
    store = simulator.classify_instruction({"name": "sw", "type": "store"})
    assert store == "sw"
    branch = simulator.classify_instruction({"name": "beq", "type": "branch"})
    assert branch == "beq"


def test_simulate_instruction():
    """Test single instruction simulation."""
    simulator = PerformanceSimulator(seed=42)
    instr = {"name": "add", "type": "arith", "regs_read": 2, "regs_write": 1}
    stats = simulator.simulate_instruction(instr, "RISC-V")
    assert stats.completed == True
    assert stats.isa == "RISC-V"
    assert stats.cycles > 0


def test_simulate_instruction_latency():
    """Test instruction latency values."""
    simulator = PerformanceSimulator(seed=42)
    arith = {"name": "add", "type": "arith", "regs_read": 2, "regs_write": 1}
    load = {"name": "lw", "type": "load", "regs_read": 1, "regs_write": 1}
    arith_stats = simulator.simulate_instruction(arith, "RISC-V")
    load_stats = simulator.simulate_instruction(load, "RISC-V")
    assert arith_stats.cycles > 0
    assert load_stats.cycles > 0


def test_run_benchmark():
    """Test benchmark execution."""
    simulator = PerformanceSimulator(seed=42)
    instructions = {
        "RISC-V": [
            {"name": "addi x1, x0, 1", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "addi x2, x0, 2", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "add x3, x1, x2", "type": "arith", "regs_read": 2, "regs_write": 1},
        ],
        "ARM": [
            {"name": "mov x1, #1", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "mov x2, #2", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "add x3, x1, x2", "type": "arith", "regs_read": 2, "regs_write": 1},
        ],
    }
    result = simulator.run_benchmark(instructions)
    assert result.winner in ["RISC-V", "ARM"]
    assert len(result.total_cycles_by_isa) == 2
    assert len(result.total_instructions_by_isa) == 2
    assert len(result.avg_cpi_by_isa) == 2


def test_benchmark_result_structure():
    """Test benchmark result data structure."""
    simulator = PerformanceSimulator(seed=42)
    instructions = {
        "RISC-V": [
            {"name": "addi x1, x0, 1", "type": "arith", "regs_read": 0, "regs_write": 1},
        ],
    }
    result = simulator.run_benchmark(instructions)
    assert result.benchmark_name == "Custom Benchmark"
    assert "RISC-V" in result.total_cycles_by_isa
    assert "RISC-V" in result.total_instructions_by_isa
    assert "RISC-V" in result.avg_cpi_by_isa


def test_seed_reproducibility():
    """Test that results are reproducible with same seed."""
    sim1 = PerformanceSimulator(seed=123)
    sim2 = PerformanceSimulator(seed=123)
    instructions = {
        "RISC-V": [
            {"name": "addi x1, x0, 1", "type": "arith", "regs_read": 0, "regs_write": 1},
            {"name": "lw x2, 0(x3)", "type": "load", "regs_read": 1, "regs_write": 1},
            {"name": "sw x4, 0(x3)", "type": "store", "regs_read": 2, "regs_write": 0},
        ],
    }
    result1 = sim1.run_benchmark(instructions)
    result2 = sim2.run_benchmark(instructions)
    for isa in result1.total_cycles_by_isa:
        assert result1.total_cycles_by_isa[isa] == result2.total_cycles_by_isa[isa]


def test_pipeline_config():
    """Test pipeline configuration values."""
    simulator = PerformanceSimulator(seed=42)
    for isa in ["RISC-V", "MIPS", "ARM", "x86"]:
        config = simulator.PIPELINE_CONFIG[isa]
        assert config["stages"] > 0
        assert config["branch_penalty"] > 0
        assert config["max_ils"] > 0
        assert isinstance(config["has_forwarding"], bool)
        assert isinstance(config["has_hazard_detection"], bool)


def test_memory_model():
    """Test memory model values."""
    simulator = PerformanceSimulator(seed=42)
    model = simulator.MEMORY_MODEL
    assert model["L1_hit"] < model["L1_miss"]
    assert model["L1_miss"] < model["L2_hit"]
    assert model["L2_hit"] < model["L2_miss"]
    assert model["L2_miss"] < model["DRAM"]


def test_pipeline_init():
    """Test pipeline simulator initialization."""
    for isa in ["RISC-V", "MIPS", "ARM", "x86"]:
        sim = PipelineSimulator(isa)
        assert sim.isa == isa
        assert sim.pipeline_stages > 0
        assert sim.branch_penalty > 0


def test_simulate_pipeline():
    """Test pipeline simulation."""
    sim = PipelineSimulator("RISC-V")
    instructions = [
        {"name": "add", "type": "arith"},
        {"name": "lw", "type": "load"},
        {"name": "add", "type": "arith"},
        {"name": "sw", "type": "store"},
    ]
    cycle_counts = sim.simulate_pipeline(instructions)
    assert len(cycle_counts) == len(instructions)


def test_pipeline_visualization():
    """Test pipeline visualization output."""
    sim = PipelineSimulator("RISC-V")
    instructions = [
        {"name": "add", "type": "arith"},
        {"name": "lw", "type": "load"},
        {"name": "sub", "type": "arith"},
    ]
    viz = sim.get_pipeline_visualization(instructions, num_cycles=5)
    assert len(viz) > 0
    assert "Cycle" in viz[0]


def test_pipeline_stage():
    """Test PipelineStage enum."""
    stages = [s.value for s in PipelineStage]
    assert "IF" in stages
    assert "ID" in stages
    assert "EX" in stages
    assert "MEM" in stages
    assert "WB" in stages


def test_branch_prediction():
    """Test BranchPrediction enum."""
    predictions = [p.value for p in BranchPrediction]
    assert "static_always_taken" in predictions
    assert "static_not_taken" in predictions
    assert "dynamic_taken" in predictions


def test_create_stats():
    """Test creating execution stats."""
    stats = ExecutionStats(
        instruction="add", isa="RISC-V", cycles=3,
        completed=True, branch_taken=False,
        memory_access=False, register_read=2, register_write=1,
    )
    assert stats.instruction == "add"
    assert stats.isa == "RISC-V"
    assert stats.cycles == 3
    assert stats.completed == True


if __name__ == "__main__":
    import traceback
    tests = [
        test_classify_instruction, test_simulate_instruction,
        test_simulate_instruction_latency, test_run_benchmark,
        test_benchmark_result_structure, test_seed_reproducibility,
        test_pipeline_config, test_memory_model,
        test_pipeline_init, test_simulate_pipeline,
        test_pipeline_visualization, test_pipeline_stage,
        test_branch_prediction, test_create_stats,
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
