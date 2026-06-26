"""
示例 4: 可视化排序过程

Visualizes the external sorting process step by step.
Shows how data flows through the algorithm stages.
"""

import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chunk import split_file_into_chunks
from src.in_memory_sort import sort_chunk
from src.external_sort import ExternalSort


def visualize_chunking(input_path: str, max_chunk_size: int):
    """可视化文件分块过程。"""
    print("\n" + "=" * 60)
    print("阶段 1: 文件分块")
    print("Phase 1: File Chunking")
    print("=" * 60)

    chunk_num = 0
    for chunk in split_file_into_chunks(input_path, max_chunk_size):
        chunk_num += 1
        print(f"\n  Run #{chunk_num}:")
        print(f"    记录数 / Records: {len(chunk)}")
        print(f"    范围 / Range: [{min(chunk)}, {max(chunk)}]")
        print(f"    示例值 / Sample: {chunk[:5]}...")
        print(f"    排序后 / Sorted: {sorted(chunk)[:5]}...")


def visualize_merge(runs_info: list):
    """可视化归并过程。"""
    print("\n" + "=" * 60)
    print("阶段 2: 多路归并")
    print("Phase 2: Multi-Way Merge")
    print("=" * 60)

    print(f"\n  输入 runs 数 / Input runs: {len(runs_info)}")
    print(f"  总记录数 / Total records: {sum(r['records'] for r in runs_info)}")

    # 显示每个 run 的最小值（归并时最先被选中的值）
    print("\n  各 run 的最小值 (归并起始值):")
    for i, info in enumerate(runs_info):
        print(f"    Run #{i + 1}: min={info['min_val']}, "
              f"records={info['records']}")

    print("\n  归并过程示意:")
    print("  ┌──────────┐     ┌──────────┐     ┌──────────┐")
    print("  │ Run #1   │     │ Run #2   │     │ Run #3   │")
    print("  │ (有序)   │     │ (有序)   │     │ (有序)   │")
    print("  └────┬─────┘     └────┬─────┘     └────┬─────┘")
    print("       │                │                │")
    print("       └────────┬───────┘────────┬───────┘")
    print("                ▼                ▼")
    print("         ┌──────────────────┐")
    print("         │   Min-Heap (k)   │")
    print("         │  维护 k 个最小值  │")
    print("         └────────┬─────────┘")
    print("                  ▼")
    print("         ┌──────────────────┐")
    print("         │   输出 (有序)     │")
    print("         └──────────────────┘")


def visualize_sorted_output(output_path: str, num_lines: int = 15):
    """可视化排序结果。"""
    print(f"\n{'=' * 60}")
    print(f"排序结果 (前 {num_lines} 行)")
    print(f"Sorted Output (first {num_lines} lines)")
    print(f"{'=' * 60}")

    with open(output_path, 'r') as f:
        lines = []
        for i, line in enumerate(f):
            if i >= num_lines:
                break
            lines.append(line.strip())

    for i, val in enumerate(lines, 1):
        print(f"  {i:>3}. {val}")

    # 显示最后几行
    with open(output_path, 'r') as f:
        all_lines = f.readlines()
        total = len(all_lines)
        print(f"\n  ... ({total} records total) ...")
        for i, line in enumerate(reversed(all_lines[-5:])):
            print(f"  {total - 4 + i:>3}. {line.strip()}")


def main():
    print("=" * 60)
    print("示例 4: 可视化排序过程")
    print("Example 4: Visualizing the Sort Process")
    print("=" * 60)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    input_file = os.path.join(data_dir, "visual_input.txt")
    output_file = os.path.join(data_dir, "visual_output.txt")

    # 生成较小的测试数据以便可视化
    num_records = 50
    random.seed(42)
    data = [random.randint(1, 200) for _ in range(num_records)]

    print(f"\n生成 {num_records} 条记录的测试数据...")
    with open(input_file, 'w') as f:
        for val in data:
            f.write(f"{val}\n")

    print(f"原始数据: {data}")

    # 执行外部排序
    temp_dir = os.path.join(data_dir, "visual_temp")
    with ExternalSort(temp_dir=temp_dir,
                      chunk_size_mb=0.0001) as sorter:
        result = sorter.sort(input_file, output_file)

        # 可视化各阶段
        visualize_chunking(input_file, int(0.0001 * 1024 * 1024))

        # 收集 runs 信息用于可视化
        runs_info = []
        for run in sorter.temp_files:
            with open(run.filepath, 'r') as f:
                vals = [int(line.strip()) for line in f if line.strip()]
            runs_info.append({
                'min_val': min(vals) if vals else 0,
                'records': len(vals),
            })

        visualize_merge(runs_info)

    visualize_sorted_output(output_file)

    print(f"\n{'=' * 60}")
    print(f"验证: {'通过 ✓' if result.is_valid else '失败 ✗'}")
    print(f"总 runs: {result.num_runs}")
    print(f"总耗时: {result.timings.get('total', 0):.4f}s")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
