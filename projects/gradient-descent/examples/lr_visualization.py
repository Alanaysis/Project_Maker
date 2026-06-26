"""
Visualize learning rate schedules.

Shows how different schedulers adjust the learning rate over time.
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.lr_schedulers import StepLR, CosineLRScheduler, ExponentialLR, WarmupLR, CompositeScheduler


def visualize_lr_schedules():
    """Visualize all learning rate schedulers."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available, showing numerical results only")
        print_lr_schedules_numerically()
        return

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Learning Rate Schedulers Comparison', fontsize=14, fontweight='bold')

    epochs = np.arange(1, 1001)

    # 1. Step LR
    ax = axes[0, 0]
    step_lr = StepLR(initial_lr=0.1, step_size=200, gamma=0.1)
    lrs = []
    for _ in epochs:
        lrs.append(step_lr.step())
    ax.plot(epochs, lrs, 'b-', linewidth=2)
    ax.set_title('Step LR\n(step=200, gamma=0.1)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Learning Rate')
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')

    # 2. Cosine Annealing
    ax = axes[0, 1]
    cosine_lr = CosineLRScheduler(initial_lr=0.1, T_max=1000, eta_min=0.001)
    lrs = []
    for _ in epochs:
        lrs.append(cosine_lr.step())
    ax.plot(epochs, lrs, 'r-', linewidth=2)
    ax.set_title('Cosine Annealing\n(T_max=1000, eta_min=0.001)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Learning Rate')
    ax.grid(True, alpha=0.3)

    # 3. Exponential Decay
    ax = axes[0, 2]
    exp_lr = ExponentialLR(initial_lr=0.1, gamma=0.995)
    lrs = []
    for _ in epochs:
        lrs.append(exp_lr.step())
    ax.plot(epochs, lrs, 'g-', linewidth=2)
    ax.set_title('Exponential Decay\n(gamma=0.995)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Learning Rate')
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')

    # 4. Warmup
    ax = axes[1, 0]
    warmup_lr = WarmupLR(initial_lr=0.1, warmup_steps=100)
    lrs = []
    for _ in epochs:
        lrs.append(warmup_lr.step())
    ax.plot(epochs, lrs, 'm-', linewidth=2)
    ax.set_title('Warmup\n(warmup_steps=100)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Learning Rate')
    ax.grid(True, alpha=0.3)

    # 5. Composite (Warmup + Cosine)
    ax = axes[1, 1]
    warmup = WarmupLR(initial_lr=0.1, warmup_steps=100)
    cosine = CosineLRScheduler(initial_lr=0.1, T_max=900, eta_min=0.001)
    composite = CompositeScheduler(warmup, cosine)
    lrs = []
    for _ in epochs:
        lrs.append(composite.step())
    ax.plot(epochs, lrs, 'c-', linewidth=2)
    ax.axvline(x=100, color='gray', linestyle='--', alpha=0.5, label='Warmup end')
    ax.set_title('Composite\n(Warmup + Cosine)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Learning Rate')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # 6. Comparison of all schedulers
    ax = axes[1, 2]
    schedulers = [
        ('Step', StepLR(0.1, 200, 0.1)),
        ('Cosine', CosineLRScheduler(0.1, 1000, 0.001)),
        ('Exponential', ExponentialLR(0.1, 0.995)),
        ('Warmup', WarmupLR(0.1, 100)),
    ]
    colors = ['blue', 'red', 'green', 'orange']
    for (name, sched), color in zip(schedulers, colors):
        lrs = []
        for _ in epochs:
            lrs.append(sched.step())
        ax.plot(epochs, lrs, color=color, linewidth=1.5, label=name)
    ax.set_title('All Schedulers Compared')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Learning Rate')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_yscale('log')

    plt.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), 'lr_schedules.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Learning rate schedule visualization saved to: {output_path}")

    # Also show numerical results
    print("\nFinal learning rates after 1000 epochs:")
    for name, sched in schedulers:
        for _ in epochs:
            sched.step()
        print(f"  {name:15s}: lr = {sched.get_lr():.8f}")


def print_lr_schedules_numerically():
    """Print LR schedule values without visualization."""
    epochs = np.arange(1, 1001)

    schedulers = {
        'Step LR': (StepLR(0.1, 200, 0.1), epochs),
        'Cosine': (CosineLRScheduler(0.1, 1000, 0.001), epochs),
        'Exponential': (ExponentialLR(0.1, 0.995), epochs),
        'Warmup': (WarmupLR(0.1, 100), epochs),
    }

    print("\nLearning Rate Evolution:")
    print(f"{'Epoch':>8s} | ", end='')
    for name in schedulers:
        print(f'{name:>14s} | ', end='')
    print()
    print("-" * 80)

    for i, epoch in enumerate(epochs):
        print(f'{epoch:>8d} | ', end='')
        for name, (sched, _) in schedulers.items():
            lr = sched.step()
            print(f'{lr:>14.8f} | ', end='')
        print()

    print("\nFinal LR after 1000 epochs:")
    for name, (sched, _) in schedulers.items():
        print(f"  {name:15s}: lr = {sched.get_lr():.8f}")


if __name__ == '__main__':
    visualize_lr_schedules()
