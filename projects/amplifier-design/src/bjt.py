"""
BJT 基本放大器

实现三种基本BJT放大器配置：
- 共射放大器 (Common Emitter): 电压增益高，有反相
- 共集放大器 (Common Collector / Emitter Follower): 电压增益约1，电流增益高
- 共基放大器 (Common Base): 电压增益高，无反相，输入阻抗低
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class BJTParams:
    """BJT晶体管参数"""
    beta: float = 100.0        # 电流增益 hFE
    V_A: float = 100.0         # Early电压 (V)
    V_BE: float = 0.7          # 基极-发射极电压 (V)
    V_T: float = 0.026         # 热电压 (V), 室温约26mV

    @property
    def r_pi(self):
        """小信号输入电阻 r_pi = beta * V_T / I_C"""
        return None  # 需要工作点计算

    def transconductance(self, I_C: float) -> float:
        """跨导 g_m = I_C / V_T"""
        return I_C / self.V_T

    def r_pi_from_ic(self, I_C: float) -> float:
        """从小信号集电极电流计算 r_pi"""
        return self.beta * self.V_T / I_C

    def output_resistance(self, I_C: float) -> float:
        """输出电阻 r_o = V_A / I_C"""
        return self.V_A / I_C if I_C > 0 else float('inf')


class CommonEmitter:
    """
    共射放大器 (Common Emitter Amplifier)

    电路结构:
        VCC
         |
         RC
         |
    Vin--RB1--+--Vout
              |
              BJT (NPN)
              |
              RE
              |
             GND

    特点:
    - 电压增益高 (|Av| = gm * RC)
    - 输出信号反相 (180度相移)
    - 输入阻抗中等
    - 输出阻抗高
    """

    def __init__(self, R_B1: float, R_B2: float, R_C: float, R_E: float,
                 V_CC: float, bjt: BJTParams = None):
        """
        Args:
            R_B1: 基极偏置电阻1 (上拉), Ohm
            R_B2: 基极偏置电阻2 (下拉), Ohm
            R_C: 集电极电阻, Ohm
            R_E: 发射极电阻, Ohm
            V_CC: 电源电压, V
            bjt: BJT参数
        """
        self.R_B1 = R_B1
        self.R_B2 = R_B2
        self.R_C = R_C
        self.R_E = R_E
        self.V_CC = V_CC
        self.bjt = bjt or BJTParams()

    @property
    def R_B(self) -> float:
        """等效基极偏置电阻 R_B = R_B1 || R_B2"""
        return self.R_B1 * self.R_B2 / (self.R_B1 + self.R_B2)

    @property
    def V_B(self) -> float:
        """基极直流偏置电压"""
        return self.V_CC * self.R_B2 / (self.R_B1 + self.R_B2)

    def operating_point(self) -> dict:
        """
        计算直流工作点

        Returns:
            dict: 包含 I_C, V_CE, V_B, V_E, V_C
        """
        V_B = self.V_B
        V_E = V_B - self.bjt.V_BE
        I_C = V_E / self.R_E if self.R_E > 0 else 0.0
        I_B = I_C / self.bjt.beta
        V_C = self.V_CC - I_C * self.R_C
        V_CE = V_C - V_E

        return {
            'I_C': I_C,
            'I_B': I_B,
            'V_B': V_B,
            'V_E': V_E,
            'V_C': V_C,
            'V_CE': V_CE,
        }

    def voltage_gain(self, R_L: float = float('inf')) -> float:
        """
        小信号电压增益

        Args:
            R_L: 负载电阻, Ohm (默认无穷大)

        Returns:
            float: 电压增益 (负值表示反相)
        """
        op = self.operating_point()
        I_C = op['I_C']
        if I_C <= 0:
            return 0.0

        g_m = self.bjt.transconductance(I_C)
        r_o = self.bjt.output_resistance(I_C)

        # R_out = R_C || r_o || R_L
        R_out = 1.0 / (1.0 / self.R_C + 1.0 / r_o + 1.0 / R_L)

        # Av = -gm * R_out
        return -g_m * R_out

    def input_impedance(self) -> float:
        """
        输入阻抗 Z_in = R_B || r_pi

        Returns:
            float: 输入阻抗, Ohm
        """
        op = self.operating_point()
        r_pi = self.bjt.r_pi_from_ic(op['I_C'])
        return self.R_B * r_pi / (self.R_B + r_pi)

    def output_impedance(self) -> float:
        """
        输出阻抗 Z_out = R_C || r_o

        Returns:
            float: 输出阻抗, Ohm
        """
        op = self.operating_point()
        r_o = self.bjt.output_resistance(op['I_C'])
        return self.R_C * r_o / (self.R_C + r_o)

    def summary(self) -> dict:
        """获取放大器完整参数摘要"""
        op = self.operating_point()
        return {
            'type': '共射放大器 (Common Emitter)',
            'operating_point': op,
            'voltage_gain': self.voltage_gain(),
            'input_impedance': self.input_impedance(),
            'output_impedance': self.output_impedance(),
            'phase_shift': 180.0,  # 反相
        }


class CommonCollector:
    """
    共集放大器 (Common Collector / Emitter Follower)

    电路结构:
        VCC
         |
         R_E
         |
    Vin--+--Vout
          |
         BJT (NPN)
          |
         GND

    特点:
    - 电压增益约1 (略小于1)
    - 输出信号同相
    - 输入阻抗高
    - 输出阻抗低
    - 电流增益高
    - 用作缓冲器/阻抗变换
    """

    def __init__(self, R_B1: float, R_B2: float, R_E: float,
                 V_CC: float, bjt: BJTParams = None):
        """
        Args:
            R_B1: 基极偏置电阻1 (上拉), Ohm
            R_B2: 基极偏置电阻2 (下拉), Ohm
            R_E: 发射极电阻, Ohm
            V_CC: 电源电压, V
            bjt: BJT参数
        """
        self.R_B1 = R_B1
        self.R_B2 = R_B2
        self.R_E = R_E
        self.V_CC = V_CC
        self.bjt = bjt or BJTParams()

    @property
    def R_B(self) -> float:
        return self.R_B1 * self.R_B2 / (self.R_B1 + self.R_B2)

    @property
    def V_B(self) -> float:
        return self.V_CC * self.R_B2 / (self.R_B1 + self.R_B2)

    def operating_point(self) -> dict:
        """计算直流工作点"""
        V_B = self.V_B
        V_E = V_B - self.bjt.V_BE
        I_C = V_E / self.R_E if self.R_E > 0 else 0.0
        I_B = I_C / self.bjt.beta
        V_CE = self.V_CC - V_E

        return {
            'I_C': I_C,
            'I_B': I_B,
            'V_B': V_B,
            'V_E': V_E,
            'V_CE': V_CE,
        }

    def voltage_gain(self, R_L: float = float('inf')) -> float:
        """
        小信号电压增益 (接近1)

        Av = gm * (R_E || R_L) / (1 + gm * (R_E || R_L))
        """
        op = self.operating_point()
        I_C = op['I_C']
        if I_C <= 0:
            return 0.0

        g_m = self.bjt.transconductance(I_C)
        R_EL = self.R_E * R_L / (self.R_E + R_L) if R_L < float('inf') else self.R_E

        return g_m * R_EL / (1 + g_m * R_EL)

    def input_impedance(self, R_L: float = float('inf')) -> float:
        """
        输入阻抗

        Z_in = R_B || (r_pi + (beta+1) * (R_E || R_L))
        """
        op = self.operating_point()
        r_pi = self.bjt.r_pi_from_ic(op['I_C'])
        R_EL = self.R_E * R_L / (self.R_E + R_L) if R_L < float('inf') else self.R_E
        Z_base = r_pi + (self.bjt.beta + 1) * R_EL
        return self.R_B * Z_base / (self.R_B + Z_base)

    def output_impedance(self, R_s: float = 0.0) -> float:
        """
        输出阻抗

        Z_out = R_E || ((R_s || R_B) + r_pi) / (beta + 1)
        """
        op = self.operating_point()
        r_pi = self.bjt.r_pi_from_ic(op['I_C'])
        R_s_eff = R_s * self.R_B / (R_s + self.R_B) if R_s > 0 else self.R_B
        Z_base = (R_s_eff + r_pi) / (self.bjt.beta + 1)
        return self.R_E * Z_base / (self.R_E + Z_base)

    def summary(self) -> dict:
        """获取放大器完整参数摘要"""
        return {
            'type': '共集放大器 (Common Collector / Emitter Follower)',
            'operating_point': self.operating_point(),
            'voltage_gain': self.voltage_gain(),
            'input_impedance': self.input_impedance(),
            'output_impedance': self.output_impedance(),
            'phase_shift': 0.0,  # 同相
        }


class CommonBase:
    """
    共基放大器 (Common Base Amplifier)

    电路结构:
        VCC
         |
         RC
         |
         +--Vout
         |
        BJT (NPN)
         |
    Vin--RE
         |
        GND

    特点:
    - 电压增益高
    - 输出信号同相 (无反相)
    - 输入阻抗低
    - 输出阻抗高
    - 高频特性好
    """

    def __init__(self, R_E: float, R_C: float, V_CC: float, I_C_bias: float,
                 bjt: BJTParams = None):
        """
        Args:
            R_E: 发射极电阻, Ohm
            R_C: 集电极电阻, Ohm
            V_CC: 电源电压, V
            I_C_bias: 集电极偏置电流, A
            bjt: BJT参数
        """
        self.R_E = R_E
        self.R_C = R_C
        self.V_CC = V_CC
        self.I_C_bias = I_C_bias
        self.bjt = bjt or BJTParams()

    def operating_point(self) -> dict:
        """计算直流工作点"""
        I_C = self.I_C_bias
        V_C = self.V_CC - I_C * self.R_C
        V_E = I_C * self.R_E  # 近似
        V_CE = V_C - V_E

        return {
            'I_C': I_C,
            'V_C': V_C,
            'V_E': V_E,
            'V_CE': V_CE,
        }

    def voltage_gain(self, R_L: float = float('inf')) -> float:
        """
        小信号电压增益

        Av = gm * (R_C || R_L)
        """
        g_m = self.bjt.transconductance(self.I_C_bias)
        r_o = self.bjt.output_resistance(self.I_C_bias)

        R_out = 1.0 / (1.0 / self.R_C + 1.0 / r_o + 1.0 / R_L)
        return g_m * R_out

    def input_impedance(self) -> float:
        """
        输入阻抗 (低)

        Z_in = R_E || (r_pi / (beta + 1))
        """
        r_pi = self.bjt.r_pi_from_ic(self.I_C_bias)
        Z_e = r_pi / (self.bjt.beta + 1)
        return self.R_E * Z_e / (self.R_E + Z_e)

    def output_impedance(self) -> float:
        """
        输出阻抗

        Z_out = R_C || r_o
        """
        r_o = self.bjt.output_resistance(self.I_C_bias)
        return self.R_C * r_o / (self.R_C + r_o)

    def summary(self) -> dict:
        """获取放大器完整参数摘要"""
        return {
            'type': '共基放大器 (Common Base)',
            'operating_point': self.operating_point(),
            'voltage_gain': self.voltage_gain(),
            'input_impedance': self.input_impedance(),
            'output_impedance': self.output_impedance(),
            'phase_shift': 0.0,  # 同相
        }
