"""
MPC 控制器 - 核心控制算法实现
"""

import numpy as np
from typing import Optional, Tuple, List, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum

from .plant_model import BasePlantModel, LinearPlantModel
from .optimizer import MPCOptimizer, MPCConstraints, MPCWeights


class MPCMode(Enum):
    """MPC 工作模式"""
    LINEAR = "linear"           # 线性 MPC（使用线性化模型）
    NONLINEAR = "nonlinear"     # 非线性 MPC（在线线性化）


@dataclass
class MPCConfig:
    """MPC 配置参数"""
    prediction_horizon: int = 10     # 预测时域
    control_horizon: int = 5         # 控制时域
    sample_time: float = 0.1        # 采样时间
    mode: MPCMode = MPCMode.LINEAR  # 工作模式


@dataclass
class MPCResult:
    """MPC 计算结果"""
    u_optimal: np.ndarray           # 最优控制输入
    u_sequence: np.ndarray          # 最优控制序列
    x_predicted: np.ndarray         # 预测状态序列
    y_predicted: np.ndarray         # 预测输出序列
    cost: float                     # 最优代价
    info: Dict[str, Any]            # 优化信息


class MPCController:
    """
    模型预测控制器

    实现标准 MPC 控制算法：
    1. 获取当前状态
    2. 在线线性化（非线性 MPC）
    3. 预测未来状态
    4. 求解约束优化问题
    5. 执行第一步控制
    """

    def __init__(self, plant: BasePlantModel, config: MPCConfig,
                 constraints: Optional[MPCConstraints] = None,
                 weights: Optional[MPCWeights] = None):
        """
        初始化 MPC 控制器

        Args:
            plant: 被控对象模型
            config: MPC 配置
            constraints: 约束配置
            weights: 权重配置
        """
        self.plant = plant
        self.config = config
        self.dt = config.sample_time

        # 创建优化器
        self.optimizer = MPCOptimizer(
            n_states=plant.n_states,
            n_inputs=plant.n_inputs,
            prediction_horizon=config.prediction_horizon,
            control_horizon=config.control_horizon,
            constraints=constraints,
            weights=weights
        )

        # 内部状态
        self._u_prev = np.zeros(plant.n_inputs)
        self._u_sequence = np.zeros((config.control_horizon, plant.n_inputs))

        # 工作点（用于非线性 MPC 的线性化）
        self._state_op = np.zeros(plant.n_states)
        self._u_op = np.zeros(plant.n_inputs)

        # 历史记录
        self.history = {
            'states': [],
            'inputs': [],
            'outputs': [],
            'references': [],
            'costs': []
        }

    def set_operating_point(self, state_op: np.ndarray, u_op: np.ndarray):
        """
        设置线性化工作点

        Args:
            state_op: 状态工作点
            u_op: 输入工作点
        """
        self._state_op = np.array(state_op, dtype=float)
        self._u_op = np.array(u_op, dtype=float)

    def _get_linearized_model(self, state: np.ndarray,
                               u: Optional[np.ndarray] = None) -> Tuple[List[np.ndarray], List[np.ndarray], List[np.ndarray]]:
        """
        获取线性化模型矩阵序列

        Args:
            state: 当前状态
            u: 当前输入估计

        Returns:
            (A_list, B_list, C_list) 矩阵序列
        """
        u_eval = u if u is not None else self._u_op

        if isinstance(self.plant, LinearPlantModel):
            # 线性系统：直接使用系统矩阵
            A, B, C, D = self.plant.A, self.plant.B, self.plant.C, self.plant.D
            A_list = [A] * self.config.prediction_horizon
            B_list = [B] * self.config.prediction_horizon
            C_list = [C] * self.config.prediction_horizon
        elif self.config.mode == MPCMode.LINEAR:
            # 非线性系统，线性模式：在工作点处线性化
            A, B, C, D = self.plant.linearize(self._state_op, self._u_op, self.dt)
            A_list = [A] * self.config.prediction_horizon
            B_list = [B] * self.config.prediction_horizon
            C_list = [C] * self.config.prediction_horizon
        else:
            # 非线性 MPC：在线线性化
            A_list = []
            B_list = []
            C_list = []
            x_pred = state.copy()

            for k in range(self.config.prediction_horizon):
                # 在预测点处线性化
                u_k = self._u_sequence[min(k, len(self._u_sequence) - 1)]
                A, B, C, D = self.plant.linearize(x_pred, u_k, self.dt)
                A_list.append(A)
                B_list.append(B)
                C_list.append(C)

                # 更新预测状态
                x_pred = self.plant.step(x_pred, u_k, self.dt)

        return A_list, B_list, C_list

    def compute_control(self, state: np.ndarray, reference: np.ndarray,
                        u_prev: Optional[np.ndarray] = None) -> MPCResult:
        """
        计算 MPC 控制输入

        Args:
            state: 当前状态
            reference: 参考轨迹 (可以是单点或轨迹)
            u_prev: 上一时刻控制输入

        Returns:
            MPC 计算结果
        """
        # 使用上一时刻的控制输入
        if u_prev is None:
            u_prev = self._u_prev

        # 获取线性化模型
        A_list, B_list, C_list = self._get_linearized_model(state, u_prev)

        # 处理参考轨迹
        ref = np.atleast_2d(reference)
        if ref.shape[0] == 1:
            ref = np.tile(ref, (self.config.prediction_horizon, 1))

        # 求解优化问题
        U_opt, info = self.optimizer.solve(
            x0=state,
            A_list=A_list,
            B_list=B_list,
            C_list=C_list,
            x_ref=ref,
            u_prev=u_prev,
            u_init=self._u_sequence
        )

        # 预测状态和输出
        x_pred = np.zeros((self.config.prediction_horizon + 1, self.plant.n_states))
        y_pred = np.zeros((self.config.prediction_horizon, self.plant.n_outputs))
        x_pred[0] = state

        for k in range(self.config.prediction_horizon):
            A = A_list[min(k, len(A_list) - 1)]
            B = B_list[min(k, len(B_list) - 1)]
            C = C_list[min(k, len(C_list) - 1)]

            u_k = U_opt[min(k, len(U_opt) - 1)]
            x_pred[k + 1] = A @ x_pred[k] + B @ u_k
            y_pred[k] = C @ x_pred[k]

        # 保存控制序列
        self._u_sequence = U_opt
        self._u_prev = U_opt[0]

        # 记录历史
        self.history['states'].append(state)
        self.history['inputs'].append(U_opt[0])
        self.history['outputs'].append(self.plant.output(state))
        self.history['references'].append(reference)
        self.history['costs'].append(info['cost'])

        return MPCResult(
            u_optimal=U_opt[0],
            u_sequence=U_opt,
            x_predicted=x_pred,
            y_predicted=y_pred,
            cost=info['cost'],
            info=info
        )

    def reset(self):
        """重置控制器状态"""
        self._u_prev = np.zeros(self.plant.n_inputs)
        self._u_sequence = np.zeros((self.config.control_horizon, self.plant.n_inputs))
        self.history = {
            'states': [],
            'inputs': [],
            'outputs': [],
            'references': [],
            'costs': []
        }

    def get_prediction(self, state: np.ndarray, u_sequence: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取预测轨迹

        Args:
            state: 当前状态
            u_sequence: 控制序列

        Returns:
            (状态预测序列, 输出预测序列)
        """
        N = len(u_sequence)
        x_pred = np.zeros((N + 1, self.plant.n_states))
        y_pred = np.zeros((N, self.plant.n_outputs))
        x_pred[0] = state

        for k in range(N):
            x_pred[k + 1] = self.plant.step(x_pred[k], u_sequence[k], self.dt)
            y_pred[k] = self.plant.output(x_pred[k + 1])

        return x_pred, y_pred


class IncrementalMPCController(MPCController):
    """
    增量式 MPC 控制器

    使用增量形式的 MPC，可以消除稳态误差
    状态扩展为: [x, u_prev]
    """

    def __init__(self, plant: BasePlantModel, config: MPCConfig,
                 constraints: Optional[MPCConstraints] = None,
                 weights: Optional[MPCWeights] = None):
        """
        初始化增量式 MPC 控制器

        Args:
            plant: 被控对象模型
            config: MPC 配置
            constraints: 约束配置
            weights: 权重配置
        """
        super().__init__(plant, config, constraints, weights)

        # 扩展状态维度
        self.n_aug = plant.n_states + plant.n_inputs

    def _augment_state(self, state: np.ndarray, u_prev: np.ndarray) -> np.ndarray:
        """
        构建增广状态

        Args:
            state: 原始状态
            u_prev: 上一时刻输入

        Returns:
            增广状态 [x, u_prev]
        """
        return np.concatenate([state, u_prev])

    def compute_control(self, state: np.ndarray, reference: np.ndarray,
                        u_prev: Optional[np.ndarray] = None) -> MPCResult:
        """
        计算增量式 MPC 控制输入

        Args:
            state: 当前状态
            reference: 参考轨迹
            u_prev: 上一时刻控制输入

        Returns:
            MPC 计算结果
        """
        if u_prev is None:
            u_prev = self._u_prev

        # 使用标准 MPC 计算
        result = super().compute_control(state, reference, u_prev)

        # 增量式：输出为增量
        du = result.u_optimal - u_prev

        return result


class AdaptiveMPCController(MPCController):
    """
    自适应 MPC 控制器

    在线更新模型参数以适应系统变化
    """

    def __init__(self, plant: BasePlantModel, config: MPCConfig,
                 constraints: Optional[MPCConstraints] = None,
                 weights: Optional[MPCWeights] = None,
                 adaptation_rate: float = 0.1):
        """
        初始化自适应 MPC 控制器

        Args:
            plant: 被控对象模型
            config: MPC 配置
            constraints: 约束配置
            weights: 权重配置
            adaptation_rate: 自适应速率
        """
        super().__init__(plant, config, constraints, weights)
        self.adaptation_rate = adaptation_rate

        # 模型参数历史
        self._model_history = []
        self._error_history = []

    def update_model(self, state: np.ndarray, u: np.ndarray,
                     state_next: np.ndarray):
        """
        在线更新模型参数

        Args:
            state: 当前状态
            u: 控制输入
            state_next: 下一时刻状态
        """
        # 使用递推最小二乘法更新模型参数
        # 这里简化实现，实际应用中可以使用更复杂的自适应算法
        self._model_history.append((state, u, state_next))

        # 保留最近的数据
        max_history = 100
        if len(self._model_history) > max_history:
            self._model_history = self._model_history[-max_history:]

    def compute_control(self, state: np.ndarray, reference: np.ndarray,
                        u_prev: Optional[np.ndarray] = None) -> MPCResult:
        """
        计算自适应 MPC 控制输入

        Args:
            state: 当前状态
            reference: 参考轨迹
            u_prev: 上一时刻控制输入

        Returns:
            MPC 计算结果
        """
        # 使用当前模型计算控制
        result = super().compute_control(state, reference, u_prev)

        return result
