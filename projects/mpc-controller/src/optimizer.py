"""
MPC 优化器 - 实现约束优化求解
"""

import numpy as np
from scipy.optimize import minimize, LinearConstraint, NonlinearConstraint
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass


@dataclass
class MPCConstraints:
    """MPC 约束配置"""
    # 输入约束
    u_min: Optional[np.ndarray] = None  # 输入下界
    u_max: Optional[np.ndarray] = None  # 输入上界

    # 状态约束
    x_min: Optional[np.ndarray] = None  # 状态下界
    x_max: Optional[np.ndarray] = None  # 状态上界

    # 输入变化率约束
    du_min: Optional[np.ndarray] = None  # 输入变化下界
    du_max: Optional[np.ndarray] = None  # 输入变化上界

    # 输出约束
    y_min: Optional[np.ndarray] = None  # 输出下界
    y_max: Optional[np.ndarray] = None  # 输出上界


@dataclass
class MPCWeights:
    """MPC 权重配置"""
    Q: Optional[np.ndarray] = None  # 状态权重矩阵
    R: Optional[np.ndarray] = None  # 输入权重矩阵
    Rd: Optional[np.ndarray] = None  # 输入变化率权重矩阵
    P: Optional[np.ndarray] = None  # 终端状态权重矩阵


class MPCOptimizer:
    """
    MPC 优化求解器

    使用 scipy.optimize 实现带约束的 MPC 优化问题求解
    """

    def __init__(self, n_states: int, n_inputs: int,
                 prediction_horizon: int, control_horizon: int,
                 constraints: Optional[MPCConstraints] = None,
                 weights: Optional[MPCWeights] = None):
        """
        初始化 MPC 优化器

        Args:
            n_states: 状态维度
            n_inputs: 输入维度
            prediction_horizon: 预测时域长度
            control_horizon: 控制时域长度
            constraints: 约束配置
            weights: 权重配置
        """
        self.n_states = n_states
        self.n_inputs = n_inputs
        self.Np = prediction_horizon
        self.Nc = control_horizon

        # 设置约束
        self.constraints = constraints if constraints is not None else MPCConstraints()

        # 设置权重
        if weights is None:
            weights = MPCWeights()
        self._setup_weights(weights)

    def _setup_weights(self, weights: MPCWeights):
        """设置权重矩阵"""
        # 状态权重
        if weights.Q is not None:
            self.Q = np.array(weights.Q, dtype=float)
        else:
            self.Q = np.eye(self.n_states)

        # 输入权重
        if weights.R is not None:
            self.R = np.array(weights.R, dtype=float)
        else:
            self.R = 0.1 * np.eye(self.n_inputs)

        # 输入变化率权重
        if weights.Rd is not None:
            self.Rd = np.array(weights.Rd, dtype=float)
        else:
            self.Rd = 0.01 * np.eye(self.n_inputs)

        # 终端权重
        if weights.P is not None:
            self.P = np.array(weights.P, dtype=float)
        else:
            self.P = self.Q.copy()

    def _build_objective(self, x0: np.ndarray, A_list: List[np.ndarray],
                         B_list: List[np.ndarray], C_list: List[np.ndarray],
                         x_ref: np.ndarray, u_prev: Optional[np.ndarray]) -> callable:
        """
        构建目标函数

        Args:
            x0: 当前状态
            A_list: 状态转移矩阵序列
            B_list: 输入矩阵序列
            C_list: 输出矩阵序列
            x_ref: 参考轨迹 (Np x n_outputs)
            u_prev: 上一时刻控制输入

        Returns:
            目标函数
        """
        def objective(U_flat):
            # 将扁平化的控制序列重塑为矩阵
            U = U_flat.reshape(self.Nc, self.n_inputs)

            # 预测状态序列
            X = np.zeros((self.Np + 1, self.n_states))
            Y = np.zeros((self.Np, C_list[0].shape[0]))
            X[0] = x0

            cost = 0.0

            for k in range(self.Np):
                # 获取对应的系统矩阵
                A = A_list[min(k, len(A_list) - 1)]
                B = B_list[min(k, len(B_list) - 1)]
                C = C_list[min(k, len(C_list) - 1)]

                # 获取控制输入（控制时域之后保持最后一个值）
                if k < self.Nc:
                    u = U[k]
                else:
                    u = U[-1]

                # 状态预测
                X[k + 1] = A @ X[k] + B @ u
                Y[k] = C @ X[k]

                # 跟踪误差代价
                y_ref_k = x_ref[min(k, len(x_ref) - 1)]
                e = Y[k] - y_ref_k
                cost += e.T @ self.Q[:C.shape[0], :C.shape[0]] @ e

                # 输入代价
                cost += u.T @ self.R @ u

                # 输入变化率代价
                if k == 0:
                    du = u - u_prev if u_prev is not None else u
                else:
                    prev_u = U[k - 1] if k < self.Nc else U[-1]
                    du = u - prev_u
                cost += du.T @ self.Rd @ du

            # 终端代价
            x_terminal = X[self.Np]
            x_ref_terminal = x_ref[min(self.Np - 1, len(x_ref) - 1)]
            e_terminal = self._compute_terminal_error(x_terminal, x_ref_terminal, C_list[-1])
            cost += e_terminal.T @ self.P @ e_terminal

            return cost

        return objective

    def _compute_terminal_error(self, x: np.ndarray, x_ref: np.ndarray,
                                 C: np.ndarray) -> np.ndarray:
        """计算终端误差"""
        y = C @ x
        return y - x_ref

    def _build_constraints(self, u_prev: Optional[np.ndarray]) -> List[Dict[str, Any]]:
        """
        构建约束列表

        Args:
            u_prev: 上一时刻控制输入

        Returns:
            scipy 优化约束列表
        """
        cons = []

        # 输入约束
        if self.constraints.u_min is not None:
            for k in range(self.Nc):
                for i in range(self.n_inputs):
                    idx = k * self.n_inputs + i
                    cons.append({
                        'type': 'ineq',
                        'fun': lambda U, idx=idx, i=i: U[idx] - self.constraints.u_min[i]
                    })

        if self.constraints.u_max is not None:
            for k in range(self.Nc):
                for i in range(self.n_inputs):
                    idx = k * self.n_inputs + i
                    cons.append({
                        'type': 'ineq',
                        'fun': lambda U, idx=idx, i=i: self.constraints.u_max[i] - U[idx]
                    })

        # 输入变化率约束
        if self.constraints.du_min is not None and u_prev is not None:
            for i in range(self.n_inputs):
                cons.append({
                    'type': 'ineq',
                    'fun': lambda U, i=i: U[i] - u_prev[i] - self.constraints.du_min[i]
                })

        if self.constraints.du_max is not None and u_prev is not None:
            for i in range(self.n_inputs):
                cons.append({
                    'type': 'ineq',
                    'fun': lambda U, i=i: self.constraints.du_max[i] - (U[i] - u_prev[i])
                })

        return cons

    def _build_bounds(self) -> List[Tuple[Optional[float], Optional[float]]]:
        """
        构建变量边界

        Returns:
            变量边界列表
        """
        bounds = []
        for k in range(self.Nc):
            for i in range(self.n_inputs):
                lb = self.constraints.u_min[i] if self.constraints.u_min is not None else None
                ub = self.constraints.u_max[i] if self.constraints.u_max is not None else None
                bounds.append((lb, ub))
        return bounds

    def solve(self, x0: np.ndarray, A_list: List[np.ndarray],
              B_list: List[np.ndarray], C_list: List[np.ndarray],
              x_ref: np.ndarray, u_prev: Optional[np.ndarray] = None,
              u_init: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        求解 MPC 优化问题

        Args:
            x0: 当前状态
            A_list: 状态转移矩阵序列
            B_list: 输入矩阵序列
            C_list: 输出矩阵序列
            x_ref: 参考轨迹 (Np x n_outputs 或 n_outputs)
            u_prev: 上一时刻控制输入
            u_init: 初始猜测控制序列

        Returns:
            (最优控制序列, 优化信息)
        """
        # 确保 x_ref 为二维数组
        if x_ref.ndim == 1:
            x_ref = np.tile(x_ref, (self.Np, 1))
        elif x_ref.shape[0] < self.Np:
            x_ref = np.tile(x_ref[-1:], (self.Np, 1))

        # 构建目标函数
        objective = self._build_objective(x0, A_list, B_list, C_list, x_ref, u_prev)

        # 构建约束
        constraints = self._build_constraints(u_prev)
        bounds = self._build_bounds()

        # 初始猜测
        if u_init is None:
            U0 = np.zeros(self.Nc * self.n_inputs)
        else:
            U0 = u_init.flatten()

        # 求解优化问题
        result = minimize(
            objective,
            U0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 100, 'ftol': 1e-6}
        )

        # 提取最优控制序列
        U_opt = result.x.reshape(self.Nc, self.n_inputs)

        # 优化信息
        info = {
            'success': result.success,
            'cost': result.fun,
            'iterations': result.nit,
            'message': result.message
        }

        return U_opt, info


def create_qp_solver(n_states: int, n_inputs: int,
                     Np: int, Nc: int) -> callable:
    """
    创建基于 QP 的 MPC 求解器（使用 Hildreth 方法）

    这是一个更高效的 QP 求解方法，适用于线性 MPC

    Args:
        n_states: 状态维度
        n_inputs: 输入维度
        Np: 预测时域
        Nc: 控制时域

    Returns:
        QP 求解函数
    """
    def solve_qp(H: np.ndarray, f: np.ndarray,
                 A_ineq: Optional[np.ndarray] = None,
                 b_ineq: Optional[np.ndarray] = None,
                 A_eq: Optional[np.ndarray] = None,
                 b_eq: Optional[np.ndarray] = None) -> np.ndarray:
        """
        使用 Hildreth 方法求解 QP 问题

        min 0.5 * x^T H x + f^T x
        s.t. A_ineq x <= b_ineq
             A_eq x = b_eq

        Args:
            H: Hessian 矩阵
            f: 线性项
            A_ineq: 不等式约束矩阵
            b_ineq: 不等式约束向量
            A_eq: 等式约束矩阵
            b_eq: 等式约束向量

        Returns:
            最优解
        """
        n = len(f)

        # Hildreth QP 求解器
        # 无约束解
        x_unc = -np.linalg.solve(H, f)

        # 如果没有约束，直接返回
        if A_ineq is None and A_eq is None:
            return x_unc

        # 处理不等式约束
        if A_ineq is not None:
            m = A_ineq.shape[0]
            P = A_ineq @ np.linalg.inv(H) @ A_ineq.T
            d = A_ineq @ np.linalg.inv(H) @ f + b_ineq

            # Hildreth 迭代
            lambda_k = np.zeros(m)
            for _ in range(100):
                lambda_prev = lambda_k.copy()
                for i in range(m):
                    w = 0.0
                    for j in range(m):
                        if j != i:
                            w += P[i, j] * lambda_k[j]
                    lambda_k[i] = max(0, -(d[i] + w) / P[i, i])

                if np.linalg.norm(lambda_k - lambda_prev) < 1e-8:
                    break

            x_opt = x_unc - np.linalg.inv(H) @ A_ineq.T @ lambda_k
        else:
            x_opt = x_unc

        return x_opt

    return solve_qp
