"""
粒子群优化 (Particle Swarm Optimization) 实现

核心模块：
- particle: 粒子类
- swarm: 粒子群类（标准 PSO）
- adaptive_pso: 自适应 PSO
- chaos_pso: 混沌 PSO
- functions: 测试函数
- visualizer: 可视化

应用模块：
- neural_network: 神经网络训练
- feature_selection: 特征选择
"""

from .particle import Particle
from .swarm import Swarm, PSOConfig, PSOResult
from .adaptive_pso import AdaptiveSwarm, AdaptivePSOConfig
from .chaos_pso import ChaosSwarm, ChaosPSOConfig
from .functions import (
    sphere,
    rosenbrock,
    rastrigin,
    ackley,
    griewank,
    get_function,
    BENCHMARK_FUNCTIONS,
)
from .visualizer import PSOVisualizer
from .neural_network import NeuralNetwork, NeuralNetworkTrainer, NeuralNetworkConfig
from .feature_selection import FeatureSelector, FeatureSelectionConfig, BinaryPSO

__all__ = [
    # 核心
    "Particle",
    "Swarm",
    "PSOConfig",
    "PSOResult",
    # 变体
    "AdaptiveSwarm",
    "AdaptivePSOConfig",
    "ChaosSwarm",
    "ChaosPSOConfig",
    # 测试函数
    "sphere",
    "rosenbrock",
    "rastrigin",
    "ackley",
    "griewank",
    "get_function",
    "BENCHMARK_FUNCTIONS",
    # 可视化
    "PSOVisualizer",
    # 应用
    "NeuralNetwork",
    "NeuralNetworkTrainer",
    "NeuralNetworkConfig",
    "FeatureSelector",
    "FeatureSelectionConfig",
    "BinaryPSO",
]
