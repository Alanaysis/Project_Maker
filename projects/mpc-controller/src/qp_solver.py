"""
QP 求解器 - 实现 MPC 中的二次规划问题求解

MPC 的滚动优化核心是求解如下 QP 问题：
    min  0.5 * x^T * H * x + f^T * x
    s.t. A_ineq * x <= b_ineq
         A_eq * x = b_eq
         lb <= x <= ub

本模块实现三种 QP 求解器：
1. Hildreth 方法 - 简单迭代法
2. 活动集方法 - 精确方法
3. 基于 scipy 的通用求解器
"""

import numpy as np
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum


class QPSolverType(Enum):
    """QP 求解器类型"""
    HILDRETH = "hildreth"         # Hildreth 迭代法
    ACTIVE_SET = "active_set"     # 活动集方法
    SCIPY = "scipy"               # scipy 求解器


@dataclass
class QPResult:
    """QP 求解结果"""
    x_optimal: np.ndarray          # 最优解
    cost: float                    # 最优代价
    iterations: int                # 迭代次数
    success: bool                  # 是否成功
    message: str                   # 求解信息
    lambda_opt: Optional[np.ndarray] = None  # 最优拉格朗日乘子


class QPSolver:
    """
    QP 求解器

    求解标准 QP 问题：
        min  0.5 * x^T * H * x + f^T * x
        s.t. A * x <= b
             lb <= x <= ub
    """

    def __init__(self, solver_type: QPSolverType = QPSolverType.HILDRETH,
                 max_iterations: int = 200,
                 tolerance: float = 1e-8,
                 regularization: float = 1e-8):
        """
        初始化 QP 求解器

        Args:
            solver_type: 求解器类型
            max_iterations: 最大迭代次数
            tolerance: 收敛容差
            regularization: 正则化参数
        """
        self.solver_type = solver_type
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.regularization = regularization

    def solve(self, H: np.ndarray, f: np.ndarray,
              A_ineq: Optional[np.ndarray] = None,
              b_ineq: Optional[np.ndarray] = None,
              lb: Optional[np.ndarray] = None,
              ub: Optional[np.ndarray] = None,
              x_init: Optional[np.ndarray] = None) -> QPResult:
        """
        求解 QP 问题

        Args:
            H: Hessian 矩阵 (n x n)，必须对称正定
            f: 线性项 (n,)
            A_ineq: 不等式约束矩阵 (m x n)
            b_ineq: 不等式约束向量 (m,)
            lb: 变量下界 (n,)
            ub: 变量上界 (n,)
            x_init: 初始猜测 (n,)

        Returns:
            QPResult 求解结果
        """
        # 确保 H 对称正定
        H_reg = H + self.regularization * np.eye(H.shape[0])

        # 将边界约束转换为不等式约束
        A_full, b_full = self._build_constraints(A_ineq, b_ineq, lb, ub, H.shape[0])

        if self.solver_type == QPSolverType.HILDRETH:
            return self._solve_hildreth(H_reg, f, A_full, b_full)
        elif self.solver_type == QPSolverType.ACTIVE_SET:
            return self._solve_active_set(H_reg, f, A_full, b_full, lb, ub, x_init)
        else:
            return self._solve_scipy(H_reg, f, A_full, b_full, lb, ub)

    def _build_constraints(self, A_ineq: Optional[np.ndarray],
                           b_ineq: Optional[np.ndarray],
                           lb: Optional[np.ndarray],
                           ub: Optional[np.ndarray],
                           n: int) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """构建完整的约束矩阵"""
        constraints_A = []
        constraints_b = []

        # 添加原始不等式约束
        if A_ineq is not None and b_ineq is not None:
            constraints_A.append(A_ineq)
            constraints_b.append(b_ineq)

        # 添加下界约束: -x <= -lb => -I * x <= -lb
        if lb is not None:
            constraints_A.append(-np.eye(n))
            constraints_b.append(-lb)

        # 添加上界约束: x <= ub => I * x <= ub
        if ub is not None:
            constraints_A.append(np.eye(n))
            constraints_b.append(ub)

        if len(constraints_A) > 0:
            A_full = np.vstack(constraints_A)
            b_full = np.concatenate(constraints_b)
            return A_full, b_full

        return None, None

    def _solve_hildreth(self, H: np.ndarray, f: np.ndarray,
                        A: Optional[np.ndarray],
                        b: Optional[np.ndarray]) -> QPResult:
        """
        Hildreth QP 求解方法

        通过求解对偶问题迭代更新拉格朗日乘子

        对偶问题:
            max -0.5 * λ^T * K * λ - λ^T * d
            s.t. λ >= 0

        其中:
            K = A * H^{-1} * A^T
            d = A * H^{-1} * f + b
        """
        n = len(f)

        # 无约束解
        try:
            H_inv = np.linalg.inv(H)
        except np.linalg.LinAlgError:
            H_inv = np.linalg.pinv(H)

        x_unc = -H_inv @ f

        # 如果没有约束，直接返回
        if A is None or b is None:
            cost = 0.5 * x_unc.T @ H @ x_unc + f.T @ x_unc
            return QPResult(
                x_optimal=x_unc,
                cost=cost,
                iterations=0,
                success=True,
                message="无约束解"
            )

        m = A.shape[0]

        # 计算对偶问题参数
        K = A @ H_inv @ A.T
        d = A @ H_inv @ f + b

        # Hildreth 迭代
        lambda_k = np.zeros(m)
        iterations = 0

        for iteration in range(self.max_iterations):
            lambda_prev = lambda_k.copy()

            for i in range(m):
                w = 0.0
                for j in range(m):
                    if j != i:
                        w += K[i, j] * lambda_k[j]

                # 更新 lambda[i]
                lambda_k[i] = max(0.0, -(d[i] + w) / K[i, i])

            iterations = iteration + 1

            # 检查收敛
            if np.linalg.norm(lambda_k - lambda_prev) < self.tolerance:
                break

        # 计算原问题最优解
        x_opt = x_unc - H_inv @ A.T @ lambda_k
        cost = 0.5 * x_opt.T @ H @ x_opt + f.T @ x_opt

        return QPResult(
            x_optimal=x_opt,
            cost=cost,
            iterations=iterations,
            success=True,
            message=f"Hildreth 方法收敛，迭代 {iterations} 次",
            lambda_opt=lambda_k
        )

    def _solve_active_set(self, H: np.ndarray, f: np.ndarray,
                          A: Optional[np.ndarray],
                          b: Optional[np.ndarray],
                          lb: Optional[np.ndarray],
                          ub: Optional[np.ndarray],
                          x_init: Optional[np.ndarray]) -> QPResult:
        """
        活动集方法

        通过迭代识别活动约束集来求解 QP 问题
        """
        n = len(f)

        # 初始可行点
        if x_init is not None:
            x = x_init.copy()
        else:
            # 使用无约束解的投影
            x = -np.linalg.solve(H, f)
            if lb is not None:
                x = np.maximum(x, lb)
            if ub is not None:
                x = np.minimum(x, ub)

        # 初始活动集（边界约束）
        active_set = set()

        # 检查初始点的活动约束
        if lb is not None:
            for i in range(n):
                if abs(x[i] - lb[i]) < 1e-10:
                    active_set.add(('lb', i))
        if ub is not None:
            for i in range(n):
                if abs(x[i] - ub[i]) < 1e-10:
                    active_set.add(('ub', i))

        iterations = 0

        for iteration in range(self.max_iterations):
            iterations = iteration + 1

            # 计算梯度
            g = H @ x + f

            # 构建活动约束矩阵
            W_A = []
            W_b = []

            # 边界约束
            for (type_, idx) in active_set:
                if type_ == 'lb':
                    ei = np.zeros(n)
                    ei[idx] = -1.0
                    W_A.append(ei)
                    W_b.append(-lb[idx])
                elif type_ == 'ub':
                    ei = np.zeros(n)
                    ei[idx] = 1.0
                    W_A.append(ei)
                    W_b.append(ub[idx])

            # 不等式约束
            if A is not None:
                for i in range(A.shape[0]):
                    # 检查约束是否活动
                    if abs(A[i] @ x - b[i]) < 1e-10:
                        W_A.append(A[i])
                        W_b.append(b[i])

            if len(W_A) == 0:
                # 无活动约束，求解无约束问题
                p = -np.linalg.solve(H, g)
            else:
                W_A = np.array(W_A)
                W_b = np.array(W_b)

                # 求解 KKT 系统
                # [H  W_A^T] [p ]   [-g]
                # [W_A   0 ] [mu] = [0 ]
                n_w = W_A.shape[0]
                KKT = np.block([
                    [H, W_A.T],
                    [W_A, np.zeros((n_w, n_w))]
                ])
                rhs = np.concatenate([-g, np.zeros(n_w)])

                try:
                    sol = np.linalg.solve(KKT, rhs)
                    p = sol[:n]
                    mu = sol[n:]
                except np.linalg.LinAlgError:
                    break

            # 检查是否收敛
            if np.linalg.norm(p) < self.tolerance:
                # 检查 KKT 条件
                if len(W_A) == 0 or np.all(mu >= -self.tolerance):
                    break
                else:
                    # 移除最负的乘子对应的约束
                    min_idx = np.argmin(mu)
                    # 移除对应约束
                    active_list = list(active_set)
                    if min_idx < len(active_list):
                        active_set.remove(active_list[min_idx])
                    continue

            # 线搜索确定步长
            alpha = 1.0

            # 检查边界约束
            if lb is not None:
                for i in range(n):
                    if p[i] < 0:
                        alpha_i = (lb[i] - x[i]) / p[i]
                        if 0 < alpha_i < alpha:
                            alpha = alpha_i

            if ub is not None:
                for i in range(n):
                    if p[i] > 0:
                        alpha_i = (ub[i] - x[i]) / p[i]
                        if 0 < alpha_i < alpha:
                            alpha = alpha_i

            # 检查不等式约束
            if A is not None:
                for i in range(A.shape[0]):
                    Ap = A[i] @ p
                    if Ap > 0:
                        alpha_i = (b[i] - A[i] @ x) / Ap
                        if 0 < alpha_i < alpha:
                            alpha = alpha_i

            # 更新
            x = x + alpha * p

            # 更新活动集
            if lb is not None:
                for i in range(n):
                    if abs(x[i] - lb[i]) < 1e-10:
                        active_set.add(('lb', i))
                    elif ('lb', i) in active_set:
                        active_set.discard(('lb', i))

            if ub is not None:
                for i in range(n):
                    if abs(x[i] - ub[i]) < 1e-10:
                        active_set.add(('ub', i))
                    elif ('ub', i) in active_set:
                        active_set.discard(('ub', i))

        cost = 0.5 * x.T @ H @ x + f.T @ x

        return QPResult(
            x_optimal=x,
            cost=cost,
            iterations=iterations,
            success=True,
            message=f"活动集方法收敛，迭代 {iterations} 次"
        )

    def _solve_scipy(self, H: np.ndarray, f: np.ndarray,
                     A_ineq: Optional[np.ndarray],
                     b_ineq: Optional[np.ndarray],
                     lb: Optional[np.ndarray],
                     ub: Optional[np.ndarray]) -> QPResult:
        """
        使用 scipy.optimize 求解 QP 问题
        """
        from scipy.optimize import minimize

        n = len(f)

        def objective(x):
            return 0.5 * x @ H @ x + f @ x

        def gradient(x):
            return H @ x + f

        # 构建约束
        constraints = []
        if A_ineq is not None and b_ineq is not None:
            constraints.append({
                'type': 'ineq',
                'fun': lambda x: b_ineq - A_ineq @ x
            })

        # 构建边界
        bounds = None
        if lb is not None or ub is not None:
            bounds = []
            for i in range(n):
                l = lb[i] if lb is not None else None
                u = ub[i] if ub is not None else None
                bounds.append((l, u))

        # 初始猜测
        x0 = -np.linalg.solve(H, f)
        if lb is not None:
            x0 = np.maximum(x0, lb)
        if ub is not None:
            x0 = np.minimum(x0, ub)

        result = minimize(
            objective,
            x0,
            jac=gradient,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': self.max_iterations, 'ftol': self.tolerance}
        )

        return QPResult(
            x_optimal=result.x,
            cost=result.fun,
            iterations=result.nit,
            success=result.success,
            message=result.message
        )


def build_mpc_qp_matrices(A_list, B_list, C_list, Q, R, Rd, P,
                           x0, x_ref, u_prev, Np, Nc):
    """
    构建 MPC 优化问题的 QP 矩阵

    将 MPC 问题转化为标准 QP 形式:
        min  0.5 * U^T * H * U + f^T * U
        s.t. 约束

    Args:
        A_list: 状态转移矩阵序列
        B_list: 输入矩阵序列
        C_list: 输出矩阵序列
        Q: 状态权重
        R: 输入权重
        Rd: 输入变化率权重
        P: 终端权重
        x0: 当前状态
        x_ref: 参考轨迹
        u_prev: 上一时刻输入
        Np: 预测时域
        Nc: 控制时域

    Returns:
        (H_qp, f_qp) QP 矩阵
    """
    n = A_list[0].shape[0]
    m = B_list[0].shape[1]
    p = C_list[0].shape[0]

    # 构建预测矩阵
    # X = Psi * x0 + Theta * U
    Psi = np.zeros((Np * n, n))
    Theta = np.zeros((Np * n, Nc * m))

    # 计算 Psi 和 Theta
    Ak = np.eye(n)
    for i in range(Np):
        Psi[i * n:(i + 1) * n, :] = Ak
        A = A_list[min(i, len(A_list) - 1)]
        Ak = Ak @ A

    for i in range(Np):
        A = A_list[min(i, len(A_list) - 1)]
        for j in range(min(i + 1, Nc)):
            # 计算 A^(i-j) * B_j
            AB = np.eye(n)
            for k in range(j, i):
                AB = A_list[min(k, len(A_list) - 1)] @ AB
            B = B_list[min(j, len(B_list) - 1)]
            Theta[i * n:(i + 1) * n, j * m:(j + 1) * m] = AB @ B

    # 输出预测矩阵
    # Y = C_diag * X = C_diag * (Psi * x0 + Theta * U)
    C_diag = np.zeros((Np * p, Np * n))
    for i in range(Np):
        C = C_list[min(i, len(C_list) - 1)]
        C_diag[i * p:(i + 1) * p, i * n:(i + 1) * n] = C

    Y_Psi = C_diag @ Psi
    Y_Theta = C_diag @ Theta

    # 构建权重矩阵
    Q_bar = np.zeros((Np * p, Np * p))
    R_bar = np.zeros((Nc * m, Nc * m))
    Rd_bar = np.zeros((Nc * m, Nc * m))

    for i in range(Np):
        Q_i = Q[:p, :p] if Q.shape[0] > p else Q
        if i == Np - 1:
            P_i = P[:p, :p] if P.shape[0] > p else P
            Q_bar[i * p:(i + 1) * p, i * p:(i + 1) * p] = Q_i + P_i
        else:
            Q_bar[i * p:(i + 1) * p, i * p:(i + 1) * p] = Q_i

    for i in range(Nc):
        R_bar[i * m:(i + 1) * m, i * m:(i + 1) * m] = R

    # 输入变化率权重
    for i in range(Nc):
        Rd_bar[i * m:(i + 1) * m, i * m:(i + 1) * m] = Rd
        if i > 0:
            Rd_bar[i * m:(i + 1) * m, (i - 1) * m:i * m] = -Rd
            Rd_bar[(i - 1) * m:i * m, i * m:(i + 1) * m] = -Rd

    # QP 矩阵
    H_qp = Y_Theta.T @ Q_bar @ Y_Theta + R_bar + Rd_bar

    # 参考向量
    if x_ref.ndim == 1:
        x_ref_vec = np.tile(x_ref, Np)
    else:
        x_ref_vec = x_ref.flatten()[:Np * p]
        if len(x_ref_vec) < Np * p:
            x_ref_vec = np.tile(x_ref_vec[-p:], Np)[:Np * p]

    # 自由响应
    y_free = Y_Psi @ x0

    # 线性项
    f_qp = Y_Theta.T @ Q_bar @ (y_free - x_ref_vec)

    # 输入变化率的线性项（考虑 u_prev）
    if u_prev is not None:
        du_prev = u_prev
        f_qp[:m] += Rd @ du_prev

    return H_qp, f_qp
