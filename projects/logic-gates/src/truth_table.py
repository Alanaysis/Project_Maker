"""
Truth table generation for logic gates.

A truth table lists all possible input combinations and their corresponding outputs.
真值表列出所有可能的输入组合及其对应的输出。
"""

from typing import Callable, Dict, List, Tuple

from .gates import AND, OR, NOT, NAND, NOR, XOR, XNOR

# Map gate names to their functions
GATE_FUNCTIONS = {
    "AND": AND,
    "OR": OR,
    "NOT": NOT,
    "NAND": NAND,
    "NOR": NOR,
    "XOR": XOR,
    "XNOR": XNOR,
}


def generate_truth_table_2input(gate_func: Callable[[int, int], int],
                                gate_name: str = "Gate") -> List[Tuple[int, int, int]]:
    """
    Generate truth table for a 2-input gate.

    Args:
        gate_func: The gate function to test (e.g., AND, OR, XOR)
        gate_name: Display name for the gate

    Returns:
        List of (input_a, input_b, output) tuples
    """
    table = []
    for a in [0, 1]:
        for b in [0, 1]:
            output = gate_func(a, b)
            table.append((a, b, output))
    return table


def generate_truth_table_3input(gate_func: Callable[[int, int, int], int],
                                gate_name: str = "Gate") -> List[Tuple[int, int, int, int]]:
    """
    Generate truth table for a 3-input gate.

    Args:
        gate_func: The gate function to test
        gate_name: Display name for the gate

    Returns:
        List of (input_a, input_b, input_c, output) tuples
    """
    table = []
    for a in [0, 1]:
        for b in [0, 1]:
            for c in [0, 1]:
                output = gate_func(a, b, c)
                table.append((a, b, c, output))
    return table


def print_truth_table(gate_func: Callable, gate_name: str = "Gate",
                      num_inputs: int = 2) -> str:
    """
    Generate and print a formatted truth table string.

    Args:
        gate_func: The gate function to display
        gate_name: Display name for the gate
        num_inputs: Number of inputs (2 or 3)

    Returns:
        Formatted truth table as a string
    """
    lines = []
    padding = max(8, len(gate_name) + 2)

    if num_inputs == 2:
        header = f"  {gate_name} Truth Table (真值表)  "
        lines.append("=" * 30)
        lines.append(header.center(30))
        lines.append("=" * 30)
        lines.append(f"  A{' ':>3} B{' ':>3} | Out")
        lines.append(f"  {'-'*3} {'-'*3} | {'-'*3}")

        table = generate_truth_table_2input(gate_func, gate_name)
        for a, b, out in table:
            lines.append(f"  {a}     {b}     |  {out}")

    else:
        header = f"  {gate_name} Truth Table (真值表)  "
        lines.append("=" * 40)
        lines.append(header.center(40))
        lines.append("=" * 40)
        lines.append(f"  A{' ':>3} B{' ':>3} C{' ':>3} | Out")
        lines.append(f"  {'-'*3} {'-'*3} {'-'*3} | {'-'*3}")

        table = generate_truth_table_3input(gate_func, gate_name)
        for a, b, c, out in table:
            lines.append(f"  {a}     {b}     {c}     |  {out}")

    lines.append("=" * (len(lines[0]) if lines else 30))
    return "\n".join(lines)


def get_all_2input_truth_tables() -> Dict[str, List[Tuple[int, int, int]]]:
    """
    Get truth tables for all standard 2-input gates.

    Returns:
        Dictionary mapping gate names to their truth table rows
    """
    tables = {}
    for name, func in GATE_FUNCTIONS.items():
        tables[name] = generate_truth_table_2input(func, name)
    return tables
