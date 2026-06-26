"""
管道流动计算 - Darcy-Weisbach 方法 (Pipe Flow Calculations)

Darcy-Weisbach 方程用于计算管道中的沿程水头损失：

    h_f = f × (L/D) × (v²/(2g))

其中：
    h_f = 沿程水头损失 (m)
    f   = 达西摩擦系数 (无量纲)
    L   = 管道长度 (m)
    D   = 管道内径 (m)
    v   = 平均流速 (m/s)
    g   = 重力加速度 (m/s²)

摩擦系数 f 通过 Colebrook 方程或 Moody 图确定。
"""

import numpy as np
from scipy.optimize import fsolve


def colebrook_friction_factor(reynolds: float, roughness: float,
                              diameter: float) -> float:
    """使用 Colebrook 方程计算摩擦系数

    Colebrook 方程（隐式方程）：
        1/√f = -2 log₁₀[(ε/D)/3.7 + 2.51/(Re√f)]

    其中：
        ε = 管道绝对粗糙度 (m)
        D = 管道直径 (m)
        Re = Reynolds 数

    使用 Newton-Raphson 方法求解。

    Args:
        reynolds: Reynolds 数
        roughness: 管道绝对粗糙度 (m)
        diameter: 管道直径 (m)

    Returns:
        达西摩擦系数 f
    """
    relative_roughness = roughness / diameter

    def colebrook_eq(f):
        if f <= 0:
            return 1.0 / np.sqrt(f) + 2.0 * np.log10(relative_roughness / 3.7 + 2.51 / reynolds / np.sqrt(f))
        return 1.0 / np.sqrt(f) + 2.0 * np.log10(relative_roughness / 3.7 + 2.51 / reynolds / np.sqrt(f))

    # 初始猜测值（Swamee-Jain 近似）
    f_guess = 0.25 / (np.log10(relative_roughness / 3.7 + 5.74 / reynolds**0.9))**2

    if f_guess <= 0:
        f_guess = 0.02  # 默认值

    f_solution = fsolve(colebrook_eq, f_guess)[0]

    if f_solution <= 0:
        return 0.02  # 安全默认值

    return f_solution


def swamee_jain_friction_factor(reynolds: float, roughness: float,
                                diameter: float) -> float:
    """使用 Swamee-Jain 显式公式计算摩擦系数

    f = 0.25 / [log₁₀((ε/D)/3.7 + 5.74/Re^0.9)]²

    适用于：Re > 4000 和 10⁻⁶ < ε/D < 10⁻²

    Args:
        reynolds: Reynolds 数
        roughness: 管道绝对粗糙度 (m)
        diameter: 管道直径 (m)

    Returns:
        达西摩擦系数 f
    """
    relative_roughness = roughness / diameter
    term = relative_roughness / 3.7 + 5.74 / reynolds**0.9
    f = 0.25 / (np.log10(term))**2
    return max(f, 0.008)  # 物理下限


def laminar_friction_factor(reynolds: float) -> float:
    """层流摩擦系数计算

    对于层流 (Re < 2300)：
        f = 64 / Re

    Args:
        reynolds: Reynolds 数

    Returns:
        达西摩擦系数 f
    """
    return 64.0 / reynolds


def darcy_weisbach_head_loss(length: float, diameter: float, velocity: float,
                             reynolds: float, roughness: float = 0.0,
                             gravity: float = 9.81) -> float:
    """计算沿程水头损失 (Darcy-Weisbach 方程)

    h_f = f × (L/D) × (v²/(2g))

    Args:
        length: 管道长度 (m)
        diameter: 管道内径 (m)
        velocity: 平均流速 (m/s)
        reynolds: Reynolds 数
        roughness: 管道绝对粗糙度 (m), 默认光滑管
        gravity: 重力加速度 (m/s²)

    Returns:
        沿程水头损失 (m)
    """
    if reynolds < 2300:
        f = laminar_friction_factor(reynolds)
    else:
        f = swamee_jain_friction_factor(reynolds, roughness, diameter)

    head_loss = f * (length / diameter) * (velocity**2 / (2 * gravity))
    return head_loss


def darcy_weisbach_pressure_drop(length: float, diameter: float, velocity: float,
                                 reynolds: float, density: float,
                                 roughness: float = 0.0,
                                 gravity: float = 9.81) -> float:
    """计算沿程压力降

    ΔP = ρgh_f = f × (L/D) × (ρv²/2)

    Args:
        length: 管道长度 (m)
        diameter: 管道内径 (m)
        velocity: 平均流速 (m/s)
        reynolds: Reynolds 数
        density: 流体密度 (kg/m³)
        roughness: 管道绝对粗糙度 (m)
        gravity: 重力加速度 (m/s²)

    Returns:
        压力降 (Pa)
    """
    head_loss = darcy_weisbach_head_loss(length, diameter, velocity,
                                         reynolds, roughness, gravity)
    return density * gravity * head_loss


def flow_rate(diameter: float, velocity: float) -> float:
    """计算体积流量

    Q = A × v = π(D/2)² × v

    Args:
        diameter: 管道内径 (m)
        velocity: 平均流速 (m/s)

    Returns:
        体积流量 (m³/s)
    """
    area = np.pi * (diameter / 2)**2
    return area * velocity


def average_velocity(flow_rate: float, diameter: float) -> float:
    """根据流量和管径计算平均流速

    v = Q / A = 4Q/(πD²)

    Args:
        flow_rate: 体积流量 (m³/s)
        diameter: 管道内径 (m)

    Returns:
        平均流速 (m/s)
    """
    area = np.pi * (diameter / 2)**2
    return flow_rate / area


class PipeSegment:
    """管道段类

    表示一段具有特定几何和表面特性的管道。
    """

    # 常见管道材料的粗糙度 (m)
    ROUGHNESS = {
        "drawn_tube": 1.5e-6,       # 拉制管
        "commercial_steel": 4.6e-5,  # 商用钢管
        "wrought_iron": 6.1e-5,      # 锻铁管
        "galvanized_iron": 1.5e-4,   # 镀锌铁管
        "cast_iron": 2.6e-4,         # 铸铁管
        "concrete": 3.0e-3,          # 混凝土管
        "wood_plank": 1.8e-3,        # 木板管道
        "riveted_steel": 9.0e-3,     # 铆接钢管
    }

    def __init__(self, diameter: float, length: float, material: str = "commercial_steel",
                 roughness: float = None, fluid_density: float = 1000.0,
                 fluid_viscosity: float = 1.002e-3):
        """初始化管道段

        Args:
            diameter: 管道内径 (m)
            length: 管道长度 (m)
            material: 管道材料类型
            roughness: 自定义粗糙度 (m), 覆盖 material
            fluid_density: 流体密度 (kg/m³)
            fluid_viscosity: 流体动力粘度 (Pa·s), 水在 20°C ≈ 1.002e-3
        """
        self.diameter = diameter
        self.length = length
        self.material = material
        self.roughness = roughness if roughness is not None else self.ROUGHNESS.get(material, 0.0)
        self.fluid_density = fluid_density
        self.fluid_viscosity = fluid_viscosity
        self.cross_sectional_area = np.pi * (diameter / 2)**2
        self.perimeter = np.pi * diameter

    def reynolds_number(self, velocity: float) -> float:
        """计算 Reynolds 数

        Re = ρvD/μ = vD/ν

        Args:
            velocity: 流速 (m/s)

        Returns:
            Reynolds 数
        """
        return self.fluid_density * velocity * self.diameter / self.fluid_viscosity

    def flow_regime(self, velocity: float) -> str:
        """判断流动状态

        Args:
            velocity: 流速 (m/s)

        Returns:
            流动状态: "层流" (laminar), "过渡流" (transitional), "湍流" (turbulent)
        """
        re = self.reynolds_number(velocity)
        if re < 2300:
            return "层流 (Laminar)"
        elif re < 4000:
            return "过渡流 (Transitional)"
        else:
            return "湍流 (Turbulent)"

    def friction_factor(self, velocity: float) -> float:
        """计算摩擦系数

        Args:
            velocity: 流速 (m/s)

        Returns:
            达西摩擦系数 f
        """
        re = self.reynolds_number(velocity)
        if re < 2300:
            return laminar_friction_factor(re)
        else:
            return swamee_jain_friction_factor(re, self.roughness, self.diameter)

    def head_loss(self, velocity: float, gravity: float = 9.81) -> float:
        """计算沿程水头损失

        Args:
            velocity: 流速 (m/s)
            gravity: 重力加速度 (m/s²)

        Returns:
            沿程水头损失 (m)
        """
        re = self.reynolds_number(velocity)
        return darcy_weisbach_head_loss(self.length, self.diameter, velocity,
                                        re, self.roughness, gravity)

    def pressure_drop(self, velocity: float, gravity: float = 9.81) -> float:
        """计算压力降

        Args:
            velocity: 流速 (m/s)
            gravity: 重力加速度 (m/s²)

        Returns:
            压力降 (Pa)
        """
        return self.fluid_density * gravity * self.head_loss(velocity, gravity)

    def flow_rate(self, velocity: float) -> float:
        """计算体积流量

        Args:
            velocity: 流速 (m/s)

        Returns:
            体积流量 (m³/s)
        """
        return flow_rate(self.diameter, velocity)

    def velocity_from_flow(self, flow: float) -> float:
        """根据流量计算流速

        Args:
            flow: 体积流量 (m³/s)

        Returns:
            流速 (m/s)
        """
        return average_velocity(flow, self.diameter)


class PipeNetwork:
    """管道网络类

    用于分析串联和并联管道网络。
    """

    def __init__(self):
        self.segments = []
        self.junctions = []

    def add_segment(self, segment: PipeSegment):
        """添加管道段到网络

        Args:
            segment: PipeSegment 实例
        """
        self.segments.append(segment)

    def compute_series(self) -> dict:
        """计算串联管道网络

        串联管道特性：
            - 流量恒定: Q₁ = Q₂ = Q₃ = ...
            - 总水头损失: h_total = h₁ + h₂ + h₃ + ...

        Returns:
            计算结果字典
        """
        total_head_loss = 0
        total_length = 0
        results = []

        for i, seg in enumerate(self.segments):
            # 假设入口流量
            velocity = seg.velocity_from_flow(0.01)  # 默认 0.01 m³/s
            re = seg.reynolds_number(velocity)
            head_loss = seg.head_loss(velocity)
            pressure_drop = seg.pressure_drop(velocity)

            results.append({
                "segment_index": i,
                "diameter": seg.diameter,
                "length": seg.length,
                "material": seg.material,
                "velocity": velocity,
                "reynolds": re,
                "flow_regime": seg.flow_regime(velocity),
                "friction_factor": seg.friction_factor(velocity),
                "head_loss": head_loss,
                "pressure_drop": pressure_drop,
                "flow_rate": seg.flow_rate(velocity),
            })
            total_head_loss += head_loss
            total_length += seg.length

        return {
            "total_head_loss": total_head_loss,
            "total_length": total_length,
            "flow_rate": 0.01,
            "segments": results,
        }

    def compute_parallel(self) -> dict:
        """计算并联管道网络

        并联管道特性：
            - 水头损失相等: h₁ = h₂ = h₃ = ...
            - 总流量: Q_total = Q₁ + Q₂ + Q₃ + ...

        简化计算：假设各支路按阻力分配流量

        Returns:
            计算结果字典
        """
        if len(self.segments) < 2:
            raise ValueError("并联网络至少需要2条管道")

        total_flow = 0.01  # 总流量 0.01 m³/s
        results = []

        # 计算各支路的导流系数 (1/√R, 其中 R 为阻力)
        conductances = []
        for seg in self.segments:
            re = seg.reynolds_number(1.0)
            f = seg.friction_factor(1.0)
            resistance = f * seg.length / seg.diameter
            conductances.append(1.0 / np.sqrt(resistance))

        total_conductance = sum(conductances)

        for i, seg in enumerate(self.segments):
            flow_fraction = conductances[i] / total_conductance
            flow = total_flow * flow_fraction
            velocity = seg.velocity_from_flow(flow)
            re = seg.reynolds_number(velocity)
            head_loss = seg.head_loss(velocity)
            pressure_drop = seg.pressure_drop(velocity)

            results.append({
                "segment_index": i,
                "diameter": seg.diameter,
                "length": seg.length,
                "flow": flow,
                "velocity": velocity,
                "reynolds": re,
                "flow_regime": seg.flow_regime(velocity),
                "head_loss": head_loss,
                "pressure_drop": pressure_drop,
            })
            total_flow += 0  # already accounted

        return {
            "total_flow": total_flow,
            "branches": results,
        }
