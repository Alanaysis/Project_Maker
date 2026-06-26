"""
水头损失计算 (Head Loss Calculation)

水头损失分为两类：

1. 沿程水头损失 (Major Losses) - 由管道摩擦引起
   使用 Darcy-Weisbach 方程：
       h_f = f × (L/D) × (v²/(2g))

2. 局部水头损失 (Minor Losses) - 由管件引起
   h_m = K × (v²/(2g))

   其中 K 为损失系数，取决于管件类型。
"""

import numpy as np
from .pipe_flow import darcy_weisbach_head_loss, swamee_jain_friction_factor, laminar_friction_factor


# 常见管件的局部损失系数 K
MINOR_LOSS_COEFFICIENTS = {
    # 入口类型
    "inlet_reentrant": {"K": 0.8, "name_cn": "插入式入口", "name_en": "Reentrant Inlet"},
    "inlet_square": {"K": 0.5, "name_cn": "方形边缘入口", "name_en": "Square-Edged Inlet"},
    "inlet_rounded": {"K": 0.04, "name_cn": "圆滑入口", "name_en": "Rounded Inlet"},

    # 出口
    "exit submerged": {"K": 1.0, "name_cn": "淹没出口", "name_en": "Submerged Exit"},

    # 阀门
    "gate_valve_full_open": {"K": 0.15, "name_cn": "全开闸阀", "name_en": "Gate Valve (Full Open)"},
    "gate_valve_half_open": {"K": 2.1, "name_cn": "半开闸阀", "name_en": "Gate Valve (Half Open)"},
    "globe_valve_full_open": {"K": 10.0, "name_cn": "全开截止阀", "name_en": "Globe Valve (Full Open)"},
    "ball_valve_full_open": {"K": 0.05, "name_cn": "全开球阀", "name_en": "Ball Valve (Full Open)"},
    "check_valve": {"K": 2.5, "name_cn": "止回阀", "name_en": "Check Valve"},
    "needle_valve": {"K": 5.0, "name_cn": "针阀", "name_en": "Needle Valve"},

    # 弯头
    "elbow_90_standard": {"K": 0.9, "name_cn": "90°标准弯头", "name_en": "90° Standard Elbow"},
    "elbow_90_long_radius": {"K": 0.6, "name_cn": "90°长半径弯头", "name_en": "90° Long Radius Elbow"},
    "elbow_45_standard": {"K": 0.4, "name_cn": "45°标准弯头", "name_en": "45° Standard Elbow"},
    "elbow_flat": {"K": 1.8, "name_cn": "180°平底弯头", "name_en": "180° Flat Return Bend"},

    # 三通
    "tee_branch_flow": {"K": 1.8, "name_cn": "三通（分支流动）", "name_en": "Tee (Branch Flow)"},
    "tee_line_flow": {"K": 0.2, "name_cn": "三通（直通流动）", "name_en": "Tee (Line Flow)"},

    # 收缩/扩张
    "sudden_contraction": {"K_contract": 0.4, "name_cn": "突然收缩", "name_en": "Sudden Contraction"},
    "sudden_expansion": {"K_expand": 1.0, "name_cn": "突然扩张", "name_en": "Sudden Expansion"},

    # 其他
    "filter_clean": {"K": 7.0, "name_cn": "清洁过滤器", "name_en": "Clean Filter"},
    "strainer": {"K": 2.0, "name_cn": "滤网", "name_en": "Strainer"},
}


def major_loss(length: float, diameter: float, velocity: float,
               reynolds: float, roughness: float = 0.0,
               gravity: float = 9.81) -> float:
    """计算沿程水头损失 (Major Loss)

    使用 Darcy-Weisbach 方程：
        h_f = f × (L/D) × (v²/(2g))

    Args:
        length: 管道长度 (m)
        diameter: 管道内径 (m)
        velocity: 流速 (m/s)
        reynolds: Reynolds 数
        roughness: 管道粗糙度 (m)
        gravity: 重力加速度 (m/s²)

    Returns:
        沿程水头损失 (m)
    """
    return darcy_weisbach_head_loss(length, diameter, velocity,
                                    reynolds, roughness, gravity)


def minor_loss(velocity: float, loss_coefficient: float,
               gravity: float = 9.81) -> float:
    """计算局部水头损失 (Minor Loss)

    h_m = K × (v²/(2g))

    Args:
        velocity: 流速 (m/s)
        loss_coefficient: 损失系数 K
        gravity: 重力加速度 (m/s²)

    Returns:
        局部水头损失 (m)
    """
    return loss_coefficient * (velocity**2) / (2 * gravity)


def total_minor_loss(velocity: float, components: list,
                     gravity: float = 9.81) -> dict:
    """计算所有局部损失的总和

    Args:
        velocity: 流速 (m/s)
        components: 管件列表，每个元素为损失系数 K 或组件名称
        gravity: 重力加速度 (m/s²)

    Returns:
        包含总损失和各组件损失的字典
    """
    total_loss = 0.0
    component_losses = []

    for comp in components:
        if isinstance(comp, str):
            if comp not in MINOR_LOSS_COEFFICIENTS:
                raise ValueError(f"未知组件: {comp}")
            k = MINOR_LOSS_COEFFICIENTS[comp]["K"]
            name = MINOR_LOSS_COEFFICIENTS[comp]["name_cn"]
        else:
            k = comp
            name = "自定义"

        loss = minor_loss(velocity, k, gravity)
        total_loss += loss
        component_losses.append({
            "name": name,
            "K": k,
            "head_loss": loss,
        })

    return {
        "total_minor_loss": total_loss,
        "components": component_losses,
    }


def total_head_loss(length: float, diameter: float, velocity: float,
                    reynolds: float, roughness: float = 0.0,
                    minor_components: list = None,
                    gravity: float = 9.81) -> dict:
    """计算总水头损失（沿程 + 局部）

    h_total = h_major + h_minor

    Args:
        length: 管道长度 (m)
        diameter: 管道内径 (m)
        velocity: 流速 (m/s)
        reynolds: Reynolds 数
        roughness: 管道粗糙度 (m)
        minor_components: 局部损失组件列表
        gravity: 重力加速度 (m/s²)

    Returns:
        包含各项损失的字典
    """
    major = major_loss(length, diameter, velocity, reynolds, roughness, gravity)

    minor_result = {"total_minor_loss": 0.0, "components": []}
    if minor_components:
        minor_result = total_minor_loss(velocity, minor_components, gravity)

    return {
        "major_loss": major,
        "minor_loss": minor_result["total_minor_loss"],
        "total_loss": major + minor_result["total_minor_loss"],
        "minor_components": minor_result["components"],
        "loss_ratio": minor_result["total_minor_loss"] / (major + minor_result["total_minor_loss"])
        if (major + minor_result["total_minor_loss"]) > 0 else 0,
    }


def equivalent_length(k: float, diameter: float, reynolds: float,
                      roughness: float = 0.0) -> float:
    """将局部损失转换为等效长度

    L_eq = K × D / f

    这种方法将局部损失等效为一段直管的沿程损失。

    Args:
        k: 损失系数
        diameter: 管道直径 (m)
        reynolds: Reynolds 数
        roughness: 管道粗糙度 (m)

    Returns:
        等效长度 (m)
    """
    if reynolds < 2300:
        f = laminar_friction_factor(reynolds)
    else:
        f = swamee_jain_friction_factor(reynolds, roughness, diameter)

    if f == 0:
        return 0.0
    return k * diameter / f


class HeadLossCalculator:
    """水头损失计算器

    用于综合计算管道系统中的总水头损失。
    """

    def __init__(self, fluid_density: float = 1000.0,
                 fluid_viscosity: float = 1.002e-3,
                 gravity: float = 9.81):
        """初始化计算器

        Args:
            fluid_density: 流体密度 (kg/m³)
            fluid_viscosity: 流体动力粘度 (Pa·s)
            gravity: 重力加速度 (m/s²)
        """
        self.fluid_density = fluid_density
        self.fluid_viscosity = fluid_viscosity
        self.gravity = gravity

    def reynolds_from_velocity(self, velocity: float, diameter: float) -> float:
        """根据流速和直径计算 Reynolds 数

        Args:
            velocity: 流速 (m/s)
            diameter: 直径 (m)

        Returns:
            Reynolds 数
        """
        return (self.fluid_density * velocity * diameter) / self.fluid_viscosity

    def calculate_system(self, length: float, diameter: float,
                         flow_rate: float, roughness: float = 0.0,
                         minor_components: list = None) -> dict:
        """计算管道系统的完整水头损失

        Args:
            length: 管道长度 (m)
            diameter: 管道内径 (m)
            flow_rate: 体积流量 (m³/s)
            roughness: 管道粗糙度 (m)
            minor_components: 局部损失组件列表

        Returns:
            完整的损失分析结果
        """
        velocity = flow_rate / (np.pi * (diameter / 2)**2)
        re = self.reynolds_from_velocity(velocity, diameter)
        loss_results = total_head_loss(
            length, diameter, velocity, re, roughness,
            minor_components, self.gravity
        )

        return {
            "flow_rate": flow_rate,
            "velocity": velocity,
            "reynolds_number": re,
            "diameter": diameter,
            "length": length,
            "roughness": roughness,
            "major_loss": loss_results["major_loss"],
            "minor_loss": loss_results["minor_loss"],
            "total_loss": loss_results["total_loss"],
            "loss_ratio_minor": loss_results["loss_ratio"],
            "minor_components": loss_results["minor_components"],
        }
