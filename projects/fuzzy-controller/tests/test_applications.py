"""
应用模块测试
"""

import pytest
import numpy as np
from src.applications import TemperatureController, SpeedController


class TestTemperatureController:
    """温度控制器测试"""

    def test_basic_operation(self):
        """测试基本操作"""
        controller = TemperatureController(setpoint=25.0)

        # 低于设定值，应该加热
        power = controller.compute(current_temp=20.0)
        assert power > 0, "温度低于设定值时应加热"

    def test_above_setpoint(self):
        """测试高于设定值"""
        controller = TemperatureController(setpoint=25.0)

        # 高于设定值，应该制冷
        power = controller.compute(current_temp=30.0)
        assert power < 0, "温度高于设定值时应制冷"

    def test_at_setpoint(self):
        """测试在设定值附近"""
        controller = TemperatureController(setpoint=25.0)

        # 接近设定值，功率应该很小
        power = controller.compute(current_temp=25.0)
        assert abs(power) < 50, "接近设定值时功率应较小"

    def test_output_range(self):
        """测试输出范围"""
        controller = TemperatureController(setpoint=25.0)

        for temp in [0, 10, 20, 25, 30, 40, 50]:
            power = controller.compute(current_temp=temp)
            assert -100 <= power <= 100, f"功率 {power} 超出范围"

    def test_monotonicity(self):
        """测试单调性：温度越低，加热功率越大"""
        controller = TemperatureController(setpoint=25.0)
        controller.reset()

        temperatures = [10, 15, 20, 25, 30, 35, 40]
        powers = []

        for temp in temperatures:
            controller.reset()
            power = controller.compute(current_temp=temp)
            powers.append(power)

        # 验证趋势：温度越低，功率越大(更倾向于加热)
        for i in range(len(powers) - 1):
            assert powers[i] >= powers[i + 1] - 10, \
                f"温度 {temperatures[i]}°C 到 {temperatures[i+1]}°C, " \
                f"功率从 {powers[i]} 到 {powers[i+1]}"

    def test_reset(self):
        """测试重置"""
        controller = TemperatureController(setpoint=25.0)
        controller.compute(current_temp=20.0)
        controller.reset()
        assert controller._prev_error == 0.0

    def test_different_methods(self):
        """测试不同去模糊化方法"""
        for method in ['cog', 'mom']:
            controller = TemperatureController(setpoint=25.0, method=method)
            power = controller.compute(current_temp=20.0)
            assert -100 <= power <= 100


class TestSpeedController:
    """速度控制器测试"""

    def test_basic_operation(self):
        """测试基本操作"""
        controller = SpeedController(setpoint=60.0)

        # 低于设定值，应该加速
        throttle = controller.compute(current_speed=40.0)
        assert throttle > 0, "速度低于设定值时应加速"

    def test_above_setpoint(self):
        """测试高于设定值"""
        controller = SpeedController(setpoint=60.0)

        # 高于设定值，应该制动
        throttle = controller.compute(current_speed=80.0)
        assert throttle < 0, "速度高于设定值时应制动"

    def test_at_setpoint(self):
        """测试在设定值附近"""
        controller = SpeedController(setpoint=60.0)

        # 接近设定值
        throttle = controller.compute(current_speed=60.0)
        assert abs(throttle) < 50, "接近设定值时油门应较小"

    def test_output_range(self):
        """测试输出范围"""
        controller = SpeedController(setpoint=60.0)

        for speed in [0, 30, 50, 60, 70, 90, 120]:
            controller.reset()
            throttle = controller.compute(current_speed=speed)
            assert -100 <= throttle <= 100, f"油门 {throttle} 超出范围"

    def test_monotonicity(self):
        """测试单调性"""
        controller = SpeedController(setpoint=60.0)

        speeds = [20, 30, 40, 50, 60, 70, 80, 100]
        throttles = []

        for speed in speeds:
            controller.reset()
            throttle = controller.compute(current_speed=speed)
            throttles.append(throttle)

        # 验证趋势
        for i in range(len(throttles) - 1):
            assert throttles[i] >= throttles[i + 1] - 10, \
                f"速度 {speeds[i]} 到 {speeds[i+1]}, " \
                f"油门从 {throttles[i]} 到 {throttles[i+1]}"

    def test_reset(self):
        """测试重置"""
        controller = SpeedController(setpoint=60.0)
        controller.compute(current_speed=40.0)
        controller.reset()
        assert controller._prev_error == 0.0

    def test_different_setpoints(self):
        """测试不同设定值"""
        for setpoint in [30, 60, 100]:
            controller = SpeedController(setpoint=setpoint)
            throttle = controller.compute(current_speed=setpoint - 20)
            assert throttle > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
