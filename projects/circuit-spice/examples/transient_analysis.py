"""
瞬态分析示例

演示 RC 电路的充电和放电过程
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from src.circuit import Circuit
from src.transient_analysis import TransientAnalysis, solve_rc_circuit


def main():
    print("=" * 60)
    print("RC 电路瞬态分析")
    print("=" * 60)

    # 电路参数
    v_in = 5.0  # 输入电压 5V
    r = 1000    # 电阻 1k Ohm
    c = 1e-6    # 电容 1uF
    tau = r * c # 时间常数

    print(f"\n电路参数:")
    print(f"  V_in = {v_in} V")
    print(f"  R = {r} Ohm")
    print(f"  C = {c * 1e6} uF")
    print(f"  时间常数 τ = RC = {tau * 1000:.2f} ms")

    # 创建电路
    circuit = Circuit("RC Charging Circuit")
    circuit.add_voltage_source("V1", 0, 1, v_in)
    circuit.add_resistor("R1", 1, 2, r)
    circuit.add_capacitor("C1", 2, 0, c)
    circuit.build_node_map()

    # 瞬态分析
    print("\n" + "=" * 60)
    print("充电过程分析")
    print("=" * 60)

    analyzer = TransientAnalysis(circuit, method="trapezoidal")

    t_step = tau / 100  # 每个时间常数 100 个点
    t_stop = 5 * tau    # 5 个时间常数

    print(f"\n仿真参数:")
    print(f"  时间步长: {t_step * 1e6:.2f} us")
    print(f"  终止时间: {t_stop * 1000:.2f} ms (5τ)")

    result = analyzer.solve(t_step, t_stop)

    # 输出结果
    output_node = 2
    print("\n充电过程:")
    print(f"{'时间 (ms)':>12} {'电压 (V)':>12} {'理论值 (V)':>12} {'误差 (%)':>12}")
    print("-" * 50)

    for i in range(0, len(result.time), len(result.time) // 10):
        t = result.time[i]
        v_sim = result.node_voltages[output_node][i]
        v_theory = v_in * (1 - np.exp(-t / tau))
        error = abs(v_sim - v_theory) / v_theory * 100 if v_theory > 0 else 0

        print(f"{t * 1000:>12.3f} {v_sim:>12.4f} {v_theory:>12.4f} {error:>12.2f}")

    # 关键时间点
    print("\n关键时间点:")
    tau_points = [1, 2, 3, 4, 5]
    for n in tau_points:
        t = n * tau
        idx = int(t / t_step)
        if idx < len(result.time):
            v_sim = result.node_voltages[output_node][idx]
            v_theory = v_in * (1 - np.exp(-n))
            print(f"  {n}τ = {t * 1000:.2f} ms: V = {v_sim:.4f} V (理论: {v_theory:.4f} V)")

    # 放电过程
    print("\n" + "=" * 60)
    print("放电过程分析")
    print("=" * 60)

    # 创建放电电路
    circuit_discharge = Circuit("RC Discharge Circuit")
    circuit_discharge.add_voltage_source("V1", 0, 1, 0)  # 0V 输入
    circuit_discharge.add_resistor("R1", 1, 2, r)
    circuit_discharge.add_capacitor("C1", 2, 0, c)
    circuit_discharge.build_node_map()

    analyzer_discharge = TransientAnalysis(circuit_discharge)

    # 初始条件: 电容已充电到 5V
    initial_conditions = {2: v_in}

    result_discharge = analyzer_discharge.solve(t_step, t_stop, initial_conditions=initial_conditions)

    print("\n放电过程:")
    print(f"{'时间 (ms)':>12} {'电压 (V)':>12} {'理论值 (V)':>12}")
    print("-" * 40)

    for i in range(0, len(result_discharge.time), len(result_discharge.time) // 10):
        t = result_discharge.time[i]
        v_sim = result_discharge.node_voltages[output_node][i]
        v_theory = v_in * np.exp(-t / tau)

        print(f"{t * 1000:>12.3f} {v_sim:>12.4f} {v_theory:>12.4f}")

    # 积分方法比较
    print("\n" + "=" * 60)
    print("积分方法比较")
    print("=" * 60)

    # 创建新电路
    circuit_compare = Circuit("RC Compare")
    circuit_compare.add_voltage_source("V1", 0, 1, v_in)
    circuit_compare.add_resistor("R1", 1, 2, r)
    circuit_compare.add_capacitor("C1", 2, 0, c)
    circuit_compare.build_node_map()

    # 梯形法
    analyzer_trap = TransientAnalysis(circuit_compare, method="trapezoidal")
    result_trap = analyzer_trap.solve(t_step, t_stop)

    # 后向欧拉法
    analyzer_be = TransientAnalysis(circuit_compare, method="backward_euler")
    result_be = analyzer_be.solve(t_step, t_stop)

    print("\n在 t = 1τ 处的比较:")
    idx_1tau = int(tau / t_step)

    v_trap = result_trap.node_voltages[output_node][idx_1tau]
    v_be = result_be.node_voltages[output_node][idx_1tau]
    v_theory = v_in * (1 - np.exp(-1))

    print(f"  梯形法: {v_trap:.6f} V")
    print(f"  后向欧拉法: {v_be:.6f} V")
    print(f"  理论值: {v_theory:.6f} V")


if __name__ == "__main__":
    main()
