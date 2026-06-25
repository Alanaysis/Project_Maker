"""
MPC 仿真环境 - 实现系统仿真和可视化
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple, List, Dict, Any, Callable
from dataclasses import dataclass

from .plant_model import BasePlantModel
from .mpc_controller import MPCController, MPCConfig


@dataclass
class SimulationConfig:
    """仿真配置"""
    total_time: float = 10.0        # 总仿真时间 (s)
    sample_time: float = 0.1        # 采样时间 (s)
    noise_std: float = 0.0          # 过程噪声标准差
    measurement_noise_std: float = 0.0  # 测量噪声标准差


@dataclass
class SimulationResult:
    """仿真结果"""
    time: np.ndarray                # 时间序列
    states: np.ndarray              # 状态序列
    inputs: np.ndarray              # 输入序列
    outputs: np.ndarray             # 输出序列
    references: np.ndarray          # 参考序列
    costs: np.ndarray               # 代价序列
    info: Dict[str, Any]            # 附加信息


class MPCSimulation:
    """
    MPC 仿真环境

    提供完整的 MPC 控制系统仿真功能
    """

    def __init__(self, plant: BasePlantModel, controller: MPCController,
                 sim_config: Optional[SimulationConfig] = None):
        """
        初始化仿真环境

        Args:
            plant: 被控对象
            controller: MPC 控制器
            sim_config: 仿真配置
        """
        self.plant = plant
        self.controller = controller
        self.config = sim_config if sim_config is not None else SimulationConfig()

        # 仿真状态
        self._time = 0.0
        self._state = None
        self._is_running = False

    def _generate_reference(self, t: float, reference_fn: Callable) -> np.ndarray:
        """
        生成参考信号

        Args:
            t: 当前时间
            reference_fn: 参考信号生成函数

        Returns:
            参考值
        """
        return reference_fn(t)

    def _add_noise(self, value: np.ndarray, std: float) -> np.ndarray:
        """
        添加噪声

        Args:
            value: 原始值
            std: 噪声标准差

        Returns:
            添加噪声后的值
        """
        if std > 0:
            return value + np.random.randn(*value.shape) * std
        return value

    def run(self, x0: np.ndarray,
            reference_fn: Callable[[float], np.ndarray],
            u_prev: Optional[np.ndarray] = None) -> SimulationResult:
        """
        运行仿真

        Args:
            x0: 初始状态
            reference_fn: 参考信号生成函数 f(t) -> reference
            u_prev: 初始控制输入

        Returns:
            仿真结果
        """
        # 初始化
        N = int(self.config.total_time / self.config.sample_time)
        dt = self.config.sample_time

        # 预分配数组
        time_arr = np.zeros(N + 1)
        states = np.zeros((N + 1, self.plant.n_states))
        inputs = np.zeros((N, self.plant.n_inputs))
        outputs = np.zeros((N, self.plant.n_outputs))
        references = np.zeros((N, self.plant.n_outputs))
        costs = np.zeros(N)

        # 初始状态
        states[0] = x0
        current_state = x0.copy()

        # 重置控制器
        self.controller.reset()

        # 仿真主循环
        for k in range(N):
            t = k * dt
            time_arr[k] = t

            # 生成参考信号
            ref = self._generate_reference(t, reference_fn)
            references[k] = ref

            # 获取带噪声的测量状态
            measured_state = self._add_noise(current_state, self.config.measurement_noise_std)

            # MPC 计算控制输入
            result = self.controller.compute_control(
                state=measured_state,
                reference=ref,
                u_prev=u_prev
            )

            # 应用控制输入
            u_applied = result.u_optimal
            inputs[k] = u_applied
            costs[k] = result.cost

            # 系统状态更新
            current_state = self.plant.step(current_state, u_applied, dt)

            # 添加过程噪声
            current_state = self._add_noise(current_state, self.config.noise_std)

            # 记录状态和输出
            states[k + 1] = current_state
            outputs[k] = self.plant.output(current_state)

            # 更新上一时刻输入
            u_prev = u_applied

        # 最后一个时间点
        time_arr[N] = N * dt

        return SimulationResult(
            time=time_arr,
            states=states,
            inputs=inputs,
            outputs=outputs,
            references=references,
            costs=costs,
            info={
                'total_time': self.config.total_time,
                'sample_time': dt,
                'n_steps': N
            }
        )

    def run_step_response(self, x0: np.ndarray,
                          step_value: np.ndarray,
                          step_time: float = 0.0) -> SimulationResult:
        """
        运行阶跃响应仿真

        Args:
            x0: 初始状态
            step_value: 阶跃参考值
            step_time: 阶跃发生时间

        Returns:
            仿真结果
        """
        def step_reference(t):
            if t >= step_time:
                return step_value
            return np.zeros_like(step_value)

        return self.run(x0, step_reference)

    def run_sinusoidal_response(self, x0: np.ndarray,
                                 amplitude: np.ndarray,
                                 frequency: float) -> SimulationResult:
        """
        运行正弦响应仿真

        Args:
            x0: 初始状态
            amplitude: 振幅
            frequency: 频率 (Hz)

        Returns:
            仿真结果
        """
        def sinusoidal_reference(t):
            return amplitude * np.sin(2 * np.pi * frequency * t)

        return self.run(x0, sinusoidal_reference)

    def run_random_reference(self, x0: np.ndarray,
                             ref_range: Tuple[float, float] = (-1.0, 1.0),
                             change_interval: float = 2.0) -> SimulationResult:
        """
        运行随机参考仿真

        Args:
            x0: 初始状态
            ref_range: 参考值范围
            change_interval: 参考值变化间隔

        Returns:
            仿真结果
        """
        current_ref = np.random.uniform(ref_range[0], ref_range[1],
                                         size=self.plant.n_outputs)
        next_change = change_interval

        def random_reference(t):
            nonlocal current_ref, next_change
            if t >= next_change:
                current_ref = np.random.uniform(ref_range[0], ref_range[1],
                                                 size=self.plant.n_outputs)
                next_change += change_interval
            return current_ref

        return self.run(x0, random_reference)


class MPCVisualizer:
    """
    MPC 可视化工具

    提供仿真结果的可视化功能
    """

    @staticmethod
    def plot_simulation_result(result: SimulationResult,
                                state_names: Optional[List[str]] = None,
                                input_names: Optional[List[str]] = None,
                                output_names: Optional[List[str]] = None,
                                title: str = "MPC 仿真结果",
                                save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制仿真结果

        Args:
            result: 仿真结果
            state_names: 状态变量名称
            input_names: 输入变量名称
            output_names: 输出变量名称
            title: 图表标题
            save_path: 保存路径

        Returns:
            matplotlib Figure 对象
        """
        n_states = result.states.shape[1]
        n_inputs = result.inputs.shape[1]
        n_outputs = result.outputs.shape[1]

        # 默认名称
        if state_names is None:
            state_names = [f'状态 {i+1}' for i in range(n_states)]
        if input_names is None:
            input_names = [f'输入 {i+1}' for i in range(n_inputs)]
        if output_names is None:
            output_names = [f'输出 {i+1}' for i in range(n_outputs)]

        # 创建子图
        fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        fig.suptitle(title, fontsize=14)

        # 绘制状态
        ax1 = axes[0]
        for i in range(n_states):
            ax1.plot(result.time, result.states[:, i],
                    label=state_names[i], linewidth=1.5)
        ax1.set_ylabel('状态')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)

        # 绘制输出和参考
        ax2 = axes[1]
        for i in range(n_outputs):
            ax2.plot(result.time[:len(result.outputs)], result.outputs[:, i],
                    label=output_names[i], linewidth=1.5)
            ax2.plot(result.time[:len(result.references)], result.references[:, i],
                    '--', label=f'{output_names[i]} 参考', linewidth=1.0)
        ax2.set_ylabel('输出')
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)

        # 绘制控制输入
        ax3 = axes[2]
        for i in range(n_inputs):
            ax3.step(result.time[:len(result.inputs)], result.inputs[:, i],
                    label=input_names[i], linewidth=1.5, where='post')
        ax3.set_xlabel('时间 (s)')
        ax3.set_ylabel('控制输入')
        ax3.legend(loc='best')
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    @staticmethod
    def plot_cost_history(result: SimulationResult,
                          title: str = "MPC 代价历史",
                          save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制代价历史

        Args:
            result: 仿真结果
            title: 图表标题
            save_path: 保存路径

        Returns:
            matplotlib Figure 对象
        """
        fig, ax = plt.subplots(figsize=(10, 4))

        time = result.time[:len(result.costs)]
        ax.plot(time, result.costs, 'b-', linewidth=1.5)
        ax.set_xlabel('时间 (s)')
        ax.set_ylabel('代价值')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    @staticmethod
    def plot_tracking_error(result: SimulationResult,
                            output_names: Optional[List[str]] = None,
                            title: str = "MPC 跟踪误差",
                            save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制跟踪误差

        Args:
            result: 仿真结果
            output_names: 输出变量名称
            title: 图表标题
            save_path: 保存路径

        Returns:
            matplotlib Figure 对象
        """
        n_outputs = result.outputs.shape[1]

        if output_names is None:
            output_names = [f'输出 {i+1}' for i in range(n_outputs)]

        fig, axes = plt.subplots(n_outputs, 1, figsize=(10, 3 * n_outputs), sharex=True)
        if n_outputs == 1:
            axes = [axes]

        fig.suptitle(title, fontsize=14)

        for i in range(n_outputs):
            error = result.references[:, i] - result.outputs[:, i]
            time = result.time[:len(error)]

            axes[i].plot(time, error, 'r-', linewidth=1.5)
            axes[i].axhline(y=0, color='k', linestyle='-', linewidth=0.5)
            axes[i].set_ylabel(f'{output_names[i]} 误差')
            axes[i].grid(True, alpha=0.3)

        axes[-1].set_xlabel('时间 (s)')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    @staticmethod
    def plot_phase_portrait(result: SimulationResult,
                            state_indices: Tuple[int, int] = (0, 1),
                            title: str = "相平面图",
                            save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制相平面图

        Args:
            result: 仿真结果
            state_indices: 状态索引
            title: 图表标题
            save_path: 保存路径

        Returns:
            matplotlib Figure 对象
        """
        fig, ax = plt.subplots(figsize=(8, 8))

        i, j = state_indices
        ax.plot(result.states[:, i], result.states[:, j], 'b-', linewidth=1.5)
        ax.plot(result.states[0, i], result.states[0, j], 'go', markersize=10, label='起点')
        ax.plot(result.states[-1, i], result.states[-1, j], 'rs', markersize=10, label='终点')

        ax.set_xlabel(f'状态 {i+1}')
        ax.set_ylabel(f'状态 {j+1}')
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig
