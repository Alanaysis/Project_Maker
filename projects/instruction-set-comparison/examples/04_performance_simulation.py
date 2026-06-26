"""
Example 4: Performance Simulation
示例4：性能模拟

This script demonstrates cycle-accurate performance simulation for
comparing different ISAs on common algorithms.

Key concepts:
- CPI (Cycles Per Instruction): Lower is better
- IPC (Instructions Per Cycle): Higher is better
- Pipeline effects: Branch penalties, cache misses
- Instruction count vs. clock rate trade-off (RISC vs CISC)
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from performance_simulation import PerformanceSimulator, PipelineSimulator


def generate_fibonacci_sequence(n: int) -> dict:
    """Generate a Fibonacci computation sequence for benchmarking."""
    instructions = []
    # Initialize
    instructions.append({"name": "li x1, 0", "type": "arith", "regs_read": 0, "regs_write": 1})
    instructions.append({"name": "li x2, 1", "type": "arith", "regs_read": 0, "regs_write": 1})
    instructions.append({"name": "li x3, 0", "type": "arith", "regs_read": 0, "regs_write": 1})
    instructions.append({"name": "li x4, 2", "type": "arith", "regs_read": 0, "regs_write": 1})

    # Loop setup
    instructions.append({"name": "addi x5, x3, 1", "type": "arith", "regs_read": 1, "regs_write": 1})
    instructions.append({"name": "add x6, x1, x2", "type": "arith", "regs_read": 2, "regs_write": 1})
    instructions.append({"name": "addi x7, x4, -1", "type": "arith", "regs_read": 1, "regs_write": 1})

    # Loop body (repeated)
    loop_body = [
        {"name": "add x8, x1, x2", "type": "arith", "regs_read": 2, "regs_write": 1},
        {"name": "addi x9, x7, -1", "type": "arith", "regs_read": 1, "regs_write": 1},
        {"name": "bne x9, x0, loop", "type": "branch", "regs_read": 2, "regs_write": 0},
        {"name": "add x1, x2, x0", "type": "arith", "regs_read": 2, "regs_write": 1},
        {"name": "add x2, x8, x0", "type": "arith", "regs_read": 2, "regs_write": 1},
        {"name": "addi x3, x3, 1", "type": "arith", "regs_read": 1, "regs_write": 1},
    ]

    # Add loop iterations
    for i in range(max(1, n // 5)):
        instructions.extend(loop_body)

    return instructions


def generate_sort_sequence() -> dict:
    """Generate a simple sort benchmark sequence."""
    instructions = []

    # Array setup (load values)
    for i in range(8):
        instructions.append({
            "name": f"li x{i+10}, {i*10}",
            "type": "arith",
            "regs_read": 0,
            "regs_write": 1
        })

    # Store to memory
    for i in range(8):
        instructions.append({
            "name": f"sw x{i+10}, {i*4}(x1)",
            "type": "store",
            "regs_read": 2,
            "regs_write": 0
        })

    # Load for comparison
    for i in range(8):
        instructions.append({
            "name": f"lw x{i+20}, {i*4}(x1)",
            "type": "load",
            "regs_read": 1,
            "regs_write": 1
        })

    # Comparison and swap operations
    for i in range(7):
        instructions.append({
            "name": "sub x30, x20, x21",
            "type": "arith",
            "regs_read": 2,
            "regs_write": 1
        })
        instructions.append({
            "name": "bge x30, x0, no_swap",
            "type": "branch",
            "regs_read": 2,
            "regs_write": 0,
            "branch_taken": True
        })
        instructions.append({
            "name": "add x31, x20, x0",
            "type": "arith",
            "regs_read": 1,
            "regs_write": 1
        })
        instructions.append({
            "name": "add x32, x21, x0",
            "type": "arith",
            "regs_read": 1,
            "regs_write": 1
        })
        instructions.append({
            "name": "sw x31, {i*4}(x1)",
            "type": "store",
            "regs_read": 2,
            "regs_write": 0
        })
        instructions.append({
            "name": "sw x32, {(i+1)*4}(x1)",
            "type": "store",
            "regs_read": 2,
            "regs_write": 0
        })
        instructions.append({
            "name": "no_swap:",
            "type": "label",
            "regs_read": 0,
            "regs_write": 0
        })

    return instructions


def run_performance_benchmarks():
    """Run performance benchmarks across ISAs."""
    print("=" * 80)
    print("EXAMPLE 4: PERFORMANCE SIMULATION")
    print("示例4：性能模拟")
    print("=" * 80)

    simulator = PerformanceSimulator(seed=42)

    # Benchmark 1: Fibonacci computation
    print("\n" + "=" * 80)
    print("BENCHMARK 1: FIBONACCI COMPUTATION")
    print("基准测试1：斐波那契计算")
    print("=" * 80)

    fib_instructions = generate_fibonacci_sequence(20)
    instructions_map = {
        "RISC-V": fib_instructions,
        "ARM": fib_instructions,
        "x86": fib_instructions,
        "MIPS": fib_instructions,
    }

    fib_result = simulator.run_benchmark(instructions_map)
    simulator.print_benchmark_result(fib_result)

    # Benchmark 2: Sort operation
    print("\n" + "=" * 80)
    print("BENCHMARK 2: SORT OPERATION")
    print("基准测试2：排序操作")
    print("=" * 80)

    sort_instructions = generate_sort_sequence()
    instructions_map = {
        "RISC-V": sort_instructions,
        "ARM": sort_instructions,
        "x86": sort_instructions,
        "MIPS": sort_instructions,
    }

    sort_result = simulator.run_benchmark(instructions_map)
    simulator.print_benchmark_result(sort_result)

    # Pipeline visualization
    print("\n" + "=" * 80)
    print("PIPELINE VISUALIZATION")
    print("流水线可视化")
    print("=" * 80)

    pipeline_sim = PipelineSimulator("RISC-V")
    sample_instructions = [
        {"name": "add", "type": "arith"},
        {"name": "lw", "type": "load"},
        {"name": "add", "type": "arith"},
        {"name": "sw", "type": "store"},
        {"name": "sub", "type": "arith"},
        {"name": "bne", "type": "branch"},
        {"name": "mul", "type": "arith"},
        {"name": "addi", "type": "arith"},
    ]

    visualization = pipeline_sim.get_pipeline_visualization(sample_instructions, num_cycles=10)
    for line in visualization:
        print(line)

    print("\n" + "=" * 80)
    print("KEY INSIGHTS")
    print("关键见解")
    print("=" * 80)
    print("""
  1. RISC ISAs (RISC-V, MIPS):
     - Higher instruction count for complex operations
     - Lower CPI due to simple pipeline
     - Predictable performance

  2. CISC ISA (x86):
     - Lower instruction count for same work
     - Higher CPI due to complex pipeline
     - Variable performance depending on micro-op translation

  3. ARM:
     - Balanced approach
     - Good instruction count and CPI
     - Efficient for mobile/embedded workloads

  4. Pipeline depth trade-off:
     - Deeper pipeline = higher clock speed
     - Deeper pipeline = larger branch penalty
     - Modern CPUs use out-of-order execution to mitigate
""")

    print("=" * 80)


if __name__ == "__main__":
    run_performance_benchmarks()
