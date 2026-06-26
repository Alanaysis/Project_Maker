"""
Timing diagram generation / 时序图生成

Generates timing diagrams for sequential logic circuits using matplotlib.
使用matplotlib为时序逻辑电路生成时序图。

Timing diagrams visualize how signals change over clock cycles,
which is essential for understanding sequential circuit behavior.
时序图可视化信号如何随时钟周期变化，对理解时序电路行为至关重要。
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from typing import List, Dict, Tuple, Optional


class TimingDiagramGenerator:
    """
    Generates timing diagrams for sequential logic signals.
    为时序逻辑信号生成时序图。
    """

    # Signal colors for different signals
    SIGNAL_COLORS = {
        'clock': 'black',
        'input': 'blue',
        'output': 'red',
        'internal': 'green',
        'state': 'purple',
    }

    def __init__(self, figsize: Tuple[int, int] = (14, 8)):
        self.figsize = figsize
        self.signals: Dict[str, List[int]] = {}
        self.signal_labels: Dict[str, str] = {}
        self.signal_types: Dict[str, str] = {}
        self.num_cycles: int = 0

    def add_signal(self, name: str, data: List[int], label: str = "", signal_type: str = "output") -> None:
        """
        Add a signal to the timing diagram.
        添加信号到时序图。

        Args:
            name: Unique signal name
            data: List of 0/1 values for each clock cycle
            label: Display label
            signal_type: Signal type for coloring (clock/input/output/internal/state)
        """
        self.signals[name] = data
        self.signal_labels[name] = label or name
        self.signal_types[name] = signal_type
        self.num_cycles = max(self.num_cycles, len(data))

    def clear_signals(self) -> None:
        """Clear all signals / 清除所有信号"""
        self.signals.clear()
        self.signal_labels.clear()
        self.signal_types.clear()
        self.num_cycles = 0

    def generate(self, title: str = "Timing Diagram", save_path: Optional[str] = None) -> plt.Figure:
        """
        Generate and optionally save the timing diagram.
        生成并可选地保存时序图。

        Args:
            title: Diagram title
            save_path: Path to save the image (if None, returns figure only)

        Returns:
            The matplotlib Figure object
        """
        if not self.signals:
            raise ValueError("No signals to display. Add signals with add_signal().")

        fig, ax = plt.subplots(figsize=self.figsize)
        num_cycles = self.num_cycles

        # Calculate signal row spacing
        num_signals = len(self.signals)
        row_height = 0.8
        y_start = num_signals * row_height

        # Draw each signal
        for idx, (name, data) in enumerate(self.signals.items()):
            y_pos = y_start - idx * row_height
            color = self.SIGNAL_COLORS.get(self.signal_types.get(name, "output"), "blue")
            label = self.signal_labels[name]

            # Draw the signal waveform
            self._draw_signal(ax, data, y_pos, color, num_cycles)

            # Add signal label
            ax.text(-0.5, y_pos, label, ha='right', va='center', fontsize=9, fontweight='bold')

        # Add clock reference line
        if 'clock' in self.signal_types:
            clock_y = y_start - list(self.signals.keys()).index('clock') * row_height if 'clock' in self.signals else y_start
            ax.axhline(y=clock_y, color='gray', linestyle=':', alpha=0.3)

        # Format axes
        ax.set_xlim(-0.5, num_cycles + 0.5)
        ax.set_ylim(-0.5, y_start + 0.5)
        ax.set_xticks(range(num_cycles + 1))
        ax.set_xticklabels([str(i) for i in range(num_cycles + 1)])
        ax.set_yticks([])
        ax.set_title(title, fontsize=14, fontweight='bold', pad=10)
        ax.set_xlabel('Clock Cycle', fontsize=11)
        ax.grid(axis='x', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

        # Add legend
        legend_patches = [
            mpatches.Patch(color='black', label='Clock'),
            mpatches.Patch(color='blue', label='Input'),
            mpatches.Patch(color='red', label='Output'),
            mpatches.Patch(color='green', label='Internal'),
            mpatches.Patch(color='purple', label='State'),
        ]
        ax.legend(handles=legend_patches, loc='upper right', fontsize=8)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            print(f"Timing diagram saved to: {save_path}")

        return fig

    def _draw_signal(self, ax, data: List[int], y_pos: float, color: str, num_cycles: int) -> None:
        """
        Draw a single signal waveform.
        绘制单个信号波形。
        """
        # Extend data to cover all cycles
        extended_data = data + [data[-1]] if len(data) <= num_cycles else data[:num_cycles + 1]

        # Create step plot
        x = np.arange(len(extended_data))
        y = np.full(len(extended_data), y_pos)
        y[extended_data == 1] = y_pos + 0.3

        # Draw the signal
        for i in range(len(x) - 1):
            # Vertical transition
            if extended_data[i] != extended_data[i + 1]:
                ax.plot([x[i], x[i]], [y_pos, y_pos + 0.3], color=color, linewidth=1.5)
            # Horizontal segment
            ax.plot([x[i], x[i + 1]], [y[i], y[i + 1]], color=color, linewidth=1.5)

        # Draw clock edge markers
        if self.signal_types.get('clock') == 'clock':
            for i in range(len(x) - 1):
                if extended_data[i] == 0 and extended_data[i + 1] == 1:
                    ax.plot([x[i], x[i]], [y_pos, y_pos + 0.3], color='black', linewidth=2)
                    ax.plot([x[i] + 0.05, x[i]], [y_pos + 0.25, y_pos + 0.3], color='black', linewidth=1)


class ClockSignal:
    """
    Generates clock signal for timing diagrams.
    为时序图生成时钟信号。
    """

    @staticmethod
    def generate(num_cycles: int = 8, duty_cycle: float = 0.5) -> List[int]:
        """
        Generate a clock signal pattern.
        生成时钟信号模式。

        Args:
            num_cycles: Number of clock cycles
            duty_cycle: Duty cycle (0.5 = 50%)

        Returns:
            List of 0/1 values
        """
        signal = []
        for i in range(num_cycles):
            high_duration = int(duty_cycle * 2)
            signal.extend([1] * high_duration + [0] * (2 - high_duration))
        return signal[:num_cycles * 2]  # Simplified square wave


def generate_counter_timing_diagram(counter, num_cycles: int = 8,
                                     title: str = "Counter Timing Diagram",
                                     save_path: Optional[str] = None) -> TimingDiagramGenerator:
    """
    Generate a timing diagram for a counter.
    为计数器生成时序图。

    Args:
        counter: Counter object (RippleCounter, SynchronousCounter, etc.)
        num_cycles: Number of clock cycles to display
        title: Diagram title
        save_path: Optional save path

    Returns:
        TimingDiagramGenerator instance
    """
    generator = TimingDiagramGenerator(figsize=(14, 6))

    # Add clock signal
    clock = ClockSignal.generate(num_cycles)
    generator.add_signal('clock', clock, "CLK", "clock")

    # Add counter output bits (LSB first)
    num_bits = counter.num_bits
    for i in range(num_bits):
        bit_values = []
        for cycle in range(num_cycles):
            counter.step()
            bit_values.append((counter.value >> i) & 1)
        generator.add_signal(f'Q{i}', bit_values, f"Q{i}", "output")

    generator.generate(title=title, save_path=save_path)
    return generator


def generate_fsm_timing_diagram(fsm, input_sequence: List[str],
                                 title: str = "FSM Timing Diagram",
                                 save_path: Optional[str] = None) -> TimingDiagramGenerator:
    """
    Generate a timing diagram for an FSM execution.
    为状态机执行生成时序图。

    Args:
        fsm: FSM object
        input_sequence: Input sequence to process
        title: Diagram title
        save_path: Optional save path

    Returns:
        TimingDiagramGenerator instance
    """
    generator = TimingDiagramGenerator(figsize=(14, 6))

    # Add clock
    clock = ClockSignal.generate(len(input_sequence))
    generator.add_signal('clock', clock, "CLK", "clock")

    # Add input
    generator.add_signal('input', [int(b) for b in input_sequence], "INPUT", "input")

    # Run FSM and collect states
    fsm.reset()
    states = []
    for inp in input_sequence:
        output, state = fsm.step(inp)
        states.append(state)

    # Encode states as numbers for plotting
    state_names = list(set(states))
    state_to_num = {name: idx for idx, name in enumerate(state_names)}
    state_values = [state_to_num[s] for s in states]

    if state_values:
        # Extend for display
        extended = state_values + [state_values[-1]]
        x = np.arange(len(extended))
        y = np.array([state_to_num[s] for s in states + [states[-1]]])

        for i in range(len(x) - 1):
            if extended[i] != extended[i + 1]:
                pass  # Vertical line
            generator.add_signal(f'state_{i}', [state_values[i]], f"S={states[i]}", "state")

    # Add state labels
    if states:
        generator.generate(title=title, save_path=save_path)

    return generator
