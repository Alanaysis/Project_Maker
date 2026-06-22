"""
Multi-GPU Parallel Computing Framework
========================================

A learning-oriented multi-GPU parallel computing framework supporting:
- Data Parallelism
- Model Parallelism
- NCCL-based gradient synchronization (AllReduce)

Core training loop:
    Data Sharding -> Multi-GPU Compute -> Gradient Sync -> Parameter Update

Usage:
    from src.core import DataParallelTrainer, ModelParallelTrainer
    from src.core import AllReduceCommunicator
"""

__version__ = "0.1.0"
__author__ = "learning-project"
