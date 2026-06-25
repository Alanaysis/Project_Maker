"""
Easing Functions Demo

Demonstrates all available easing functions with visual output.
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from animation_engine.easing import EASING_FUNCTIONS, list_easing_functions


def render_easing_curve(name, fn, width=60, height=20):
    """Render an easing curve as ASCII art."""
    lines = []
    for row in range(height, -1, -1):
        line = ""
        y = row / height
        for col in range(width):
            x = col / width
            v = fn(x)
            if abs(v - y) < 1.0 / height:
                line += "*"
            elif row == 0:
                line += "-"
            elif col == 0:
                line += "|"
            else:
                line += " "
        lines.append(line)
    return lines


def main():
    print("=" * 65)
    print("  Animation Engine - Easing Functions Demo")
    print("=" * 65)
    print()

    funcs = list_easing_functions()

    # Group by family
    families = {}
    for name in funcs:
        family = name.split("_")[1] if "_" in name else "other"
        if family not in families:
            families[family] = []
        families[family].append(name)

    for family, names in sorted(families.items()):
        print(f"--- {family.upper()} ---")
        for name in names:
            fn = EASING_FUNCTIONS[name]
            # Sample values
            samples = [fn(t / 10) for t in range(11)]
            bar = " ".join(f"{s:.2f}" for s in samples)
            print(f"  {name:25s} | {bar}")
        print()

    # Show a few curves
    print("=" * 65)
    print("  Curve Visualization (ease_out_bounce)")
    print("=" * 65)
    fn = EASING_FUNCTIONS["ease_out_bounce"]
    curve = render_easing_curve("ease_out_bounce", fn, width=50, height=15)
    for line in curve:
        print(f"  {line}")
    print()

    # Practical example: animate a value
    print("=" * 65)
    print("  Practical Example: Animating x from 0 to 100")
    print("=" * 65)
    print()

    for easing_name in ["linear", "ease_in_quad", "ease_out_quad", "ease_in_out_quad"]:
        fn = EASING_FUNCTIONS[easing_name]
        print(f"  {easing_name}:")
        frames = []
        for i in range(11):
            t = i / 10
            v = fn(t) * 100
            bar = "#" * int(v / 2)
            frames.append(f"    t={t:.1f}  x={v:6.1f}  |{bar}")
        for f in frames:
            print(f)
        print()


if __name__ == "__main__":
    main()
