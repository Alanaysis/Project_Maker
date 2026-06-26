"""
线性规划求解器 (Linear Programming Solver)

实现单纯形法及其变体，用于求解标准形式的线性规划问题。

问题形式:
    最小化 c^T * x
    满足: A * x <= b
          x >= 0

核心算法:
    1. 标准形转换 (Standard Form Conversion)
    2. 两阶段单纯形法 (Two-Phase Simplex Method)
    3. 大M法 (Big-M Method)
    4. 对偶问题求解 (Dual Problem Solver)
"""
