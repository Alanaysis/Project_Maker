#!/usr/bin/env python3
"""
Performance Benchmark Example
===============================

Run comprehensive benchmarks on the multi-GPU framework.
Measures:
- AllReduce throughput across different algorithms and tensor sizes
- Data parallel training throughput and scaling efficiency
- Communication overhead

Usage:
    python examples/benchmark.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from src.utils.benchmark import Benchmark
from src.utils.logger import setup_logger


def main():
    logger = setup_logger("benchmark", level=logging.INFO)

    logger.info("=" * 60)
    logger.info("MULTI-GPU FRAMEWORK BENCHMARK")
    logger.info("=" * 60)

    bench = Benchmark(gpu_counts=[1, 2, 4])

    results = bench.run_all()
    bench.print_report(results)

    logger.info("\nBenchmark complete!")


if __name__ == "__main__":
    main()
