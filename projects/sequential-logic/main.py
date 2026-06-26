#!/usr/bin/env python3
"""
Sequential Logic Circuit Simulator / 时序逻辑电路模拟器

Usage:
    python main.py flip-flop      # Run flip-flop simulation
    python main.py counter        # Run counter simulation
    python main.py register       # Run register operations
    python main.py fsm            # Run FSM demo
    python main.py all            # Run all demos
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("Available demos: flip-flop, counter, register, fsm, all")
        sys.exit(1)

    demo_name = sys.argv[1].lower()

    demos = {
        "flip-flop": "examples/01_flip_flop_simulation.py",
        "counter": "examples/02_counter_simulation.py",
        "register": "examples/04_register_operations.py",
        "fsm": "examples/05_fsm_demo.py",
        "all": None,
    }

    if demo_name not in demos:
        print(f"Unknown demo: {demo_name}")
        print(f"Available: {', '.join(demos.keys())}")
        sys.exit(1)

    if demo_name == "all":
        print("Running all demos... / 运行所有演示...")
        print()
        for name, path in demos.items():
            if name != "all" and path:
                print("=" * 60)
                print(f"Running: {name}")
                print("=" * 60)
                os.system(f"python {path}")
                print()
    else:
        path = demos[demo_name]
        os.system(f"python {path}")


if __name__ == "__main__":
    main()
