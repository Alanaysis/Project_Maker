"""
Example 2: Visualize truth tables using matplotlib.

Run: python examples/visualize_truth_tables.py
Requires: pip install matplotlib
"""

from src.gates import AND, OR, NOT, NAND, NOR, XOR, XNOR
from src.visualizer import visualize_truth_tables

# Collect all gate functions
gate_funcs = {
    "AND": AND,
    "OR": OR,
    "NAND": NAND,
    "NOR": NOR,
    "XOR": XOR,
    "XNOR": XNOR,
}

print("Generating truth table visualization...")
print("生成真值表可视化...")

visualize_truth_tables(
    gate_funcs,
    save_path="truth_tables.png",
    title="Logic Gates Truth Tables (逻辑门真值表)"
)

print("\nVisualization complete! Check truth_tables.png")
print("可视化完成！请查看 truth_tables.png")
