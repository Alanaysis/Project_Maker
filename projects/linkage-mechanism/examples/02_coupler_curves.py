"""Coupler curve visualization for different four-bar linkages.

不同四连杆机构的连杆曲线可视化。

Demonstrates how the coupler curve shape depends on the link lengths
and the position of the coupler point.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt

from src.position_analysis import FourBarParams, check_grashof, GrashofType
from src.visualization import plot_coupler_curve


def main():
    print("=" * 70)
    print("Coupler Curve Visualization / 连杆曲线可视化")
    print("=" * 70)

    # Define several different mechanisms
    mechanisms = [
        {
            'name': 'Crank-Rocker (曲柄摇杆)',
            'params': FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5,
                                     o2=(0.0, 0.0), o4=(4.0, 0.0)),
            'coupler_ratio': (0.5, 0.3),
            'coupler_offset': 0.0,
        },
        {
            'name': 'Double-Crank (双曲柄)',
            'params': FourBarParams(a1=3.0, a2=2.0, a3=5.0, a4=4.0,
                                     o2=(0.0, 0.0), o4=(3.0, 0.0)),
            'coupler_ratio': (0.5, 0.4),
            'coupler_offset': 0.0,
        },
        {
            'name': 'Double-Rocker (双摇杆)',
            'params': FourBarParams(a1=3.0, a2=1.5, a3=3.5, a4=2.5,
                                     o2=(0.0, 0.0), o4=(3.0, 0.0)),
            'coupler_ratio': (0.5, 0.2),
            'coupler_offset': 0.0,
        },
        {
            'name': 'Special (Change-Point) (特殊/变点机构)',
            'params': FourBarParams(a1=3.0, a2=2.0, a3=3.0, a4=2.0,
                                     o2=(0.0, 0.0), o4=(3.0, 0.0)),
            'coupler_ratio': (0.5, 0.5),
            'coupler_offset': 0.0,
        },
    ]

    # Plot all coupler curves on one figure
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.flatten()

    for idx, mech in enumerate(mechanisms):
        params = mech['params']
        grashof = check_grashof(params)

        ax = axes[idx]
        try:
            plot_coupler_curve(
                params,
                coupler_point_ratio=mech['coupler_ratio'],
                coupler_angle_offset=mech['coupler_offset'],
                num_points=720,
                ax=ax,
            )
            ax.set_title(
                f"{mech['name']}\nGrashof: {grashof.value}\n"
                f"a1={params.a1}, a2={params.a2}, a3={params.a3}, a4={params.a4}",
                fontsize=11,
            )
        except ValueError as e:
            ax.text(0.5, 0.5, f"Cannot generate curve:\n{e}",
                    transform=ax.transAxes, ha='center', va='center',
                    fontsize=10, color='red')
            ax.set_title(mech['name'], fontsize=11)

    plt.suptitle("Coupler Curves for Different Four-Bar Linkages\n不同四连杆机构的连杆曲线",
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), 'output_coupler_curves.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()

    # Individual large plots for each mechanism
    for idx, mech in enumerate(mechanisms):
        fig, ax = plt.subplots(figsize=(10, 10))
        try:
            plot_coupler_curve(
                mech['params'],
                coupler_point_ratio=mech['coupler_ratio'],
                coupler_angle_offset=mech['coupler_offset'],
                num_points=1440,
                ax=ax,
            )
            ax.set_title(
                f"{mech['name']} - Detailed View\n详细视图\n"
                f"a1={mech['params'].a1}, a2={mech['params'].a2}, "
                f"a3={mech['params'].a3}, a4={mech['params'].a4}",
                fontsize=13,
            )
            plt.tight_layout()
            output_path = os.path.join(
                os.path.dirname(__file__),
                f'output_coupler_curve_{idx}_{mech["name"].replace(" ", "_")}.png'
            )
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Saved: {output_path}")
        except ValueError as e:
            ax.text(0.5, 0.5, f"Cannot generate:\n{e}",
                    transform=ax.transAxes, ha='center', va='center',
                    fontsize=12, color='red')
            ax.set_title(mech['name'], fontsize=13)
            plt.tight_layout()
            output_path = os.path.join(
                os.path.dirname(__file__),
                f'output_coupler_curve_{idx}_error.png'
            )
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Saved: {output_path}")
        plt.close()

    print("\n" + "=" * 70)
    print("Coupler curve visualization complete!")
    print("连杆曲线可视化完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
