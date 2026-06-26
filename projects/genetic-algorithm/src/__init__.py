"""
遗传算法优化框架
Genetic Algorithm Optimization Framework

一个教育性的遗传算法实现，包含：
- 个体和种群管理
- 多种选择方法（锦标赛、轮盘赌、排名、精英）
- 多种交叉算子（单点、多点、均匀、算术）
- 多种变异算子（位翻转、交换、逆序、高斯）
- 世代和稳态两种进化模式
- 收敛检测
- 参数配置

Usage:
    from geneticalgorithm import GeneticAlgorithm
    from geneticalgorithm.suites import FunctionOptimizationSuite

    ga = GeneticAlgorithm(...)
    result = ga.optimize()
"""

__version__ = "0.1.0"
__author__ = "Learning Project"
