"""
拟牛顿法

实现 BFGS 和 L-BFGS 算法。
"""

import numpy as np
from typing import Callable, Optional, List
from .base_optimizer import BaseOptimizer


class BFGS(BaseOptimizer):
    """BFGS 算法

    拟牛顿法，通过迭代更新海森矩阵的近似。
    B_{k+1} = B_k + (y_k y_k^T)/(y_k^T s_k) - (B_k s_k s_k^T B_k)/(s_k^T B_k s_k)
    """

    def __init__(
        self,
        initial_hessian: Optional[np.ndarray] = None,
        use_line_search: bool = True,
        max_iter: int = 1000,
        tol: float = 1e-6,
        verbose: bool = False,
    ):
        super().__init__(max_iter, tol, verbose)
        self.initial_hessian = initial_hessian
        self.use_line_search = use_line_search
        self.H = None  # 逆海森矩阵近似

    def step(
        self,
        x: np.ndarray,
        func: Callable,
        grad: Callable,
    ) -> np.ndarray:
        g = grad(x)

        # 初始化逆海森矩阵近似
        if self.H is None:
            if self.initial_hessian is not None:
                self.H = self.initial_hessian.copy()
            else:
                self.H = np.eye(len(x))

        # 计算搜索方向
        d = -self.H @ g

        # 线搜索
        if self.use_line_search:
            alpha = super().line_search(x, d, func, grad)
        else:
            alpha = 1.0

        # 更新位置
        s = alpha * d
        x_new = x + s

        # 计算梯度变化
        g_new = grad(x_new)
        y = g_new - g

        # BFGS 更新
        ys = y @ s
        if ys > 1e-10:  # 确保正定性
            rho = 1.0 / ys
            I = np.eye(len(x))
            V = I - rho * np.outer(s, y)
            W = I - rho * np.outer(y, s)
            self.H = V @ self.H @ W + rho * np.outer(s, s)

        return x_new

    def reset(self):
        """重置优化器状态"""
        self.H = None


class LBFGS(BaseOptimizer):
    """L-BFGS 算法

    有限内存 BFGS，适用于大规模问题。
    只存储最近 m 步的 s 和 y 向量。
    """

    def __init__(
        self,
        m: int = 10,
        use_line_search: bool = True,
        max_iter: int = 1000,
        tol: float = 1e-6,
        verbose: bool = False,
    ):
        super().__init__(max_iter, tol, verbose)
        self.m = m  # 存储的历史步数
        self.use_line_search = use_line_search
        self.s_list: List[np.ndarray] = []  # s_k = x_{k+1} - x_k
        self.y_list: List[np.ndarray] = []  # y_k = g_{k+1} - g_k
        self.prev_x: Optional[np.ndarray] = None
        self.prev_g: Optional[np.ndarray] = None

    def two_loop_recursion(self, g: np.ndarray) -> np.ndarray:
        """L-BFGS 两循环递归

        高效计算 H_k * g 而不显式存储 H_k。
        """
        q = g.copy()
        alpha_list = []

        # 第一个循环
        for s, y in zip(reversed(self.s_list), reversed(self.y_list)):
            rho = 1.0 / (y @ s)
            alpha = rho * (s @ q)
            q -= alpha * y
            alpha_list.append(alpha)

        # 初始 Hessian 近似（缩放单位矩阵）
        if len(self.s_list) > 0:
            s_last = self.s_list[-1]
            y_last = self.y_list[-1]
            gamma = (s_last @ y_last) / (y_last @ y_last)
            r = gamma * q
        else:
            r = q

        # 第二个循环
        alpha_list.reverse()
        for (s, y), alpha in zip(zip(self.s_list, self.y_list), alpha_list):
            rho = 1.0 / (y @ s)
            beta = rho * (y @ r)
            r += (alpha - beta) * s

        return r

    def step(
        self,
        x: np.ndarray,
        func: Callable,
        grad: Callable,
    ) -> np.ndarray:
        g = grad(x)

        # 计算搜索方向
        d = -self.two_loop_recursion(g)

        # 线搜索
        if self.use_line_search:
            alpha = super().line_search(x, d, func, grad)
        else:
            alpha = 1.0

        # 更新位置
        s = alpha * d
        x_new = x + s

        # 保存历史
        if self.prev_x is not None and self.prev_g is not None:
            s_k = x_new - self.prev_x
            y_k = g - self.prev_g  # 注意：这里 g 是当前梯度

            # 确保正定性
            if s_k @ y_k > 1e-10:
                self.s_list.append(s_k)
                self.y_list.append(y_k)

                # 保持历史长度
                if len(self.s_list) > self.m:
                    self.s_list.pop(0)
                    self.y_list.pop(0)

        self.prev_x = x_new.copy()
        self.prev_g = g.copy()

        return x_new

    def reset(self):
        """重置优化器状态"""
        self.s_list = []
        self.y_list = []
        self.prev_x = None
        self.prev_g = None


class SR1(BaseOptimizer):
    """SR1 (Symmetric Rank 1) 算法

    另一种拟牛顿更新方法，不要求正定性。
    B_{k+1} = B_k + (y_k - B_k s_k)(y_k - B_k s_k)^T / ((y_k - B_k s_k)^T s_k)
    """

    def __init__(
        self,
        initial_hessian: Optional[np.ndarray] = None,
        use_line_search: bool = True,
        max_iter: int = 1000,
        tol: float = 1e-6,
        verbose: bool = False,
    ):
        super().__init__(max_iter, tol, verbose)
        self.initial_hessian = initial_hessian
        self.use_line_search = use_line_search
        self.H = None  # 逆海森矩阵近似

    def step(
        self,
        x: np.ndarray,
        func: Callable,
        grad: Callable,
    ) -> np.ndarray:
        g = grad(x)

        # 初始化逆海森矩阵近似
        if self.H is None:
            if self.initial_hessian is not None:
                self.H = self.initial_hessian.copy()
            else:
                self.H = np.eye(len(x))

        # 计算搜索方向
        d = -self.H @ g

        # 线搜索
        if self.use_line_search:
            alpha = super().line_search(x, d, func, grad)
        else:
            alpha = 1.0

        # 更新位置
        s = alpha * d
        x_new = x + s

        # 计算梯度变化
        g_new = grad(x_new)
        y = g_new - g

        # SR1 更新
        r = y - self.H @ s
        rs = r @ s
        if abs(rs) > 1e-10:  # 避免除以零
            self.H += np.outer(r, r) / rs

        return x_new

    def reset(self):
        """重置优化器状态"""
        self.H = None
