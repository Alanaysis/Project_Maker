"""
瞬态分析测试
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.circuit import Circuit
from src.transient_analysis import (
    TransientAnalysis, solve_rc_circuit, solve_rlc_circuit,
    step_response, IntegrationMethod
)


class TestIntegrationMethods:
    """数值积分方法测试"""

    def test_backward_euler(self):
        """测试后向欧拉法"""
        c = 1e-6
        h = 1e-6

        g_eq, i_coeff = IntegrationMethod.backward_euler(c, h)

        # G_eq = C/h
        assert g_eq == pytest.approx(c / h)
        assert i_coeff == pytest.approx(c / h)

    def test_trapezoidal(self):
        """测试梯形法"""
        c = 1e-6
        h = 1e-6

        g_eq, i_coeff = IntegrationMethod.trapezoidal(c, h)

        # G_eq = 2C/h
        assert g_eq == pytest.approx(2 * c / h)
        assert i_coeff == pytest.approx(2 * c / h)


class TestTransientAnalysis:
    """瞬态分析测试"""

    def test_rc_charging(self):
        """测试 RC 充电电路"""
        v_in = 5.0
        r = 1000
        c = 1e-6
        tau = r * c  # 时间常数 = 1ms

        t_step = tau / 100
        t_stop = 5 * tau  # 5 个时间常数

        result = solve_rc_circuit(v_in, r, c, t_step, t_stop)

        # 验证输出节点 (节点 2) 最终接近输入电压
        output_node = 2
        final_voltage = result.node_voltages[output_node][-1]
        assert final_voltage == pytest.approx(v_in, rel=0.01)

        # 验证初始电压为 0
        initial_voltage = result.node_voltages[output_node][0]
        assert initial_voltage == pytest.approx(0.0)

    def test_rc_time_constant(self):
        """测试 RC 时间常数"""
        v_in = 1.0
        r = 1000
        c = 1e-6
        tau = r * c

        t_step = tau / 1000
        t_stop = 5 * tau

        result = solve_rc_circuit(v_in, r, c, t_step, t_stop)

        # 在 t = tau 时，电压应为 1 - 1/e ≈ 0.632
        output_node = 2
        tau_idx = int(tau / t_step)
        v_at_tau = result.node_voltages[output_node][tau_idx]

        expected = v_in * (1 - 1 / np.e)
        assert v_at_tau == pytest.approx(expected, rel=0.05)

    def test_rc_discharging(self):
        """测试 RC 放电电路"""
        # 先充电，然后放电
        v_in = 5.0
        r = 1000
        c = 1e-6
        tau = r * c

        # 创建带初始条件的电路
        circuit = Circuit("RC Discharge")
        circuit.add_voltage_source("V1", 0, 1, 0)  # 0V 输入
        circuit.add_resistor("R1", 1, 2, r)
        circuit.add_capacitor("C1", 2, 0, c)
        circuit.build_node_map()

        analyzer = TransientAnalysis(circuit)

        # 设置初始条件 (电容已充电)
        initial_conditions = {2: v_in}

        t_step = tau / 100
        t_stop = 5 * tau

        result = analyzer.solve(t_step, t_stop, initial_conditions=initial_conditions)

        # 验证电压衰减
        output_node = 2
        final_voltage = result.node_voltages[output_node][-1]
        assert final_voltage == pytest.approx(0.0, abs=0.1)

    def test_rlc_oscillation(self):
        """测试 RLC 振荡"""
        v_in = 1.0
        r = 10
        l = 1e-3
        c = 1e-6

        # 计算振荡频率
        omega_0 = 1 / np.sqrt(l * c)
        f_0 = omega_0 / (2 * np.pi)
        period = 1 / f_0

        t_step = period / 100
        t_stop = 10 * period

        result = solve_rlc_circuit(v_in, r, l, c, t_step, t_stop)

        # 验证有振荡 (过冲)
        output_node = 3  # 电容节点
        max_voltage = np.max(result.node_voltages[output_node])

        # 欠阻尼系统应有超过输入电压的过冲
        assert max_voltage > v_in

    def test_step_response(self):
        """测试阶跃响应"""
        r = 1000
        c = 1e-6
        tau = r * c

        t_step = tau / 100
        t_stop = 5 * tau

        time, voltage = step_response(r, c, t_step, t_stop)

        # 验证最终值
        assert voltage[-1] == pytest.approx(1.0, rel=0.01)

        # 验证单调上升
        for i in range(1, len(voltage)):
            assert voltage[i] >= voltage[i - 1] - 1e-10

    def test_trapezoidal_vs_backward_euler(self):
        """测试梯形法与后向欧拉法的精度差异"""
        v_in = 1.0
        r = 1000
        c = 1e-6
        tau = r * c

        t_step = tau / 10
        t_stop = 5 * tau

        # 创建电路
        circuit = Circuit("RC Circuit")
        circuit.add_voltage_source("V1", 0, 1, v_in)
        circuit.add_resistor("R1", 1, 2, r)
        circuit.add_capacitor("C1", 2, 0, c)
        circuit.build_node_map()

        # 梯形法
        analyzer_trap = TransientAnalysis(circuit, method="trapezoidal")
        result_trap = analyzer_trap.solve(t_step, t_stop)

        # 后向欧拉法
        analyzer_be = TransientAnalysis(circuit, method="backward_euler")
        result_be = analyzer_be.solve(t_step, t_stop)

        # 两种方法都应收敛到相同值
        assert result_trap.node_voltages[2][-1] == pytest.approx(v_in, rel=0.01)
        assert result_be.node_voltages[2][-1] == pytest.approx(v_in, rel=0.01)

    def test_time_points(self):
        """测试时间点"""
        v_in = 1.0
        r = 1000
        c = 1e-6

        t_step = 1e-5
        t_stop = 1e-3

        result = solve_rc_circuit(v_in, r, c, t_step, t_stop)

        # 验证时间点数量
        expected_points = int(t_stop / t_step) + 1
        assert len(result.time) == expected_points

        # 验证时间步长
        for i in range(1, len(result.time)):
            assert result.time[i] - result.time[i - 1] == pytest.approx(t_step)

    def test_voltage_source_ac(self):
        """测试交流电压源瞬态"""
        circuit = Circuit("AC Source")
        circuit.add_voltage_source("V1", 0, 1, 0, frequency=1000, ac_mag=5)
        circuit.add_resistor("R1", 1, 0, 1000)
        circuit.build_node_map()

        analyzer = TransientAnalysis(circuit)

        t_step = 1e-5
        t_stop = 2e-3  # 2 个周期

        result = analyzer.solve(t_step, t_stop)

        # 验证节点 1 有交流波形
        output_node = 1
        max_v = np.max(result.node_voltages[output_node])
        min_v = np.min(result.node_voltages[output_node])

        assert max_v == pytest.approx(5.0, rel=0.1)
        assert min_v == pytest.approx(-5.0, rel=0.1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
