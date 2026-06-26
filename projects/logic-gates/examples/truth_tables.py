"""
Example 1: Display truth tables for all basic logic gates.

Run: python examples/truth_tables.py
"""

from src.gates import AND, OR, NOT, NAND, NOR, XOR, XNOR
from src.truth_table import print_truth_table, get_all_2input_truth_tables

# Display truth table for each gate
gates = [
    ("AND", AND),
    ("OR", OR),
    ("NOT", NOT),
    ("NAND", NAND),
    ("NOR", NOR),
    ("XOR", XOR),
    ("XNOR", XNOR),
]

print("=" * 50)
print("  Logic Gates Truth Tables (逻辑门真值表)")
print("=" * 50)

for name, func in gates:
    print()
    if name == "NOT":
        print("  A | Out")
        print("  --- | ---")
        for a in [0, 1]:
            print(f"  {a}   |  {func(a)}")
    else:
        print(print_truth_table(func, name, 2))

print("\n" + "=" * 50)
print("  真值表说明 (Truth Table Notes):")
print("  - 0 表示低电平 (Low voltage)")
print("  - 1 表示高电平 (High voltage)")
print("  - 每个真值表列出所有可能的输入组合")
print("=" * 50)
