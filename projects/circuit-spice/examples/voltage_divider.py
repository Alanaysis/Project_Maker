"""
分压器电路示例

演示基本的直流分析
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.circuit import Circuit
from src.dc_analysis import DCAnalysis, voltage_divider


def main():
    print("=" * 60)
    print("分压器电路分析")
    print("=" * 60)

    # 创建分压器电路
    # V1 (12V) -- R1 (1k) -- R2 (2k) -- GND
    circuit = Circuit("Voltage Divider")
    circuit.add_voltage_source("V1", 0, 1, 12)
    circuit.add_resistor("R1", 1, 2, 1000)
    circuit.add_resistor("R2", 2, 0, 2000)

    print("\n电路信息:")
    print(circuit.summary())

    # 直流分析
    print("\n" + "=" * 60)
    print("直流工作点分析")
    print("=" * 60)

    analyzer = DCAnalysis(circuit)
    result = analyzer.solve()

    print("\n节点电压:")
    for node, voltage in sorted(result.node_voltages.items()):
        print(f"  V({node}) = {voltage:.4f} V")

    print("\n支路电流:")
    for name, current in result.branch_currents.items():
        print(f"  I({name}) = {current * 1000:.4f} mA")

    # 理论计算
    print("\n" + "=" * 60)
    print("理论计算验证")
    print("=" * 60)

    v_in = 12
    r1 = 1000
    r2 = 2000
    v_out = v_in * r2 / (r1 + r2)
    i_total = v_in / (r1 + r2)

    print(f"\n分压器公式: V_out = V_in × R2 / (R1 + R2)")
    print(f"V_out = {v_in} × {r2} / ({r1} + {r2}) = {v_out:.4f} V")
    print(f"I = V_in / (R1 + R2) = {v_in} / ({r1} + {r2}) = {i_total * 1000:.4f} mA")

    # 使用函数接口
    print("\n" + "=" * 60)
    print("使用分压器函数")
    print("=" * 60)

    result2 = voltage_divider(12, 1000, 2000)
    print(f"V_out = {result2.node_voltages[2]:.4f} V")


if __name__ == "__main__":
    main()
