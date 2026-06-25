"""
Kalman Filter for Object Tracking

卡尔曼滤波器实现，用于目标跟踪中的状态估计和预测。

核心原理:
- 状态预测: 根据运动模型预测下一时刻的状态
- 状态更新: 结合观测值修正预测结果
- 协方差传播: 跟踪估计的不确定性

状态向量: [x, y, vx, vy] (位置和速度)
观测向量: [x, y] (位置)
"""

import numpy as np
from typing import Tuple, Optional


class KalmanFilter:
    """标准卡尔曼滤波器

    用于线性运动模型的目标跟踪。
    状态向量包含位置和速度，观测值为位置。
    """

    def __init__(
        self,
        dt: float = 1.0,
        process_noise: float = 1e-3,
        measurement_noise: float = 1e-1
    ):
        """初始化卡尔曼滤波器

        Args:
            dt: 时间步长
            process_noise: 过程噪声方差
            measurement_noise: 测量噪声方差
        """
        self.dt = dt

        # 状态转移矩阵 F
        # [x']   [1 0 dt 0] [x]
        # [y'] = [0 1 0 dt] [y]
        # [vx']  [0 0 1  0] [vx]
        # [vy']  [0 0 0  1] [vy]
        self.F = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1,  0],
            [0, 0, 0,  1]
        ], dtype=np.float64)

        # 观测矩阵 H (只观测位置)
        # [zx] = [1 0 0 0] [x]
        # [zy]   [0 1 0 0] [y]
        #                   [vx]
        #                   [vy]
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=np.float64)

        # 过程噪声协方差 Q
        self.Q = self._build_process_noise(process_noise)

        # 测量噪声协方差 R
        self.R = np.eye(2) * measurement_noise

        # 状态向量 [x, y, vx, vy]
        self.x = np.zeros(4, dtype=np.float64)

        # 状态协方差矩阵 P
        self.P = np.eye(4) * 100  # 初始不确定性较大

        # 卡尔曼增益
        self.K = np.zeros((4, 2), dtype=np.float64)

    def _build_process_noise(self, q: float) -> np.ndarray:
        """构建过程噪声协方差矩阵

        使用离散白噪声加速度模型。

        Args:
            q: 过程噪声强度

        Returns:
            过程噪声协方差矩阵
        """
        dt = self.dt
        Q = np.array([
            [dt**4/4, 0,        dt**3/2, 0       ],
            [0,        dt**4/4, 0,        dt**3/2 ],
            [dt**3/2,  0,        dt**2,   0       ],
            [0,        dt**3/2, 0,        dt**2   ]
        ], dtype=np.float64) * q
        return Q

    def predict(self) -> np.ndarray:
        """预测步骤

        根据运动模型预测下一时刻的状态。

        Returns:
            预测的状态向量
        """
        # 状态预测: x' = F * x
        self.x = self.F @ self.x

        # 协方差预测: P' = F * P * F^T + Q
        self.P = self.F @ self.P @ self.F.T + self.Q

        return self.x.copy()

    def update(self, measurement: np.ndarray) -> np.ndarray:
        """更新步骤

        结合测量值修正预测状态。

        Args:
            measurement: 测量向量 [x, y]

        Returns:
            更新后的状态向量
        """
        # 计算卡尔曼增益: K = P * H^T * (H * P * H^T + R)^-1
        S = self.H @ self.P @ self.H.T + self.R
        self.K = self.P @ self.H.T @ np.linalg.inv(S)

        # 状态更新: x = x + K * (z - H * x)
        y = measurement - self.H @ self.x  # 残差
        self.x = self.x + self.K @ y

        # 协方差更新: P = (I - K * H) * P
        I = np.eye(4)
        self.P = (I - self.K @ self.H) @ self.P

        return self.x.copy()

    def get_state(self) -> Tuple[float, float, float, float]:
        """获取当前状态

        Returns:
            (x, y, vx, vy) 位置和速度
        """
        return tuple(self.x)

    def get_position(self) -> Tuple[float, float]:
        """获取当前位置

        Returns:
            (x, y) 位置坐标
        """
        return (self.x[0], self.x[1])

    def get_velocity(self) -> Tuple[float, float]:
        """获取当前速度

        Returns:
            (vx, vy) 速度分量
        """
        return (self.x[2], self.x[3])

    def get_position_uncertainty(self) -> Tuple[float, float]:
        """获取位置不确定性

        Returns:
            (std_x, std_y) 位置标准差
        """
        return (np.sqrt(self.P[0, 0]), np.sqrt(self.P[1, 1]))

    def set_state(self, x: float, y: float, vx: float = 0, vy: float = 0):
        """设置初始状态

        Args:
            x: 初始x坐标
            y: 初始y坐标
            vx: 初始x速度
            vy: 初始y速度
        """
        self.x = np.array([x, y, vx, vy], dtype=np.float64)

    def reset(self, x: float = 0, y: float = 0, vx: float = 0, vy: float = 0):
        """重置滤波器

        Args:
            x: 初始x坐标
            y: 初始y坐标
            vx: 初始x速度
            vy: 初始y速度
        """
        self.x = np.array([x, y, vx, vy], dtype=np.float64)
        self.P = np.eye(4) * 100


class AdaptiveKalmanFilter(KalmanFilter):
    """自适应卡尔曼滤波器

    根据残差自动调整测量噪声协方差。
    """

    def __init__(
        self,
        dt: float = 1.0,
        process_noise: float = 1e-3,
        measurement_noise: float = 1e-1,
        window_size: int = 10,
        adaptation_rate: float = 0.1
    ):
        """初始化自适应卡尔曼滤波器

        Args:
            dt: 时间步长
            process_noise: 过程噪声方差
            measurement_noise: 初始测量噪声方差
            window_size: 残差窗口大小
            adaptation_rate: 自适应速率
        """
        super().__init__(dt, process_noise, measurement_noise)
        self.window_size = window_size
        self.adaptation_rate = adaptation_rate
        self.residuals = []

    def update(self, measurement: np.ndarray) -> np.ndarray:
        """自适应更新

        Args:
            measurement: 测量向量 [x, y]

        Returns:
            更新后的状态向量
        """
        # 计算预测残差
        predicted_measurement = self.H @ self.x
        residual = measurement - predicted_measurement

        # 存储残差
        self.residuals.append(residual)
        if len(self.residuals) > self.window_size:
            self.residuals.pop(0)

        # 自适应调整测量噪声
        if len(self.residuals) >= 3:
            residuals_array = np.array(self.residuals)
            empirical_cov = np.cov(residuals_array.T)
            innovation_cov = self.H @ self.P @ self.H.T

            # 平滑更新 R
            target_R = empirical_cov - innovation_cov
            target_R = np.maximum(target_R, self.R * 0.1)  # 下限
            self.R = (1 - self.adaptation_rate) * self.R + \
                     self.adaptation_rate * target_R

        return super().update(measurement)


if __name__ == "__main__":
    # 简单演示
    kf = KalmanFilter(dt=1.0)

    # 模拟匀速运动目标
    true_positions = [(100 + 5*i, 200 + 3*i) for i in range(20)]

    # 添加观测噪声
    np.random.seed(42)
    measurements = [
        (x + np.random.randn() * 2, y + np.random.randn() * 2)
        for x, y in true_positions
    ]

    # 初始化
    kf.set_state(measurements[0][0], measurements[0][1], 5, 3)

    print("卡尔曼滤波演示:")
    print(f"{'步骤':>4} {'真实位置':>16} {'测量位置':>16} {'滤波位置':>16} {'预测位置':>16}")
    print("-" * 80)

    for i, (true_pos, meas) in enumerate(zip(true_positions, measurements)):
        # 预测
        kf.predict()
        pred_pos = kf.get_position()

        # 更新
        kf.update(np.array(meas))
        filtered_pos = kf.get_position()

        if i % 3 == 0:
            print(f"{i:4d} ({true_pos[0]:6.1f},{true_pos[1]:6.1f}) "
                  f"({meas[0]:6.1f},{meas[1]:6.1f}) "
                  f"({filtered_pos[0]:6.1f},{filtered_pos[1]:6.1f}) "
                  f"({pred_pos[0]:6.1f},{pred_pos[1]:6.1f})")
