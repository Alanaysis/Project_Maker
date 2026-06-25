"""
运算放大器电路

实现常见的运算放大器配置：
- 反相放大器 (Inverting Amplifier)
- 同相放大器 (Non-Inverting Amplifier)
- 差分放大器 (Differential Amplifier)
- 仪表放大器 (Instrumentation Amplifier)
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class OpAmpParams:
    """运算放大器参数"""
    A_OL: float = 1e5          # 开环增益
    GBW: float = 1e6           # 增益带宽积 (Hz)
    SR: float = 0.5e6          # 转换速率 (V/s)
    V_sat: float = 13.5        # 饱和电压 (V), 假设 +/-15V供电
    I_bias: float = 100e-9     # 输入偏置电流 (A)
    V_os: float = 2e-3         # 输入失调电压 (V)
    CMRR: float = 90.0         # 共模抑制比 (dB)
    PSRR: float = 90.0         # 电源抑制比 (dB)

    @property
    def CMRR_linear(self) -> float:
        """共模抑制比 (线性值)"""
        return 10 ** (self.CMRR / 20)

    @property
    def PSRR_linear(self) -> float:
        """电源抑制比 (线性值)"""
        return 10 ** (self.PSRR / 20)


class InvertingAmp:
    r"""
    反相放大器

    电路结构:
             Rf
        ┌──/\/\/──┐
        │         │
   Rin  │    ┌────┤
  /\/\/─┤    │-   │
        ├────┤ OpAmp── Vout
  Vin ──┘  ┌─┤+   │
           │ └────┘
          GND

    传递函数: Vout/Vin = -Rf / Rin

    特点:
    - 输出反相
    - 虚地 (反相输入端为虚地)
    - 输入阻抗 = Rin
    - 增益 = -Rf/Rin
    """

    def __init__(self, R_in: float, R_f: float, opamp: OpAmpParams = None):
        """
        Args:
            R_in: 输入电阻, Ohm
            R_f: 反馈电阻, Ohm
            opamp: 运放参数
        """
        self.R_in = R_in
        self.R_f = R_f
        self.opamp = opamp or OpAmpParams()

    def gain(self) -> float:
        """
        理想闭环电压增益

        Returns:
            float: Av = -Rf/Rin (负值表示反相)
        """
        return -self.R_f / self.R_in

    def gain_with_loading(self) -> float:
        """
        考虑有限开环增益的实际闭环增益

        Returns:
            float: 实际增益
        """
        ideal = self.gain()
        beta = self.R_in / (self.R_in + self.R_f)  # 反馈系数
        return ideal / (1 + (1 - ideal) / (self.opamp.A_OL * beta))

    def input_impedance(self) -> float:
        """
        输入阻抗 (等于输入电阻，因为虚地)

        Returns:
            float: Z_in = Rin
        """
        return self.R_in

    def output_impedance(self) -> float:
        """
        输出阻抗 (理想运放为0)

        Returns:
            float: Z_out ≈ Ro_OL / (1 + A_OL * beta)
        """
        beta = self.R_in / (self.R_in + self.R_f)
        return self.opamp.A_OL * beta  # 简化近似

    def bandwidth(self) -> float:
        """
        闭环带宽

        BW = GBW / |Av|

        Returns:
            float: 带宽, Hz
        """
        return self.opamp.GBW / abs(self.gain())

    def max_output_swing(self, freq: float) -> float:
        """
        受转换速率限制的最大输出幅度

        Vmax = SR / (2 * pi * f)

        Args:
            freq: 信号频率, Hz

        Returns:
            float: 最大输出幅度, V
        """
        sr_limit = self.opamp.SR / (2 * np.pi * freq)
        return min(sr_limit, self.opamp.V_sat)

    def transfer_function(self, f: np.ndarray) -> np.ndarray:
        """
        频率响应 (含运放有限带宽)

        Args:
            f: 频率数组, Hz

        Returns:
            np.ndarray: 复数传递函数值
        """
        s = 1j * 2 * np.pi * f
        # 一阶近似: H(s) = (-Rf/Rin) / (1 + s/omega_p)
        # omega_p = GBW / (1 + Rf/Rin)
        omega_p = 2 * np.pi * self.opamp.GBW / (1 + abs(self.gain()))
        return self.gain() / (1 + s / omega_p)

    def summary(self) -> dict:
        """获取放大器完整参数摘要"""
        return {
            'type': '反相放大器 (Inverting Amplifier)',
            'ideal_gain': self.gain(),
            'actual_gain': self.gain_with_loading(),
            'input_impedance': self.input_impedance(),
            'bandwidth': self.bandwidth(),
            'gain_bandwidth_product': self.opamp.GBW,
            'phase_shift': 180.0,
        }


class NonInvertingAmp:
    r"""
    同相放大器

    电路结构:
             Rf
        ┌──/\/\/──┐
        │         │
        │    ┌────┤
   Rin  │    │-   │
  /\/\/─┤    │    ├── Vout
        ├────┤OpAmp│
  Vin ──┤  ┌─┤+   │
        │  │ └────┘
        │ GND

    传递函数: Vout/Vin = 1 + Rf/Rin

    特点:
    - 输出同相
    - 输入阻抗非常高 (运放输入阻抗)
    - 增益 = 1 + Rf/Rin
    """

    def __init__(self, R_in: float, R_f: float, opamp: OpAmpParams = None):
        """
        Args:
            R_in: 接地电阻, Ohm
            R_f: 反馈电阻, Ohm
            opamp: 运放参数
        """
        self.R_in = R_in
        self.R_f = R_f
        self.opamp = opamp or OpAmpParams()

    def gain(self) -> float:
        """
        理想闭环电压增益

        Returns:
            float: Av = 1 + Rf/Rin
        """
        return 1 + self.R_f / self.R_in

    def gain_with_loading(self) -> float:
        """考虑有限开环增益的实际增益"""
        ideal = self.gain()
        beta = self.R_in / (self.R_in + self.R_f)
        return ideal / (1 + ideal / (self.opamp.A_OL * beta))

    def input_impedance(self) -> float:
        """
        输入阻抗 (非常高，取决于运放)

        Returns:
            float: Z_in ≈ A_OL * R_in (简化)
        """
        return self.opamp.A_OL * self.R_in

    def bandwidth(self) -> float:
        """闭环带宽"""
        return self.opamp.GBW / self.gain()

    def max_output_swing(self, freq: float) -> float:
        """受转换速率限制的最大输出幅度"""
        sr_limit = self.opamp.SR / (2 * np.pi * freq)
        return min(sr_limit, self.opamp.V_sat)

    def transfer_function(self, f: np.ndarray) -> np.ndarray:
        """
        频率响应

        Args:
            f: 频率数组, Hz

        Returns:
            np.ndarray: 复数传递函数值
        """
        s = 1j * 2 * np.pi * f
        omega_p = 2 * np.pi * self.opamp.GBW / self.gain()
        return self.gain() / (1 + s / omega_p)

    def summary(self) -> dict:
        """获取放大器完整参数摘要"""
        return {
            'type': '同相放大器 (Non-Inverting Amplifier)',
            'ideal_gain': self.gain(),
            'actual_gain': self.gain_with_loading(),
            'input_impedance': self.input_impedance(),
            'bandwidth': self.bandwidth(),
            'gain_bandwidth_product': self.opamp.GBW,
            'phase_shift': 0.0,
        }


class DifferentialAmp:
    r"""
    差分放大器

    电路结构:
        R1       Rf
  V1 ─/\/\/─┐  ┌─/\/\/─┐
            │  │        │
            └──┤-       │
               │  OpAmp──├── Vout
  V2 ─/\/\/─┐──┤+       │
        R2  │  └────────┘
           GND

    传递函数: Vout = (Rf/R1) * (V2 - V1)  (当 Rf/R1 = R_gnd/R2)

    特点:
    - 放大两个输入信号的差值
    - 抑制共模信号
    - CMRR取决于电阻匹配精度
    """

    def __init__(self, R1: float, R_f: float, R2: float = None, R_g: float = None,
                 opamp: OpAmpParams = None):
        """
        Args:
            R1: 反相输入端电阻, Ohm
            R_f: 反馈电阻, Ohm
            R2: 同相输入端电阻, Ohm (默认=R1)
            R_g: 同相输入端接地电阻, Ohm (默认=R_f)
            opamp: 运放参数
        """
        self.R1 = R1
        self.R_f = R_f
        self.R2 = R2 or R1
        self.R_g = R_g or R_f
        self.opamp = opamp or OpAmpParams()

    def differential_gain(self) -> float:
        """
        差模增益

        Returns:
            float: Ad = Rf / R1
        """
        return self.R_f / self.R1

    def common_mode_gain(self) -> float:
        """
        共模增益 (理想为0，实际取决于电阻匹配)

        Returns:
            float: Acm
        """
        Ad = self.differential_gain()
        # 理想情况下，当 Rf/R1 = Rg/R2 时，Acm = 0
        actual_ratio = self.R_g / self.R2
        ideal_ratio = self.R_f / self.R1
        return Ad * (actual_ratio - ideal_ratio) / (actual_ratio + 1)

    def cmrr(self) -> float:
        """
        共模抑制比 (dB)

        Returns:
            float: CMRR in dB
        """
        Ad = abs(self.differential_gain())
        Acm = abs(self.common_mode_gain())
        if Acm < 1e-30:
            return float('inf')
        return 20 * np.log10(Ad / Acm)

    def output(self, V1: float, V2: float) -> float:
        """
        计算输出电压

        Vout = Ad * (V2 - V1)

        Args:
            V1: 反相输入电压, V
            V2: 同相输入电压, V

        Returns:
            float: 输出电压, V (受饱和限制)
        """
        Vout = self.differential_gain() * (V2 - V1)
        return np.clip(Vout, -self.opamp.V_sat, self.opamp.V_sat)

    def bandwidth(self) -> float:
        """闭环带宽"""
        return self.opamp.GBW / self.differential_gain()

    def summary(self) -> dict:
        """获取放大器完整参数摘要"""
        return {
            'type': '差分放大器 (Differential Amplifier)',
            'differential_gain': self.differential_gain(),
            'common_mode_gain': self.common_mode_gain(),
            'cmrr_dB': self.cmrr(),
            'bandwidth': self.bandwidth(),
            'gain_bandwidth_product': self.opamp.GBW,
        }


class InstrumentationAmp:
    r"""
    仪表放大器 (三运放结构)

    电路结构:
       +-----------------------------------+
       |                                   |
  V1 --+ Rg    +-----+   +-----+          |
       +-\/\/--+OA1   +---+     |          |
       |       +-----+   |     |          |
       |                 |OA3  +--Vout     |
       |       +-----+   |     |          |
  V2 --+ Rg    |OA2  +---+     |          |
       +-\/\/--+     |   +-----+          |
       |       +-----+                     |
       +-----------------------------------+

    传递函数: Vout = (1 + 2*R1/Rg) * (V2 - V1)

    特点:
    - 极高的输入阻抗
    - 极高的共模抑制比
    - 增益通过单个电阻 Rg 设置
    - 广泛用于传感器信号放大
    """

    def __init__(self, R1: float, R_g: float,
                 R2: float = None, R3: float = None,
                 R4: float = None, R5: float = None,
                 opamp: OpAmpParams = None):
        """
        Args:
            R1: 前级运放反馈电阻, Ohm
            R_g: 增益设置电阻, Ohm
            R2: 后级运放反相输入电阻, Ohm (默认=R1)
            R3: 后级运放同相输入电阻, Ohm (默认=R1)
            R4: 后级运放反馈电阻, Ohm (默认=R1)
            R5: 后级运放接地电阻, Ohm (默认=R1)
            opamp: 运放参数
        """
        self.R1 = R1
        self.R_g = R_g
        self.R2 = R2 or R1
        self.R3 = R3 or R1
        self.R4 = R4 or R1
        self.R5 = R5 or R1
        self.opamp = opamp or OpAmpParams()

    def gain(self) -> float:
        """
        差模增益

        Returns:
            float: G = (1 + 2*R1/Rg) * (R4/R2) / (R5/(R3+R5)) / (R4/(R2))
            简化: G = 1 + 2*R1/Rg (当 R4/R2 = R5/R3)
        """
        return 1 + 2 * self.R1 / self.R_g

    def set_gain(self, new_gain: float) -> None:
        """
        设置目标增益并更新 R_g

        Args:
            new_gain: 目标增益
        """
        if new_gain <= 1:
            raise ValueError("增益必须大于1")
        self.R_g = 2 * self.R1 / (new_gain - 1)

    def output(self, V1: float, V2: float) -> float:
        """
        计算输出电压

        Args:
            V1: 输入1, V
            V2: 输入2, V

        Returns:
            float: 输出电压, V
        """
        Vout = self.gain() * (V2 - V1)
        return np.clip(Vout, -self.opamp.V_sat, self.opamp.V_sat)

    def bandwidth(self) -> float:
        """闭环带宽"""
        return self.opamp.GBW / self.gain()

    def input_impedance(self) -> float:
        """
        输入阻抗 (非常高)

        Returns:
            float: Z_in ≈ 10^12 Ohm (运放输入阻抗)
        """
        return 1e12

    def summary(self) -> dict:
        """获取放大器完整参数摘要"""
        return {
            'type': '仪表放大器 (Instrumentation Amplifier)',
            'gain': self.gain(),
            'input_impedance': self.input_impedance(),
            'bandwidth': self.bandwidth(),
            'gain_bandwidth_product': self.opamp.GBW,
            'cmrr_dB': self.opamp.CMRR,
        }
