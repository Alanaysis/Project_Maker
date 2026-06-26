"""
Visualization utilities for logic gate truth tables and circuits.

Requires matplotlib. Install with: pip install matplotlib
需要 matplotlib。安装：pip install matplotlib
"""

from typing import Callable, Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


def visualize_truth_tables(gate_funcs: Dict[str, Callable],
                           save_path: str = "truth_tables.png",
                           title: str = "Logic Gates Truth Tables"):
    """
    Visualize truth tables for multiple gates as bar charts.
    以柱状图形式可视化多个门的真值表。

    Args:
        gate_funcs: Dictionary mapping gate names to gate functions
        save_path: Path to save the output image
        title: Chart title
    """
    n_gates = len(gate_funcs)
    fig = plt.figure(figsize=(14, 6 + n_gates * 2))
    gs = gridspec.GridSpec(n_gates, 1, hspace=0.5)

    gate_colors = {
        "AND": "#4CAF50",
        "OR": "#2196F3",
        "NOT": "#FF9800",
        "NAND": "#9C27B0",
        "NOR": "#F44336",
        "XOR": "#00BCD4",
        "XNOR": "#FF5722",
    }

    for idx, (name, func) in enumerate(gate_funcs.items()):
        ax = fig.add_subplot(gs[idx])

        inputs = []
        outputs = []
        for a in [0, 1]:
            for b in [0, 1]:
                out = func(a, b)
                inputs.append(f"{a},{b}")
                outputs.append(out)

        colors = [gate_colors.get(name, "#607D8B")] * 4
        bars = ax.bar(inputs, outputs, color=colors, edgecolor="black", linewidth=0.8)

        for bar, val in zip(bars, outputs):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                    str(val), ha="center", va="bottom", fontsize=12, fontweight="bold")

        ax.set_title(f"{name} Gate ({name} 门)", fontsize=14, fontweight="bold")
        ax.set_ylabel("Output", fontsize=11)
        ax.set_xlabel("Inputs (A, B)", fontsize=11)
        ax.set_ylim(-0.15, 1.3)
        ax.set_yticks([0, 1])
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle(title, fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Truth table visualization saved to: {save_path}")


def visualize_circuit_operations(save_path: str = "circuit_ops.png"):
    """
    Visualize basic circuit operations (half adder, full adder).
    可视化基本电路操作（半加器、全加器）。
    """
    from .gates import XOR, AND, OR
    from .circuits import HalfAdder, FullAdder

    fig, axes = plt.subplots(2, 1, figsize=(12, 10))

    # Half Adder visualization
    ax1 = axes[0]
    ha = HalfAdder()
    ha_inputs = [(0, 0), (0, 1), (1, 0), (1, 1)]
    sums = []
    carries = []
    for a, b in ha_inputs:
        w_a = Wire("A", a)
        w_b = Wire("B", b)
        ha.set_inputs(w_a, w_b)
        ha.evaluate()
        s, c = ha.get_result()
        sums.append(s)
        carries.append(c)

    x_pos = [i for i, _ in enumerate(ha_inputs)]
    bar_width = 0.35
    ax1.bar([p - bar_width / 2 for p in x_pos], sums, bar_width,
            label="Sum (和)", color="#4CAF50", edgecolor="black")
    ax1.bar([p + bar_width / 2 for p in x_pos], carries, bar_width,
            label="Carry (进位)", color="#F44336", edgecolor="black")

    for i, (a, b) in enumerate(ha_inputs):
        ax1.text(i, max(sums[0], carries[0]) + 0.1,
                 f"A={a},B={b}", ha="center", fontsize=9)

    ax1.set_title("Half Adder (半加器) Operation", fontsize=14, fontweight="bold")
    ax1.set_ylabel("Output Value", fontsize=11)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(["0,0", "0,1", "1,0", "1,1"])
    ax1.set_ylim(-0.1, 1.3)
    ax1.set_yticks([0, 1])
    ax1.legend(loc="upper right")
    ax1.grid(axis="y", alpha=0.3)

    # Full Adder visualization
    ax2 = axes[1]
    fa = FullAdder()
    fa_inputs = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 0),
                 (0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 1)]
    fa_sums = []
    fa_carries = []
    for a, b, c in fa_inputs:
        w_a = Wire("A", a)
        w_b = Wire("B", b)
        w_c = Wire("Cin", c)
        fa.set_inputs(w_a, w_b, w_c)
        fa.evaluate()
        s, c_out = fa.get_result()
        fa_sums.append(s)
        fa_carries.append(c_out)

    x_pos2 = [i for i, _ in enumerate(fa_inputs)]
    ax2.bar([p - bar_width / 2 for p in x_pos2], fa_sums, bar_width,
            label="Sum (和)", color="#4CAF50", edgecolor="black")
    ax2.bar([p + bar_width / 2 for p in x_pos2], fa_carries, bar_width,
            label="Cout (进位输出)", color="#F44336", edgecolor="black")

    for i, (a, b, c) in enumerate(fa_inputs):
        ax2.text(i, max(fa_sums[0], fa_carries[0]) + 0.1,
                 f"A={a},B={b},Cin={c}", ha="center", fontsize=8)

    ax2.set_title("Full Adder (全加器) Operation", fontsize=14, fontweight="bold")
    ax2.set_ylabel("Output Value", fontsize=11)
    ax2.set_xticks(x_pos2)
    tick_labels = [f"{a},{b},{c}" for a, b, c in fa_inputs]
    ax2.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=8)
    ax2.set_ylim(-0.1, 1.3)
    ax2.set_yticks([0, 1])
    ax2.legend(loc="upper right")
    ax2.grid(axis="y", alpha=0.3)

    fig.suptitle("Circuit Operations (电路操作)", fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Circuit operation visualization saved to: {save_path}")


class Wire:
    """Minimal Wire class for visualization compatibility."""

    def __init__(self, name: str = "", value: int = 0):
        self.name = name
        self.value = value
