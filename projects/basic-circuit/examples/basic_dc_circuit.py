"""
基础直流电路示例

演示电阻串联、并联、分压器等基本直流电路分析。
"""

import numpy as np
import matplotlib.pyplot as plt
from src.circuit import Circuit
from src.dc_analysis import DCAnalyzer, voltage_divider, series_resistance, parallel_resistance
from src.components import ohms_law, power


def example_ohms_law():
    """欧姆定律示例"""
    print("=" * 60)
    print("欧姆定律示例")
    print("=" * 60)

    # 已知电压和电阻，求电流
    result = ohms_law(voltage=12, resistance=1000)
    print(f"V=12V, R=1kΩ -> I={result['current']*1000:.2f}mA")

    # 已知电流和电阻，求电压
    result = ohms_law(current=0.005, resistance=2000)
    print(f"I=5mA, R=2kΩ -> V={result['voltage']:.2f}V")

    # 功率计算
    p = power(voltage=12, current=0.01)
    print(f"V=12V, I=10mA -> P={p*1000:.2f}mW")


def example_series_parallel():
    """串并联电阻示例"""
    print("\n" + "=" * 60)
    print("串并联电阻示例")
    print("=" * 60)

    # 串联
    r_series = series_resistance(1000, 2000, 3000)
    print(f"R1=1kΩ, R2=2kΩ, R3=3kΩ 串联: R_total={r_series:.0f}Ω")

    # 并联
    r_parallel = parallel_resistance(1000, 2000, 3000)
    print(f"R1=1kΩ, R2=2kΩ, R3=3kΩ 并联: R_total={r_parallel:.2f}Ω")


def example_voltage_divider():
    """分压器示例"""
    print("\n" + "=" * 60)
    print("分压器示例")
    print("=" * 60)

    v_in = 12
    r1 = 1000
    r2 = 2000

    v_out = voltage_divider(v_in, r1, r2)
    print(f"输入电压: {v_in}V")
    print(f"R1={r1}Ω, R2={r2}Ω")
    print(f"输出电压: {v_out:.2f}V")
    print(f"分压比: {v_out/v_in:.4f}")


def example_series_circuit():
    """串联电路分析"""
    print("\n" + "=" * 60)
    print("串联电路分析")
    print("=" * 60)

    # 创建电路
    circuit = Circuit("串联电路")
    n0 = circuit.add_node("GND")
    n1 = circuit.add_node("VCC")
    n2 = circuit.add_node("中间点")
    circuit.set_ground(n0)

    # 添加元件
    circuit.add_voltage_source("V1", n0, n1, 12)
    circuit.add_resistor("R1", n1, n2, 1000)
    circuit.add_resistor("R2", n2, n0, 2000)

    # 分析
    analyzer = DCAnalyzer(circuit)
    result = analyzer.solve()

    print("电路结构:")
    print(circuit.summary())
    print("\n分析结果:")
    print(result.summary())


def example_parallel_circuit():
    """并联电路分析"""
    print("\n" + "=" * 60)
    print("并联电路分析")
    print("=" * 60)

    # 创建电路
    circuit = Circuit("并联电路")
    n0 = circuit.add_node("GND")
    n1 = circuit.add_node("VCC")
    circuit.set_ground(n0)

    # 添加元件
    circuit.add_voltage_source("V1", n0, n1, 10)
    circuit.add_resistor("R1", n1, n0, 1000)
    circuit.add_resistor("R2", n1, n0, 2000)
    circuit.add_resistor("R3", n1, n0, 3000)

    # 分析
    analyzer = DCAnalyzer(circuit)
    result = analyzer.solve()

    print("电路结构:")
    print(circuit.summary())
    print("\n分析结果:")
    print(result.summary())

    # 验证总电流
    i_total = sum(result.branch_currents.values())
    print(f"\n总电流: {i_total*1000:.2f}mA")


def plot_voltage_divider():
    """绘制分压器特性曲线"""
    r1 = 1000
    r2_values = np.linspace(100, 10000, 100)
    v_in = 12

    v_out = [voltage_divider(v_in, r1, r2) for r2 in r2_values]

    plt.figure(figsize=(10, 6))
    plt.plot(r2_values, v_out, 'b-', linewidth=2)
    plt.xlabel('R2 (Ω)')
    plt.ylabel('输出电压 (V)')
    plt.title(f'分压器特性 (V_in={v_in}V, R1={r1}Ω)')
    plt.grid(True)
    plt.savefig('voltage_divider_curve.png', dpi=150)
    plt.close()
    print("\n已保存: voltage_divider_curve.png")


if __name__ == "__main__":
    example_ohms_law()
    example_series_parallel()
    example_voltage_divider()
    example_series_circuit()
    example_parallel_circuit()
    plot_voltage_divider()
