"""
模糊控制器使用示例

本示例展示如何使用模糊控制器实现：
1. 基本温度控制 (Mamdani 推理)
2. 多输入多输出控制
3. Sugeno 推理
4. 温度控制应用 (TemperatureController)
5. 速度控制应用 (SpeedController)
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fuzzy_set import FuzzySet, TriangularMF, TrapezoidalMF, GaussianMF
from src.rule_engine import FuzzyRule
from src.controller import FuzzyController
from src.applications import TemperatureController, SpeedController


def basic_example():
    """基本使用示例"""
    print("=" * 60)
    print("1. 基本使用示例：温度控制风扇转速 (Mamdani)")
    print("=" * 60)

    # 1. 创建模糊控制器
    controller = FuzzyController(defuzzify_method='cog')

    # 2. 定义输入变量：温度
    temperature_sets = {
        'cold': FuzzySet('cold', TriangularMF('cold', 0, 0, 20)),
        'warm': FuzzySet('warm', TriangularMF('warm', 10, 20, 30)),
        'hot': FuzzySet('hot', TriangularMF('hot', 20, 40, 40))
    }
    controller.add_input_variable('temperature', temperature_sets)

    # 3. 定义输出变量：风扇转速
    fan_speed_sets = {
        'slow': FuzzySet('slow', TriangularMF('slow', 0, 0, 50)),
        'medium': FuzzySet('medium', TriangularMF('medium', 25, 50, 75)),
        'fast': FuzzySet('fast', TriangularMF('fast', 50, 100, 100))
    }
    controller.add_output_variable('fan_speed', fan_speed_sets, universe=(0, 100))

    # 4. 添加模糊规则
    rules = [
        FuzzyRule(
            antecedent=[('temperature', 'cold', 'IS')],
            consequent=[('fan_speed', 'slow')],
            weight=1.0
        ),
        FuzzyRule(
            antecedent=[('temperature', 'warm', 'IS')],
            consequent=[('fan_speed', 'medium')],
            weight=1.0
        ),
        FuzzyRule(
            antecedent=[('temperature', 'hot', 'IS')],
            consequent=[('fan_speed', 'fast')],
            weight=1.0
        )
    ]
    controller.add_rules(rules)

    # 5. 测试不同温度
    print("\n温度控制测试:")
    print("-" * 40)

    test_temperatures = [5, 10, 15, 20, 25, 30, 35]

    for temp in test_temperatures:
        output = controller.control({'temperature': temp})
        fan_speed = output['fan_speed']

        # 确定风扇状态
        if fan_speed < 30:
            status = "慢速"
        elif fan_speed < 60:
            status = "中速"
        else:
            status = "快速"

        print(f"温度: {temp:2d}°C -> 风扇转速: {fan_speed:5.1f}% ({status})")


def sugeno_example():
    """Sugeno 推理示例"""
    print("\n" + "=" * 60)
    print("2. Sugeno 推理示例")
    print("=" * 60)

    controller = FuzzyController()

    # 定义输入
    temp_sets = {
        'cold': FuzzySet('cold', TriangularMF('cold', 0, 0, 20)),
        'warm': FuzzySet('warm', TriangularMF('warm', 10, 20, 30)),
        'hot': FuzzySet('hot', TriangularMF('hot', 20, 40, 40))
    }
    controller.add_input_variable('temperature', temp_sets)

    # 添加规则
    controller.add_rule(FuzzyRule(
        antecedent=[('temperature', 'cold', 'IS')],
        consequent=[('power', 'low')]
    ))
    controller.add_rule(FuzzyRule(
        antecedent=[('temperature', 'warm', 'IS')],
        consequent=[('power', 'medium')]
    ))
    controller.add_rule(FuzzyRule(
        antecedent=[('temperature', 'hot', 'IS')],
        consequent=[('power', 'high')]
    ))

    # 零阶 Sugeno 参数: 每条规则的输出为常数
    # 规则1 (cold): 输出 20
    # 规则2 (warm): 输出 50
    # 规则3 (hot):  输出 90
    sugeno_params = {
        'power': [(20.0,), (50.0,), (90.0,)]
    }

    print("\n零阶 Sugeno (结论为常数):")
    print("-" * 40)
    for temp in [5, 15, 25, 35]:
        result, details = controller.control_sugeno(
            {'temperature': temp}, sugeno_params
        )
        print(f"温度: {temp:2d}°C -> 功率: {result['power']:5.1f}%")

    # 一阶 Sugeno 参数: f = p0 + p1*x
    # 规则1: f = 10 + 0.5*temp
    # 规则2: f = 20 + 1.0*temp
    # 规则3: f = 30 + 1.5*temp
    sugeno_params_linear = {
        'power': [(10.0, 0.5), (20.0, 1.0), (30.0, 1.5)]
    }

    print("\n一阶 Sugeno (结论为线性函数 f = p0 + p1*temp):")
    print("-" * 40)
    for temp in [5, 15, 25, 35]:
        result, details = controller.control_sugeno(
            {'temperature': temp}, sugeno_params_linear
        )
        print(f"温度: {temp:2d}°C -> 功率: {result['power']:5.1f}%")


def step_by_step_example():
    """逐步执行示例"""
    print("\n" + "=" * 60)
    print("3. 逐步执行示例：查看推理过程")
    print("=" * 60)

    # 创建简单的控制器
    controller = FuzzyController()

    # 定义输入
    temperature_sets = {
        'cold': FuzzySet('cold', TriangularMF('cold', 0, 0, 20)),
        'warm': FuzzySet('warm', TriangularMF('warm', 10, 20, 30)),
        'hot': FuzzySet('hot', TriangularMF('hot', 20, 40, 40))
    }
    controller.add_input_variable('temperature', temperature_sets)

    # 定义输出
    fan_speed_sets = {
        'slow': FuzzySet('slow', TriangularMF('slow', 0, 0, 50)),
        'medium': FuzzySet('medium', TriangularMF('medium', 25, 50, 75)),
        'fast': FuzzySet('fast', TriangularMF('fast', 50, 100, 100))
    }
    controller.add_output_variable('fan_speed', fan_speed_sets, universe=(0, 100))

    # 添加规则
    rules = [
        FuzzyRule(
            antecedent=[('temperature', 'cold', 'IS')],
            consequent=[('fan_speed', 'slow')]
        ),
        FuzzyRule(
            antecedent=[('temperature', 'warm', 'IS')],
            consequent=[('fan_speed', 'medium')]
        ),
        FuzzyRule(
            antecedent=[('temperature', 'hot', 'IS')],
            consequent=[('fan_speed', 'fast')]
        )
    ]
    controller.add_rules(rules)

    # 逐步执行
    temp = 25
    print(f"\n输入温度: {temp}°C")
    print("-" * 40)

    results = controller.control_step_by_step({'temperature': temp})

    # 显示模糊化结果
    print("\n  步骤1 - 模糊化:")
    for var_name, fuzzy_values in results['fuzzy_inputs'].items():
        print(f"    {var_name}:")
        for set_name, membership in fuzzy_values.items():
            print(f"      {set_name}: {membership:.3f}")

    # 显示规则激活
    print("\n  步骤2 - 规则激活:")
    for i, rule_info in enumerate(results['rule_activations']):
        print(f"    规则 {i+1}: {rule_info['rule']}")
        print(f"      激活强度: {rule_info['activation']:.3f}")

    # 显示精确输出
    print("\n  步骤3 - 去模糊化输出:")
    for var_name, value in results['crisp_outputs'].items():
        print(f"    {var_name}: {value:.1f}")


def temperature_application_example():
    """温度控制应用示例"""
    print("\n" + "=" * 60)
    print("4. 温度控制应用 (TemperatureController)")
    print("=" * 60)

    controller = TemperatureController(setpoint=25.0)

    print("\n设定温度: 25°C")
    print("-" * 50)
    print(f"{'当前温度':>10s}  {'误差':>8s}  {'功率':>8s}  {'状态'}")
    print("-" * 50)

    for temp in [10, 15, 20, 22, 25, 28, 30, 35, 40]:
        controller.reset()
        power = controller.compute(current_temp=temp)
        error = 25 - temp

        if power > 10:
            status = "强加热"
        elif power > 0:
            status = "弱加热"
        elif power > -10:
            status = "关闭"
        elif power > -50:
            status = "弱制冷"
        else:
            status = "强制冷"

        print(f"{temp:>8d}°C  {error:>+6.1f}°C  {power:>+6.1f}%  {status}")


def speed_application_example():
    """速度控制应用示例"""
    print("\n" + "=" * 60)
    print("5. 速度控制应用 (SpeedController)")
    print("=" * 60)

    controller = SpeedController(setpoint=60.0)

    print("\n设定速度: 60 km/h")
    print("-" * 55)
    print(f"{'当前速度':>10s}  {'误差':>8s}  {'油门':>8s}  {'状态'}")
    print("-" * 55)

    for speed in [0, 20, 40, 50, 60, 70, 80, 100, 120]:
        controller.reset()
        throttle = controller.compute(current_speed=speed)
        error = 60 - speed

        if throttle > 10:
            status = "强加速"
        elif throttle > 0:
            status = "弱加速"
        elif throttle > -10:
            status = "滑行"
        elif throttle > -50:
            status = "弱制动"
        else:
            status = "强制动"

        print(f"{speed:>8d}km/h  {error:>+6.1f}km/h  {throttle:>+6.1f}%  {status}")


if __name__ == '__main__':
    basic_example()
    sugeno_example()
    step_by_step_example()
    temperature_application_example()
    speed_application_example()
