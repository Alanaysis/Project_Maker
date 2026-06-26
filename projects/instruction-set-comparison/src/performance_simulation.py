"""
Performance Simulation Module
性能模拟模块

This module provides a cycle-accurate simulation framework for comparing
instruction execution across different ISAs.

Key concepts:
- CPI (Cycles Per Instruction): Average number of cycles per instruction.
  Lower CPI means higher performance for a given clock speed.
- IPC (Instructions Per Cycle): Average number of instructions executed
  per cycle. Higher IPC indicates better pipelining and parallelism.
- Instruction-level parallelism (ILP): How many instructions can execute
  simultaneously in a pipeline.
- Pipeline depth: Number of stages in the instruction pipeline.
  Deeper pipelines allow higher clock speeds but increase branch penalty.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import random


class PipelineStage(Enum):
    """Standard pipeline stages for RISC processors."""
    IF = "IF"      # Instruction Fetch
    ID = "ID"      # Instruction Decode
    EX = "EX"      # Execute
    MEM = "MEM"    # Memory Access
    WB = "WB"      # Write Back


class BranchPrediction(Enum):
    """Branch prediction strategies."""
    STATIC_ALWAYS_TAKEN = "static_always_taken"
    STATIC_NOT_TAKEN = "static_not_taken"
    DYNAMIC_TAKEN = "dynamic_taken"  # Simulated prediction


@dataclass
class ExecutionStats:
    """Statistics for a single instruction execution."""
    instruction: str
    isa: str
    cycles: int
    completed: bool
    branch_taken: bool = False
    memory_access: bool = False
    register_read: int = 0
    register_write: int = 0


@dataclass
class BenchmarkResult:
    """Result of a benchmark comparison."""
    benchmark_name: str
    instructions: List[Dict]
    results: Dict[str, ExecutionStats]
    total_cycles_by_isa: Dict[str, int]
    total_instructions_by_isa: Dict[str, int]
    avg_cpi_by_isa: Dict[str, float]
    winner: str  # ISA with lowest total cycles


class PerformanceSimulator:
    """
    Cycle-accurate performance simulator for ISA comparison.

    This simulator models the execution of instruction sequences on
    different ISAs, accounting for:
    - Different instruction latencies
    - Pipeline characteristics
    - Branch penalties
    - Memory access costs
    """

    # Instruction latency tables (in cycles) for each ISA
    # These are simplified models based on typical implementations
    INSTRUCTION_LATENCIES = {
        "RISC-V": {
            "add": 1, "sub": 1, "and": 1, "or": 1, "xor": 1, "sll": 1, "srl": 1,
            "addi": 1, "andi": 1, "ori": 1, "slli": 1, "srli": 1,
            "lw": 3, "sw": 3,
            "lb": 3, "lh": 3, "lwu": 3, "lbu": 3, "lhu": 3,
            "ld": 3, "sd": 3,
            "beq": 1, "bne": 1, "blt": 1, "bge": 1, "bltu": 1, "bgeu": 1,
            "jal": 3, "jalr": 3,
            "lui": 1, "auipc": 1,
            "nop": 1,
        },
        "MIPS": {
            "add": 1, "sub": 1, "and": 1, "or": 1, "xor": 1, "sll": 1, "srl": 1,
            "addi": 1, "andi": 1, "ori": 1, "slli": 1, "srli": 1,
            "lw": 3, "sw": 3,
            "lb": 3, "lh": 3, "lbu": 3, "lhu": 3,
            "sd": 3,
            "beq": 1, "bne": 1, "bltz": 1, "bgtz": 1,
            "j": 3, "jal": 3, "jalr": 3,
            "nop": 1,
        },
        "ARM": {
            "add": 1, "sub": 1, "and": 1, "orr": 1, "eor": 1, "lsl": 1, "lsr": 1,
            "addi": 1, "and": 1, "orr": 1, "lsl": 1, "lsr": 1,
            "ldr": 3, "str": 3,
            "ldr": 3, "str": 3,
            "cbz": 1, "cbn": 1, "tbz": 1, "tbn": 1,
            "b": 3, "bl": 3, "br": 3, "blr": 3,
            "nop": 1,
        },
        "x86": {
            "add": 1, "sub": 1, "and": 1, "or": 1, "xor": 1, "shl": 1, "shr": 1,
            "mov": 1,
            "mov": 3,  # load or store
            "lea": 1,
            "jmp": 1,  # near jump
            "call": 3,
            "ret": 2,
            "nop": 1,
        },
    }

    # Pipeline characteristics for each ISA
    PIPELINE_CONFIG = {
        "RISC-V": {
            "stages": 5,
            "branch_penalty": 2,
            "max_ils": 2,  # Max instructions in flight
            "has_forwarding": True,
            "has_hazard_detection": True,
        },
        "MIPS": {
            "stages": 5,
            "branch_penalty": 5,  # Classic MIPS has larger branch penalty
            "max_ils": 2,
            "has_forwarding": False,
            "has_hazard_detection": True,
        },
        "ARM": {
            "stages": 13,  # AArch64 has deep pipeline
            "branch_penalty": 10,
            "max_ils": 4,
            "has_forwarding": True,
            "has_hazard_detection": True,
        },
        "x86": {
            "stages": 15,  # Modern x86 has very deep pipeline
            "branch_penalty": 14,
            "max_ils": 6,
            "has_forwarding": True,
            "has_hazard_detection": True,
        },
    }

    # Memory access latency model
    MEMORY_MODEL = {
        "L1_hit": 1,    # L1 cache hit: 1 cycle
        "L1_miss": 10,  # L1 cache miss: ~10 cycles
        "L2_hit": 40,   # L2 cache hit: ~40 cycles
        "L2_miss": 200,  # L2 cache miss: ~200 cycles
        "DRAM": 300,    # Main memory access
    }

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the performance simulator.

        Args:
            seed: Random seed for reproducible results
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        self.stats_history: List[ExecutionStats] = []

    def classify_instruction(self, instruction: Dict) -> str:
        """
        Classify an instruction into a category for latency lookup.

        Args:
            instruction: Instruction dictionary with 'name' and 'type' fields

        Returns:
            Category string for latency lookup
        """
        name = instruction.get("name", "").lower()
        instr_type = instruction.get("type", "unknown")

        if instr_type == "arith":
            return name
        elif instr_type == "load":
            return "lw" if "ld" not in name else "ld"
        elif instr_type == "store":
            return "sw" if "sd" not in name else "sd"
        elif instr_type == "branch":
            return "beq" if "jump" not in name else "jal"
        elif instr_type == "jump":
            return "jal"
        else:
            return name

    def simulate_instruction(self, instruction: Dict, isa: str) -> ExecutionStats:
        """
        Simulate the execution of a single instruction.

        Args:
            instruction: Instruction dictionary
            isa: ISA name

        Returns:
            ExecutionStats for this instruction
        """
        category = self.classify_instruction(instruction)
        latencies = self.INSTRUCTION_LATENCIES.get(isa, {})
        latency = latencies.get(category, 3)  # Default latency

        # Check for branch
        branch_taken = instruction.get("branch_taken", False)
        if branch_taken:
            latency += self.PIPELINE_CONFIG.get(isa, {}).get("branch_penalty", 2)

        # Check for memory access
        memory_access = instruction.get("type", "") in ("load", "store")
        if memory_access:
            # Simulate cache behavior
            cache_hit = random.random() < 0.85  # 85% L1 hit rate
            if cache_hit:
                latency += self.MEMORY_MODEL["L1_hit"]
            else:
                latency += self.MEMORY_MODEL["L1_miss"]

        # Count register operations
        reg_read = instruction.get("regs_read", 2)
        reg_write = instruction.get("regs_write", 1)

        return ExecutionStats(
            instruction=instruction.get("name", "unknown"),
            isa=isa,
            cycles=latency,
            completed=True,
            branch_taken=branch_taken,
            memory_access=memory_access,
            register_read=reg_read,
            register_write=reg_write,
        )

    def run_benchmark(self, instructions: Dict[str, List[Dict]]) -> BenchmarkResult:
        """
        Run a benchmark across all ISAs.

        Args:
            instructions: Dictionary mapping ISA name to list of instructions

        Returns:
            BenchmarkResult with comparison data
        """
        results = {}
        total_cycles = {}
        total_instructions = {}

        for isa, instr_list in instructions.items():
            cycles = 0
            instr_count = 0

            for instr in instr_list:
                stats = self.simulate_instruction(instr, isa)
                results[f"{isa}:{instr_count}"] = stats
                cycles += stats.cycles
                instr_count += 1
                self.stats_history.append(stats)

            total_cycles[isa] = cycles
            total_instructions[isa] = instr_count

        # Determine winner (lowest total cycles)
        winner = min(total_cycles, key=total_cycles.get)

        # Calculate average CPI
        avg_cpi = {}
        for isa in total_cycles:
            if total_instructions[isa] > 0:
                avg_cpi[isa] = total_cycles[isa] / total_instructions[isa]
            else:
                avg_cpi[isa] = 0.0

        return BenchmarkResult(
            benchmark_name="Custom Benchmark",
            instructions=[],
            results=results,
            total_cycles_by_isa=total_cycles,
            total_instructions_by_isa=total_instructions,
            avg_cpi_by_isa=avg_cpi,
            winner=winner,
        )

    def print_benchmark_result(self, result: BenchmarkResult):
        """Print benchmark results in a readable format."""
        print("=" * 80)
        print(f"BENCHMARK RESULT: {result.benchmark_name}")
        print("基准测试结果")
        print("=" * 80)

        print(f"\n{'ISA':<10} {'Instructions':>14} {'Cycles':>10} {'CPI':>8} {'Rank':>6}")
        print("-" * 55)

        # Sort by cycles
        sorted_isas = sorted(
            result.total_cycles_by_isa.items(),
            key=lambda x: x[1]
        )

        for rank, (isa, cycles) in enumerate(sorted_isas, 1):
            instrs = result.total_instructions_by_isa[isa]
            cpi = result.avg_cpi_by_isa[isa]
            print(f"{isa:<10} {instrs:>14} {cycles:>10} {cpi:>8.2f} {rank:>6}")

        print(f"\nWinner: {result.winner}")
        print("=" * 80)


class PipelineSimulator:
    """
    Simulates a simplified RISC pipeline for detailed analysis.

    This simulator models the 5-stage RISC pipeline (IF, ID, EX, MEM, WB)
    and shows how hazards and forwarding affect execution.
    """

    def __init__(self, isa: str = "RISC-V"):
        """
        Initialize the pipeline simulator.

        Args:
            isa: ISA to simulate
        """
        self.isa = isa
        self.pipeline_config = PerformanceSimulator.PIPELINE_CONFIG.get(isa, {})
        self.pipeline_stages = self.pipeline_config.get("stages", 5)
        self.branch_penalty = self.pipeline_config.get("branch_penalty", 2)
        self.has_forwarding = self.pipeline_config.get("has_forwarding", False)
        self.cycle = 0
        self.pipeline: List[Optional[Dict]] = [None] * self.pipeline_stages

    def simulate_pipeline(self, instructions: List[Dict]) -> List[int]:
        """
        Simulate instruction execution through the pipeline.

        Args:
            instructions: List of instructions to simulate

        Returns:
            List of cycle counts for each instruction
        """
        cycle_counts = []
        instruction_queue = list(instructions)
        pipeline = [None] * self.pipeline_stages
        self.cycle = 0

        while instruction_queue or any(p is not None for p in pipeline):
            self.cycle += 1

            # Shift pipeline stages
            for i in range(self.pipeline_stages - 1, 0, -1):
                if pipeline[i] is not None:
                    pipeline[i]["stage"] += 1
                    if pipeline[i]["stage"] >= self.pipeline_stages:
                        cycle_counts.append(pipeline[i].get("start_cycle", self.cycle))
                        pipeline[i] = None
                elif i > 0 and pipeline[i - 1] is None:
                    break

            # Fetch new instruction if pipeline stage 0 is free
            if pipeline[0] is None and instruction_queue:
                instr = instruction_queue.pop(0)
                instr["start_cycle"] = self.cycle
                instr["stage"] = 0
                pipeline[0] = instr

        return cycle_counts

    def get_pipeline_visualization(self, instructions: List[Dict],
                                   num_cycles: int = 10) -> List[str]:
        """
        Generate a text visualization of the pipeline.

        Args:
            instructions: Instructions to visualize
            num_cycles: Number of cycles to show

        Returns:
            List of strings representing pipeline state per cycle
        """
        visualization = []
        pipeline = [None] * self.pipeline_stages
        instr_queue = list(instructions[:num_cycles])

        stage_names = ["IF", "ID", "EX", "MEM", "WB"]
        if self.pipeline_stages > 5:
            stage_names = ["IF", "ID", "EX", "MEM", "WB", "ROB", "RET"]
            while len(stage_names) < self.pipeline_stages:
                stage_names.append(f"STG{len(stage_names)}")

        for cycle in range(num_cycles + 5):
            row = f"Cycle {cycle:3d}: "
            for i in range(self.pipeline_stages):
                if pipeline[i] is not None:
                    stage_idx = min(pipeline[i]["stage"], len(stage_names) - 1)
                    instr_name = pipeline[i].get("name", "?")[:3]
                    row += f"[{stage_names[stage_idx]}:{instr_name}] "
                else:
                    row += "[----] "
            visualization.append(row)

            # Shift pipeline
            for i in range(self.pipeline_stages - 1, 0, -1):
                if pipeline[i] is not None:
                    pipeline[i]["stage"] += 1
                    if pipeline[i]["stage"] >= self.pipeline_stages:
                        pipeline[i] = None
                elif i > 0 and pipeline[i - 1] is None:
                    break

            # Fetch
            if pipeline[0] is None and instr_queue:
                instr = instr_queue.pop(0)
                instr["start_cycle"] = cycle
                instr["stage"] = 0
                pipeline[0] = instr

        return visualization
