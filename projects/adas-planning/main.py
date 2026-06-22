#!/usr/bin/env python3
"""
ADAS Planning and Control System - Main Entry Point

This script provides a command-line interface for running the ADAS
planning and control system.

Usage:
    python main.py [command] [options]

Commands:
    demo        - Run simple demo
    compare     - Compare algorithms
    test        - Run tests
    visualize   - Visualize results

Examples:
    python main.py demo
    python main.py compare --planner astar --controller pid
    python main.py test
"""

import argparse
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_demo():
    """Run simple demonstration."""
    from examples.simple_demo import main
    main()


def run_comparison(args):
    """Run algorithm comparison."""
    from src.simulation import Simulation, SimulationConfig

    config = SimulationConfig(
        map_width=50,
        map_height=50,
        obstacle_density=0.3,
        start=(2, 2),
        goal=(47, 47),
        planner_type=args.planner if args.planner else "astar",
        controller_type=args.controller if args.controller else "pid",
        seed=42
    )

    sim = Simulation(config)
    sim.setup()

    print("Running simulation...")
    result = sim.run()

    print(f"\nResults:")
    print(f"  Success: {result.success}")
    print(f"  Time: {result.total_time:.2f}s")
    print(f"  Average Error: {result.average_error:.3f}m")
    print(f"  Max Error: {result.max_error:.3f}m")

    if args.visualize:
        sim.visualize(result)


def run_tests():
    """Run unit tests."""
    import pytest
    pytest.main(["-v", "tests/"])


def run_visualization():
    """Run visualization demo."""
    from src.simulation import Simulation, SimulationConfig

    config = SimulationConfig(
        map_width=30,
        map_height=30,
        obstacle_density=0.25,
        start=(2, 15),
        goal=(27, 15),
        seed=42
    )

    sim = Simulation(config)
    sim.setup()

    result = sim.run()
    sim.visualize(result)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ADAS Planning and Control System"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run simple demo")

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare algorithms")
    compare_parser.add_argument(
        "--planner",
        choices=["astar", "dijkstra", "rrt"],
        default="astar",
        help="Planning algorithm"
    )
    compare_parser.add_argument(
        "--controller",
        choices=["pid", "stanley", "mpc"],
        default="pid",
        help="Control algorithm"
    )
    compare_parser.add_argument(
        "--visualize",
        action="store_true",
        help="Show visualization"
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")

    # Visualize command
    viz_parser = subparsers.add_parser("visualize", help="Run visualization demo")

    args = parser.parse_args()

    if args.command == "demo":
        run_demo()
    elif args.command == "compare":
        run_comparison(args)
    elif args.command == "test":
        run_tests()
    elif args.command == "visualize":
        run_visualization()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
