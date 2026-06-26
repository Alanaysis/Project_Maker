"""
伯努利方程求解器 (Bernoulli Equation Solver)

伯努利方程是流体力学中的基本方程，描述了沿流线的能量守恒：

    P/ρg + v²/(2g) + z = constant

其中：
    P = 压力 (Pa)
    ρ = 流体密度 (kg/m³)
    g = 重力加速度 (m/s²)
    v = 流速 (m/s)
    z = 高程 (m)

各项分别代表：
    P/ρg     - 压力头 (Pressure Head)
    v²/(2g)  - 速度头 (Velocity Head)
    z        - 高程头 (Elevation Head)
"""

import numpy as np


class BernoulliSolver:
    """伯努利方程求解器

    用于计算沿流线的压力、速度和高度变化。

    使用条件：
        1. 稳态流动
        2. 不可压缩流体
        3. 无粘性效应（理想流体）
        4. 沿同一条流线
    """

    def __init__(self, density: float = 1000.0, gravity: float = 9.81):
        """初始化伯努利求解器

        Args:
            density: 流体密度 (kg/m³), 默认水 1000 kg/m³
            gravity: 重力加速度 (m/s²), 默认 9.81 m/s²
        """
        self.density = density
        self.gravity = gravity

    def solve_for_pressure(self, p1: float, v1: float, z1: float,
                           v2: float, z2: float) -> float:
        """已知点1的参数，求解点2的压力

        伯努利方程变形：
            P₂ = P₁ + ½ρ(v₁² - v₂²) + ρg(z₁ - z₂)

        Args:
            p1: 点1的压力 (Pa)
            v1: 点1的速度 (m/s)
            z1: 点1的高程 (m)
            v2: 点2的速度 (m/s)
            z2: 点2的高程 (m)

        Returns:
            点2的压力 (Pa)
        """
        pressure_head_diff = 0.5 * self.density * (v1**2 - v2**2)
        elevation_head_diff = self.density * self.gravity * (z1 - z2)
        return p1 + pressure_head_diff + elevation_head_diff

    def solve_for_velocity(self, p1: float, v1: float, z1: float,
                           p2: float, z2: float) -> float:
        """已知点1的参数和点2的压力，求解点2的速度

        伯努利方程变形：
            v₂ = √[v₁² + 2(P₁ - P₂)/ρ + 2g(z₁ - z₂)]

        Args:
            p1: 点1的压力 (Pa)
            v1: 点1的速度 (m/s)
            z1: 点1的高程 (m)
            p2: 点2的压力 (Pa)
            z2: 点2的高程 (m)

        Returns:
            点2的速度 (m/s)
        """
        term = v1**2 + 2 * (p1 - p2) / self.density + 2 * self.gravity * (z1 - z2)
        if term < 0:
            raise ValueError(
                f"速度计算中出现负值 ({term})，"
                "请检查输入参数是否物理合理"
            )
        return np.sqrt(term)

    def solve_for_elevation(self, p1: float, v1: float, z1: float,
                            p2: float, v2: float) -> float:
        """已知点1的参数和点2的压力/速度，求解点2的高程

        伯努利方程变形：
            z₂ = z₁ + (P₁ - P₂)/(ρg) + (v₁² - v₂²)/(2g)

        Args:
            p1: 点1的压力 (Pa)
            v1: 点1的速度 (m/s)
            z1: 点1的高程 (m)
            p2: 点2的压力 (Pa)
            v2: 点2的速度 (m/s)

        Returns:
            点2的高程 (m)
        """
        pressure_head = (p1 - p2) / (self.density * self.gravity)
        velocity_head = (v1**2 - v2**2) / (2 * self.gravity)
        return z1 + pressure_head + velocity_head

    def total_head(self, pressure: float, velocity: float, elevation: float) -> float:
        """计算总水头 (Total Head)

        H = P/(ρg) + v²/(2g) + z

        Args:
            pressure: 压力 (Pa)
            velocity: 速度 (m/s)
            elevation: 高程 (m)

        Returns:
            总水头 (m)
        """
        pressure_head = pressure / (self.density * self.gravity)
        velocity_head = velocity**2 / (2 * self.gravity)
        return pressure_head + velocity_head + elevation

    def head_loss_beroulli(self, p1: float, v1: float, z1: float,
                           p2: float, v2: float, z2: float) -> float:
        """计算实际流体中的水头损失（扩展伯努利方程）

        对于实际流体，加入水头损失项：
            H₁ = H₂ + h_loss

        其中 h_loss = H₁ - H₂

        Args:
            p1: 点1的压力 (Pa)
            v1: 点1的速度 (m/s)
            z1: 点1的高程 (m)
            p2: 点2的压力 (Pa)
            v2: 点2的速度 (m/s)
            z2: 点2的高程 (m)

        Returns:
            水头损失 (m)
        """
        h1 = self.total_head(p1, v1, z1)
        h2 = self.total_head(p2, v2, z2)
        return h1 - h2

    def pressure_coefficient(self, p: float, p_ref: float,
                             v: float, rho: float = None) -> float:
        """计算压力系数 Cₚ

        Cₚ = (P - P_ref) / (½ρv²)

        压力系数用于无量纲化压力分布。

        Args:
            p: 局部压力 (Pa)
            p_ref: 参考压力 (Pa)
            v: 参考速度 (m/s)
            rho: 流体密度 (kg/m³), 默认使用实例密度

        Returns:
            压力系数 (无量纲)
        """
        if rho is None:
            rho = self.density
        dynamic_pressure = 0.5 * rho * v**2
        if dynamic_pressure == 0:
            raise ValueError("动压为零，无法计算压力系数")
        return (p - p_ref) / dynamic_pressure

    def analyze_energy_profile(self, points: list) -> dict:
        """分析沿流线的能量分布

        Args:
            points: 点列表，每个点为 (pressure, velocity, elevation)

        Returns:
            包含各点能量成分的分析结果字典
        """
        results = []
        for p, v, z in points:
            pressure_head = p / (self.density * self.gravity)
            velocity_head = v**2 / (2 * self.gravity)
            total = self.total_head(p, v, z)
            results.append({
                "position": (p, v, z),
                "pressure_head": pressure_head,
                "velocity_head": velocity_head,
                "elevation_head": z,
                "total_head": total,
            })
        return {"energy_profile": results}
