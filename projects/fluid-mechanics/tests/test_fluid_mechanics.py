#!/usr/bin/env python3
"""
流体力学基础 - 单元测试套件
"""

import sys
import os
import unittest
import numpy as np

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.bernoulli import BernoulliSolver
from src.pipe_flow import (
    darcy_weisbach_head_loss, darcy_weisbach_pressure_drop,
    flow_rate, average_velocity, PipeSegment, PipeNetwork,
    colebrook_friction_factor, swamee_jain_friction_factor,
    laminar_friction_factor
)
from src.reynolds import (
    reynolds_number, reynolds_number_kinematic, classify_flow_regime,
    critical_velocity, FlowRegimeAnalyzer, FLUID_PROPERTIES
)
from src.head_loss import (
    major_loss, minor_loss, total_minor_loss, total_head_loss,
    equivalent_length, HeadLossCalculator
)
from src.continuity import (
    cross_sectional_area, volumetric_flow_rate, average_velocity as cont_velocity,
    diameter_from_flow, continuity_solver, ContinuityAnalyzer
)
from src.pressure_drop import (
    elevation_pressure_change, frictional_pressure_drop,
    acceleration_pressure_drop, total_pressure_drop, PressureDropAnalyzer
)


class TestBernoulliSolver(unittest.TestCase):
    """伯努利方程求解器测试"""

    def setUp(self):
        self.solver = BernoulliSolver(density=998.2, gravity=9.81)

    def test_solve_for_pressure(self):
        """测试压力求解"""
        # 水平管道，速度增加，压力应降低
        p2 = self.solver.solve_for_pressure(200000, 1.0, 0, 2.0, 0)
        self.assertLess(p2, 200000, "速度增加时压力应降低")
        # 验证计算正确性
        expected = 200000 + 0.5 * 998.2 * (1.0**2 - 2.0**2)
        self.assertAlmostEqual(p2, expected, places=5)

    def test_solve_for_velocity(self):
        """测试速度求解"""
        v2 = self.solver.solve_for_velocity(200000, 1.0, 0, 180000, 0)
        expected = np.sqrt(1.0**2 + 2 * (200000 - 180000) / 998.2)
        self.assertAlmostEqual(v2, expected, places=5)

    def test_total_head(self):
        """测试总水头计算"""
        h = self.solver.total_head(200000, 2.0, 10.0)
        pressure_head = 200000 / (998.2 * 9.81)
        velocity_head = 2.0**2 / (2 * 9.81)
        expected = pressure_head + velocity_head + 10.0
        self.assertAlmostEqual(h, expected, places=5)

    def test_head_loss_beroulli(self):
        """测试水头损失计算"""
        # 点1能量高于点2
        h_loss = self.solver.head_loss_beroulli(
            200000, 1.0, 0, 180000, 2.0, 0
        )
        self.assertGreater(h_loss, 0, "水头损失应为正")

    def test_pressure_coefficient(self):
        """测试压力系数计算"""
        cp = self.solver.pressure_coefficient(150000, 200000, 5.0, 998.2)
        expected = (150000 - 200000) / (0.5 * 998.2 * 25)
        self.assertAlmostEqual(cp, expected, places=5)

    def test_negative_velocity_error(self):
        """测试速度计算中的负值错误"""
        with self.assertRaises(ValueError):
            self.solver.solve_for_velocity(100000, 1.0, 0, 300000, 0)


class TestPipeFlow(unittest.TestCase):
    """管道流动计算测试"""

    def test_laminar_friction_factor(self):
        """测试层流摩擦系数"""
        f = laminar_friction_factor(1000)
        expected = 64.0 / 1000
        self.assertAlmostEqual(f, expected, places=5)

    def test_swamee_jain_friction_factor(self):
        """测试Swamee-Jain摩擦系数"""
        f = swamee_jain_friction_factor(100000, 0.000046, 0.1)
        self.assertGreater(f, 0, "摩擦系数应为正")
        self.assertLess(f, 0.1, "摩擦系数应在合理范围内")

    def test_darcy_weisbach_laminar(self):
        """测试Darcy-Weisbach层流计算"""
        h = darcy_weisbach_head_loss(100, 0.1, 1.0, 1000, 0.0)
        self.assertGreater(h, 0, "水头损失应为正")

    def test_darcy_weisbach_turbulent(self):
        """测试Darcy-Weisbach湍流计算"""
        h = darcy_weisbach_head_loss(100, 0.1, 5.0, 500000, 0.000046)
        self.assertGreater(h, 0, "水头损失应为正")

    def test_flow_rate_calculation(self):
        """测试流量计算"""
        Q = flow_rate(0.1, 2.0)
        expected = np.pi * (0.05)**2 * 2.0
        self.assertAlmostEqual(Q, expected, places=6)

    def test_average_velocity_calculation(self):
        """测试平均速度计算"""
        v = average_velocity(0.01, 0.1)
        area = np.pi * (0.05)**2
        expected = 0.01 / area
        self.assertAlmostEqual(v, expected, places=6)

    def test_pipe_segment_reynolds(self):
        """测试管道段Reynolds数计算"""
        seg = PipeSegment(0.1, 100, fluid_density=998.2, fluid_viscosity=1.002e-3)
        re = seg.reynolds_number(1.0)
        expected = 998.2 * 1.0 * 0.1 / 1.002e-3
        self.assertAlmostEqual(re, expected, places=1)

    def test_pipe_segment_flow_regime(self):
        """测试流动状态判断"""
        seg = PipeSegment(0.1, 100, fluid_density=998.2, fluid_viscosity=1.002e-3)
        regime = seg.flow_regime(0.01)
        self.assertIn("层流", regime)

        regime = seg.flow_regime(5.0)
        self.assertIn("湍流", regime)

    def test_pipe_network_series(self):
        """测试串联管道网络计算"""
        network = PipeNetwork()
        network.add_segment(PipeSegment(0.1, 100, fluid_density=998.2, fluid_viscosity=1.002e-3))
        network.add_segment(PipeSegment(0.05, 50, fluid_density=998.2, fluid_viscosity=1.002e-3))
        result = network.compute_series()
        self.assertGreater(result["total_head_loss"], 0)
        self.assertEqual(len(result["segments"]), 2)


class TestReynoldsNumber(unittest.TestCase):
    """Reynolds数计算测试"""

    def test_reynolds_number_calculation(self):
        """测试Reynolds数计算"""
        re = reynolds_number(1.0, 0.1, 998.2, 1.002e-3)
        expected = 998.2 * 1.0 * 0.1 / 1.002e-3
        self.assertAlmostEqual(re, expected, places=1)

    def test_reynolds_kinematic(self):
        """测试运动粘度Reynolds数计算"""
        re = reynolds_number_kinematic(1.0, 0.1, 1.004e-6)
        expected = 1.0 * 0.1 / 1.004e-6
        self.assertAlmostEqual(re, expected, places=1)

    def test_classify_laminar(self):
        """测试层流分类"""
        result = classify_flow_regime(1000)
        self.assertEqual(result["regime"], "laminar")
        self.assertTrue(result["is_laminar"])
        self.assertFalse(result["is_turbulent"])

    def test_classify_turbulent(self):
        """测试湍流分类"""
        result = classify_flow_regime(100000)
        self.assertEqual(result["regume"], "turbulent")
        self.assertFalse(result["is_laminar"])
        self.assertTrue(result["is_turbulent"])

    def test_classify_transitional(self):
        """测试过渡流分类"""
        result = classify_flow_regime(3000)
        self.assertEqual(result["regime"], "transitional")

    def test_critical_velocity(self):
        """测试临界速度计算"""
        v_crit = critical_velocity(0.1, 998.2, 1.002e-3)
        expected = 2300 * 1.002e-3 / (998.2 * 0.1)
        self.assertAlmostEqual(v_crit, expected, places=4)

    def test_flow_regime_analyzer(self):
        """测试流动状态分析器"""
        analyzer = FlowRegimeAnalyzer("water_20c")
        result = analyzer.analyze(1.0, 0.1)
        self.assertIn("reynolds_number", result)
        self.assertIn("regime", result)

    def test_fluid_properties(self):
        """测试流体物性参数"""
        self.assertIn("water_20c", FLUID_PROPERTIES)
        self.assertEqual(FLUID_PROPERTIES["water_20c"]["density"], 998.2)
        self.assertEqual(FLUID_PROPERTIES["air_20c"]["density"], 1.204)


class TestHeadLoss(unittest.TestCase):
    """水头损失计算测试"""

    def test_major_loss(self):
        """测试沿程水头损失"""
        h = major_loss(100, 0.1, 2.0, 200000, 0.0)
        self.assertGreater(h, 0)

    def test_minor_loss(self):
        """测试局部水头损失"""
        h = minor_loss(2.0, 0.5)
        expected = 0.5 * 4.0 / (2 * 9.81)
        self.assertAlmostEqual(h, expected, places=5)

    def test_total_minor_loss(self):
        """测试总局部损失"""
        result = total_minor_loss(2.0, ["elbow_90_standard", "gate_valve_full_open"])
        self.assertGreater(result["total_minor_loss"], 0)
        self.assertEqual(len(result["components"]), 2)

    def test_total_head_loss(self):
        """测试总水头损失"""
        result = total_head_loss(100, 0.1, 2.0, 200000, 0.0)
        self.assertGreater(result["total_loss"], 0)
        self.assertGreater(result["major_loss"], 0)

    def test_equivalent_length(self):
        """测试等效长度计算"""
        L_eq = equivalent_length(0.5, 0.1, 200000, 0.0)
        self.assertGreater(L_eq, 0)

    def test_head_loss_calculator(self):
        """测试水头损失计算器"""
        calc = HeadLossCalculator()
        result = calc.calculate_system(100, 0.1, 0.01)
        self.assertIn("total_loss", result)
        self.assertIn("reynolds_number", result)


class TestContinuity(unittest.TestCase):
    """连续性方程测试"""

    def test_cross_sectional_area(self):
        """测试截面积计算"""
        area = cross_sectional_area(0.1)
        expected = np.pi * (0.05)**2
        self.assertAlmostEqual(area, expected, places=6)

    def test_volumetric_flow_rate(self):
        """测试体积流量计算"""
        area = np.pi * (0.05)**2
        Q = volumetric_flow_rate(area, 2.0)
        self.assertAlmostEqual(Q, area * 2.0, places=6)

    def test_average_velocity(self):
        """测试平均速度计算"""
        v = cont_velocity(0.01, np.pi * (0.05)**2)
        expected = 0.01 / (np.pi * (0.05)**2)
        self.assertAlmostEqual(v, expected, places=6)

    def test_diameter_from_flow(self):
        """测试管径计算"""
        d = diameter_from_flow(0.01, 2.0)
        self.assertGreater(d, 0)
        # 验证：用计算的管径应该得到正确的流量
        area = cross_sectional_area(d)
        self.assertAlmostEqual(area * 2.0, 0.01, places=5)

    def test_continuity_solver(self):
        """测试连续性方程求解"""
        # D1 = 0.1, v1 = 1.0, D2 = 0.05
        # v2 = v1 * (D1/D2)² = 1.0 * 4 = 4.0
        v2 = continuity_solver(0.1, 1.0, 0.05)
        self.assertAlmostEqual(v2, 4.0, places=5)

    def test_continuity_analyzer(self):
        """测试连续性分析器"""
        analyzer = ContinuityAnalyzer()
        analyzer.add_section(0.1, velocity=2.0)
        analyzer.add_section(0.05)
        result = analyzer.analyze()
        self.assertTrue(result["all_flows_equal"])


class TestPressureDrop(unittest.TestCase):
    """压力降分析测试"""

    def test_elevation_pressure_change(self):
        """测试高程压力变化"""
        dp = elevation_pressure_change(998.2, 9.81, 10)
        expected = 998.2 * 9.81 * 10
        self.assertAlmostEqual(dp, expected, places=1)

    def test_frictional_pressure_drop(self):
        """测试摩擦压力降"""
        dp = frictional_pressure_drop(100, 0.1, 2.0, 200000, 998.2, 0.0)
        self.assertGreater(dp, 0)

    def test_acceleration_pressure_drop(self):
        """测试加速度压力降"""
        dp = acceleration_pressure_drop(998.2, 5.0, 2.0)
        # v1 > v2, 所以 dp > 0 (压力降低)
        self.assertGreater(dp, 0)

    def test_total_pressure_drop(self):
        """测试总压力降"""
        result = total_pressure_drop(
            998.2, 9.81, 100, 0.1, 2.0, 200000, 0.0,
            height_change=0
        )
        self.assertGreater(result["total_drop"], 0)

    def test_pressure_drop_analyzer(self):
        """测试压力降分析器"""
        analyzer = PressureDropAnalyzer()
        analyzer.add_segment(100, 0.1, 0.000046, 0)
        analyzer.add_segment(50, 0.05, 0.000046, 10)
        result = analyzer.analyze(0.01)
        self.assertIn("total_pressure_drop", result)
        self.assertIn("pressure_profile", result)

    def test_find_required_pressure(self):
        """测试所需入口压力计算"""
        analyzer = PressureDropAnalyzer()
        analyzer.add_segment(100, 0.1, 0.000046)
        req_p = analyzer.find_required_pressure(0.01, min_outlet_pressure=100000)
        self.assertGreater(req_p, 100000)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def test_bernoulli_with_continuity(self):
        """测试伯努利方程与连续性方程的结合"""
        # 变径管道：D1=0.1m, D2=0.05m, v1=2m/s
        A1 = np.pi * (0.05)**2
        A2 = np.pi * (0.025)**2
        v2 = 2.0 * A1 / A2  # 连续性方程

        solver = BernoulliSolver(density=998.2, gravity=9.81)
        p2 = solver.solve_for_pressure(200000, 2.0, 0, v2, 0)

        # 验证：速度增加，压力降低
        self.assertLess(p2, 200000)

        # 验证总水头守恒（理想流体）
        h1 = solver.total_head(200000, 2.0, 0)
        h2 = solver.total_head(p2, v2, 0)
        self.assertAlmostEqual(h1, h2, places=5)

    def test_full_pipe_system(self):
        """测试完整管道系统分析"""
        # 设置管道
        seg = PipeSegment(0.1, 100, 'commercial_steel',
                         fluid_density=998.2, fluid_viscosity=1.002e-3)

        velocity = 2.0
        re = seg.reynolds_number(velocity)
        h_loss = seg.head_loss(velocity)
        dp = seg.pressure_drop(velocity)

        # 验证物理合理性
        self.assertGreater(re, 0)
        self.assertGreater(h_loss, 0)
        self.assertGreater(dp, 0)

        # 验证Reynolds数
        self.assertGreater(re, 4000)  # 应该是湍流

        # 验证流动状态
        regime = seg.flow_regime(velocity)
        self.assertIn("湍流", regime)


if __name__ == "__main__":
    unittest.main(verbosity=2)
