"""
Reynolds 数计算与流动状态分类 (Reynolds Number & Flow Regime)

Reynolds 数是流体力学中最重要的无量纲数之一，用于判断流动状态：

    Re = ρvD/μ = vD/ν

其中：
    ρ = 流体密度 (kg/m³)
    v = 特征速度 (m/s)
    D = 特征长度 (m)
    μ = 动力粘度 (Pa·s)
    ν = 运动粘度 (m²/s)

流动状态判据：
    Re < 2300   → 层流 (Laminar)
    2300 ≤ Re < 4000 → 过渡流 (Transitional)
    Re ≥ 4000   → 湍流 (Turbulent)
"""

import numpy as np


# 常见流体在 20°C 下的物性参数
FLUID_PROPERTIES = {
    "water_20c": {
        "density": 998.2,       # kg/m³
        "viscosity": 1.002e-3,  # Pa·s (动力粘度)
        "kinematic_viscosity": 1.004e-6,  # m²/s (运动粘度)
        "name_cn": "水 (20°C)",
        "name_en": "Water at 20°C",
    },
    "water_80c": {
        "density": 971.8,
        "viscosity": 3.55e-4,
        "kinematic_viscosity": 3.65e-7,
        "name_cn": "水 (80°C)",
        "name_en": "Water at 80°C",
    },
    "air_20c": {
        "density": 1.204,
        "viscosity": 1.825e-5,
        "kinematic_viscosity": 1.516e-5,
        "name_cn": "空气 (20°C)",
        "name_en": "Air at 20°C",
    },
    "oil_sae30": {
        "density": 891.0,
        "viscosity": 0.29,
        "kinematic_viscosity": 3.255e-4,
        "name_cn": "SAE 30 机油",
        "name_en": "SAE 30 Oil",
    },
    "glycerin_20c": {
        "density": 1261.0,
        "viscosity": 1.49,
        "kinematic_viscosity": 1.182e-3,
        "name_cn": "甘油 (20°C)",
        "name_en": "Glycerin at 20°C",
    },
}


def reynolds_number(velocity: float, diameter: float, density: float,
                    viscosity: float) -> float:
    """计算 Reynolds 数

    Re = ρvD/μ

    Args:
        velocity: 流速 (m/s)
        diameter: 特征直径/长度 (m)
        density: 流体密度 (kg/m³)
        viscosity: 动力粘度 (Pa·s)

    Returns:
        Reynolds 数
    """
    return (density * velocity * diameter) / viscosity


def reynolds_number_kinematic(velocity: float, diameter: float,
                              kinematic_viscosity: float) -> float:
    """使用运动粘度计算 Reynolds 数

    Re = vD/ν

    Args:
        velocity: 流速 (m/s)
        diameter: 特征直径/长度 (m)
        kinematic_viscosity: 运动粘度 (m²/s)

    Returns:
        Reynolds 数
    """
    return (velocity * diameter) / kinematic_viscosity


def classify_flow_regime(reynolds: float) -> dict:
    """根据 Reynolds 数分类流动状态

    Args:
        reynolds: Reynolds 数

    Returns:
        流动状态信息字典
    """
    if reynolds < 2300:
        regime = "laminar"
        regime_cn = "层流"
        description = (
            "流动稳定，流体分层流动，各层之间无混合。"
            "速度剖面呈抛物线分布。"
        )
        velocity_profile = "parabolic"
    elif reynolds < 4000:
        regime = "transitional"
        regime_cn = "过渡流"
        description = (
            "流动状态不稳定，在层流和湍流之间波动。"
            "流动特性难以预测。"
        )
        velocity_profile = "unstable"
    else:
        regime = "turbulent"
        regime_cn = "湍流"
        description = (
            "流动混乱，存在大量涡旋和速度脉动。"
            "速度剖面接近均匀分布。"
        )
        velocity_profile = "flat"

    return {
        "reynolds": reynolds,
        "regime": regime,
        "regime_cn": regime_cn,
        "description": description,
        "velocity_profile": velocity_profile,
        "is_laminar": reynolds < 2300,
        "is_turbulent": reynolds >= 4000,
    }


def critical_velocity(diameter: float, density: float,
                      viscosity: float, re_threshold: float = 2300) -> float:
    """计算临界速度（从层流到湍流的转变速度）

    v_critical = Re_critical × μ / (ρD)

    Args:
        diameter: 管道直径 (m)
        density: 流体密度 (kg/m³)
        viscosity: 动力粘度 (Pa·s)
        re_threshold: Reynolds 数临界值

    Returns:
        临界速度 (m/s)
    """
    return re_threshold * viscosity / (density * diameter)


def dynamic_viscosity_sutherland(temperature_c: float, fluid_type: str = "air") -> float:
    """使用 Sutherland 公式计算气体动力粘度

    μ = μ₀ × (T/T₀)^(3/2) × (T₀ + S)/(T + S)

    Args:
        temperature_c: 温度 (°C)
        fluid_type: 流体类型

    Returns:
        动力粘度 (Pa·s)
    """
    T = temperature_c + 273.15  # 转换为 Kelvin

    if fluid_type == "air":
        mu_0 = 1.716e-5
        T_0 = 273.15
        S = 110.4
    else:
        # 默认值
        mu_0 = 1.716e-5
        T_0 = 273.15
        S = 110.4

    T_kelvin = T
    mu = mu_0 * (T_kelvin / T_0)**1.5 * (T_0 + S) / (T_kelvin + S)
    return mu


def kinematic_viscosity_from_temp(fluid: str, temperature_c: float) -> float:
    """根据流体类型和温度获取运动粘度

    Args:
        fluid: 流体类型名称
        temperature_c: 温度 (°C)

    Returns:
        运动粘度 (m²/s)
    """
    if fluid in FLUID_PROPERTIES:
        return FLUID_PROPERTIES[fluid]["kinematic_viscosity"]
    raise ValueError(f"未知流体类型: {fluid}")


class FlowRegimeAnalyzer:
    """流动状态分析器

    用于分析和可视化流动状态的类。
    """

    def __init__(self, fluid: str = "water_20c"):
        """初始化分析器

        Args:
            fluid: 流体类型名称，默认为水 (20°C)
        """
        if fluid not in FLUID_PROPERTIES:
            raise ValueError(f"未知流体类型: {fluid}. 可用类型: {list(FLUID_PROPERTIES.keys())}")
        self.fluid = fluid
        self.properties = FLUID_PROPERTIES[fluid]

    def analyze(self, velocity: float, diameter: float) -> dict:
        """分析给定条件下的流动状态

        Args:
            velocity: 流速 (m/s)
            diameter: 管道直径 (m)

        Returns:
            分析结果字典
        """
        re = reynolds_number(velocity, diameter,
                            self.properties["density"],
                            self.properties["viscosity"])
        regime = classify_flow_regime(re)

        result = {
            "fluid": self.properties["name_cn"],
            "velocity": velocity,
            "diameter": diameter,
            "density": self.properties["density"],
            "viscosity": self.properties["viscosity"],
            "reynolds_number": re,
        }
        result.update(regime)
        return result

    def analyze_range(self, diameters: list, velocities: list) -> list:
        """分析多个直径和速度组合

        Args:
            diameters: 直径列表 (m)
            velocities: 速度列表 (m/s)

        Returns:
            分析结果列表
        """
        results = []
        for d in diameters:
            for v in velocities:
                result = self.analyze(v, d)
                results.append(result)
        return results

    def get_critical_velocity(self, diameter: float) -> float:
        """获取给定直径的临界速度

        Args:
            diameter: 管道直径 (m)

        Returns:
            临界速度 (m/s)
        """
        return critical_velocity(diameter,
                                self.properties["density"],
                                self.properties["viscosity"])
