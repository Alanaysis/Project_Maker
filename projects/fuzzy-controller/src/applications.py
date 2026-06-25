"""
实际应用模块

提供预配置的模糊控制器应用:
- 温度控制 (TemperatureController)
- 速度控制 (SpeedController)

每个应用类封装了完整的模糊控制系统配置，
包括隶属函数、规则库和控制逻辑。
"""

import numpy as np
from typing import Dict, List, Tuple
from .fuzzy_set import FuzzySet, TriangularMF, TrapezoidalMF, GaussianMF
from .rule_engine import FuzzyRule
from .controller import FuzzyController


class TemperatureController:
    """
    模糊温度控制器

    用于控制加热/制冷系统的功率输出。

    输入变量:
        - temperature_error: 温度误差 (设定值 - 实际值), 范围 [-20, 20]°C
        - error_change: 误差变化率, 范围 [-10, 10]°C/s

    输出变量:
        - heater_power: 加热器功率, 范围 [-100, 100]%
            正值=加热, 负值=制冷

    模糊规则 (9 条):
        误差大负 + 变化率负 → 强制冷
        误差零   + 变化率零 → 关闭
        误差大正 + 变化率正 → 强加热
        ...

    使用示例:
        controller = TemperatureController(setpoint=25.0)
        power = controller.compute(current_temp=20.0)
    """

    def __init__(self, setpoint: float = 25.0, method: str = 'cog'):
        """
        初始化温度控制器

        参数:
            setpoint: 温度设定值 (°C)
            method: 去模糊化方法
        """
        self.setpoint = setpoint
        self.controller = FuzzyController(defuzzify_method=method)
        self._prev_error = 0.0
        self._build_system()

    def _build_system(self):
        """构建模糊控制系统"""
        # ---- 输入1: 温度误差 ----
        error_sets = {
            'negative_big': FuzzySet('negative_big',
                                     TriangularMF('nb', -20, -20, -10)),
            'negative_small': FuzzySet('negative_small',
                                       TriangularMF('ns', -15, -5, 0)),
            'zero': FuzzySet('zero',
                             TriangularMF('ze', -5, 0, 5)),
            'positive_small': FuzzySet('positive_small',
                                       TriangularMF('ps', 0, 5, 15)),
            'positive_big': FuzzySet('positive_big',
                                     TriangularMF('pb', 10, 20, 20)),
        }
        self.controller.add_input_variable('error', error_sets)

        # ---- 输入2: 误差变化率 ----
        change_sets = {
            'negative': FuzzySet('negative',
                                 TriangularMF('neg', -10, -10, 0)),
            'zero': FuzzySet('zero',
                             TriangularMF('ze', -5, 0, 5)),
            'positive': FuzzySet('positive',
                                 TriangularMF('pos', 0, 10, 10)),
        }
        self.controller.add_input_variable('change', change_sets)

        # ---- 输出: 加热器功率 ----
        power_sets = {
            'cool_strong': FuzzySet('cool_strong',
                                    TriangularMF('cs', -100, -100, -50)),
            'cool_weak': FuzzySet('cool_weak',
                                  TriangularMF('cw', -80, -30, 0)),
            'off': FuzzySet('off',
                            TriangularMF('off', -30, 0, 30)),
            'heat_weak': FuzzySet('heat_weak',
                                  TriangularMF('hw', 0, 30, 80)),
            'heat_strong': FuzzySet('heat_strong',
                                    TriangularMF('hs', 50, 100, 100)),
        }
        self.controller.add_output_variable('power', power_sets, universe=(-100, 100))

        # ---- 模糊规则 (5x3 规则表) ----
        rules = [
            # 误差负大 → 不管变化率，都需要制冷
            FuzzyRule([('error', 'negative_big', 'IS'), ('change', 'negative', 'IS')],
                      [('power', 'cool_strong')], 'AND'),
            FuzzyRule([('error', 'negative_big', 'IS'), ('change', 'zero', 'IS')],
                      [('power', 'cool_strong')], 'AND'),
            FuzzyRule([('error', 'negative_big', 'IS'), ('change', 'positive', 'IS')],
                      [('power', 'cool_weak')], 'AND'),

            # 误差负小
            FuzzyRule([('error', 'negative_small', 'IS'), ('change', 'negative', 'IS')],
                      [('power', 'cool_weak')], 'AND'),
            FuzzyRule([('error', 'negative_small', 'IS'), ('change', 'zero', 'IS')],
                      [('power', 'cool_weak')], 'AND'),
            FuzzyRule([('error', 'negative_small', 'IS'), ('change', 'positive', 'IS')],
                      [('power', 'off')], 'AND'),

            # 误差零
            FuzzyRule([('error', 'zero', 'IS'), ('change', 'negative', 'IS')],
                      [('power', 'cool_weak')], 'AND'),
            FuzzyRule([('error', 'zero', 'IS'), ('change', 'zero', 'IS')],
                      [('power', 'off')], 'AND'),
            FuzzyRule([('error', 'zero', 'IS'), ('change', 'positive', 'IS')],
                      [('power', 'heat_weak')], 'AND'),

            # 误差正小
            FuzzyRule([('error', 'positive_small', 'IS'), ('change', 'negative', 'IS')],
                      [('power', 'off')], 'AND'),
            FuzzyRule([('error', 'positive_small', 'IS'), ('change', 'zero', 'IS')],
                      [('power', 'heat_weak')], 'AND'),
            FuzzyRule([('error', 'positive_small', 'IS'), ('change', 'positive', 'IS')],
                      [('power', 'heat_weak')], 'AND'),

            # 误差正大
            FuzzyRule([('error', 'positive_big', 'IS'), ('change', 'negative', 'IS')],
                      [('power', 'heat_weak')], 'AND'),
            FuzzyRule([('error', 'positive_big', 'IS'), ('change', 'zero', 'IS')],
                      [('power', 'heat_strong')], 'AND'),
            FuzzyRule([('error', 'positive_big', 'IS'), ('change', 'positive', 'IS')],
                      [('power', 'heat_strong')], 'AND'),
        ]
        self.controller.add_rules(rules)

    def compute(self, current_temp: float) -> float:
        """
        计算控制输出

        参数:
            current_temp: 当前温度 (°C)

        返回:
            加热器功率 (%), 正值加热，负值制冷
        """
        error = self.setpoint - current_temp
        change = error - self._prev_error
        self._prev_error = error

        output = self.controller.control({
            'error': max(-20, min(20, error)),
            'change': max(-10, min(10, change))
        })

        return max(-100, min(100, output['power']))

    def reset(self):
        """重置控制器状态"""
        self._prev_error = 0.0


class SpeedController:
    """
    模糊速度控制器

    用于控制电机或车辆的速度。

    输入变量:
        - speed_error: 速度误差 (设定值 - 实际值), 范围 [-50, 50] km/h
        - error_change: 误差变化率, 范围 [-20, 20] km/h/s

    输出变量:
        - throttle: 油门/驱动量, 范围 [-100, 100]%
            正值=加速, 负值=制动

    使用示例:
        controller = SpeedController(setpoint=60.0)
        throttle = controller.compute(current_speed=50.0)
    """

    def __init__(self, setpoint: float = 60.0, method: str = 'cog'):
        """
        初始化速度控制器

        参数:
            setpoint: 速度设定值 (km/h)
            method: 去模糊化方法
        """
        self.setpoint = setpoint
        self.controller = FuzzyController(defuzzify_method=method)
        self._prev_error = 0.0
        self._build_system()

    def _build_system(self):
        """构建模糊控制系统"""
        # ---- 输入1: 速度误差 ----
        error_sets = {
            'negative_big': FuzzySet('negative_big',
                                     TriangularMF('nb', -50, -50, -20)),
            'negative_small': FuzzySet('negative_small',
                                       TriangularMF('ns', -30, -10, 0)),
            'zero': FuzzySet('zero',
                             TriangularMF('ze', -10, 0, 10)),
            'positive_small': FuzzySet('positive_small',
                                       TriangularMF('ps', 0, 10, 30)),
            'positive_big': FuzzySet('positive_big',
                                     TriangularMF('pb', 20, 50, 50)),
        }
        self.controller.add_input_variable('error', error_sets)

        # ---- 输入2: 误差变化率 ----
        change_sets = {
            'negative': FuzzySet('negative',
                                 TriangularMF('neg', -20, -20, 0)),
            'zero': FuzzySet('zero',
                             TriangularMF('ze', -10, 0, 10)),
            'positive': FuzzySet('positive',
                                 TriangularMF('pos', 0, 20, 20)),
        }
        self.controller.add_input_variable('change', change_sets)

        # ---- 输出: 油门/驱动量 ----
        throttle_sets = {
            'brake_strong': FuzzySet('brake_strong',
                                     TriangularMF('bs', -100, -100, -50)),
            'brake_weak': FuzzySet('brake_weak',
                                   TriangularMF('bw', -80, -30, 0)),
            'coast': FuzzySet('coast',
                              TriangularMF('coast', -30, 0, 30)),
            'accel_weak': FuzzySet('accel_weak',
                                   TriangularMF('aw', 0, 30, 80)),
            'accel_strong': FuzzySet('accel_strong',
                                     TriangularMF('as', 50, 100, 100)),
        }
        self.controller.add_output_variable('throttle', throttle_sets, universe=(-100, 100))

        # ---- 模糊规则 ----
        rules = [
            # 误差负大 → 需要制动
            FuzzyRule([('error', 'negative_big', 'IS'), ('change', 'negative', 'IS')],
                      [('throttle', 'brake_strong')], 'AND'),
            FuzzyRule([('error', 'negative_big', 'IS'), ('change', 'zero', 'IS')],
                      [('throttle', 'brake_strong')], 'AND'),
            FuzzyRule([('error', 'negative_big', 'IS'), ('change', 'positive', 'IS')],
                      [('throttle', 'brake_weak')], 'AND'),

            # 误差负小
            FuzzyRule([('error', 'negative_small', 'IS'), ('change', 'negative', 'IS')],
                      [('throttle', 'brake_weak')], 'AND'),
            FuzzyRule([('error', 'negative_small', 'IS'), ('change', 'zero', 'IS')],
                      [('throttle', 'brake_weak')], 'AND'),
            FuzzyRule([('error', 'negative_small', 'IS'), ('change', 'positive', 'IS')],
                      [('throttle', 'coast')], 'AND'),

            # 误差零
            FuzzyRule([('error', 'zero', 'IS'), ('change', 'negative', 'IS')],
                      [('throttle', 'brake_weak')], 'AND'),
            FuzzyRule([('error', 'zero', 'IS'), ('change', 'zero', 'IS')],
                      [('throttle', 'coast')], 'AND'),
            FuzzyRule([('error', 'zero', 'IS'), ('change', 'positive', 'IS')],
                      [('throttle', 'accel_weak')], 'AND'),

            # 误差正小
            FuzzyRule([('error', 'positive_small', 'IS'), ('change', 'negative', 'IS')],
                      [('throttle', 'coast')], 'AND'),
            FuzzyRule([('error', 'positive_small', 'IS'), ('change', 'zero', 'IS')],
                      [('throttle', 'accel_weak')], 'AND'),
            FuzzyRule([('error', 'positive_small', 'IS'), ('change', 'positive', 'IS')],
                      [('throttle', 'accel_weak')], 'AND'),

            # 误差正大 → 需要加速
            FuzzyRule([('error', 'positive_big', 'IS'), ('change', 'negative', 'IS')],
                      [('throttle', 'accel_weak')], 'AND'),
            FuzzyRule([('error', 'positive_big', 'IS'), ('change', 'zero', 'IS')],
                      [('throttle', 'accel_strong')], 'AND'),
            FuzzyRule([('error', 'positive_big', 'IS'), ('change', 'positive', 'IS')],
                      [('throttle', 'accel_strong')], 'AND'),
        ]
        self.controller.add_rules(rules)

    def compute(self, current_speed: float) -> float:
        """
        计算控制输出

        参数:
            current_speed: 当前速度 (km/h)

        返回:
            油门量 (%), 正值加速，负值制动
        """
        error = self.setpoint - current_speed
        change = error - self._prev_error
        self._prev_error = error

        output = self.controller.control({
            'error': max(-50, min(50, error)),
            'change': max(-20, min(20, change))
        })

        return max(-100, min(100, output['throttle']))

    def reset(self):
        """重置控制器状态"""
        self._prev_error = 0.0
