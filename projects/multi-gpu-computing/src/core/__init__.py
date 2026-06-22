"""
Core module for multi-GPU parallel computing framework.

This module contains:
- Tensor: GPU tensor abstraction
- Communicator: NCCL communication abstraction
- AllReduce: Gradient synchronization algorithms
- DataParallelTrainer: Data parallel training
- ModelParallelTrainer: Model parallel training
"""

from .tensor import GPUTensor
from .communicator import Communicator, NCCLCommunicator, SimulationCommunicator
from .allreduce import AllReduce, RingAllReduce, TreeAllReduce
from .data_parallel import DataParallelTrainer
from .model_parallel import ModelParallelTrainer

__all__ = [
    "GPUTensor",
    "Communicator",
    "NCCLCommunicator",
    "SimulationCommunicator",
    "AllReduce",
    "RingAllReduce",
    "TreeAllReduce",
    "DataParallelTrainer",
    "ModelParallelTrainer",
]
