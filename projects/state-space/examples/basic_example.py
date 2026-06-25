"""
状态空间模型基本示例

演示状态空间模型的创建、仿真和分析
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.state_space_model import StateSpaceModel
from src.analysis import controllability_matrix, observability_matrix, is_controllable, is_observable


def main():
    print("=" * 60)
    print("状态空间模型基本示例")
    print("=" * 60)

    # 1. 定义系统矩阵
    # 离散时间二阶系统
    A = np.array([[0.9, 0.1],
                  [-0.1, 0.8]])
    B = np.array([[1.0],
                  [0.5]])
    C = np.array([[1.0, 0.0]])
    D = np.array([[0.0]])

    print("\n1. 系统矩阵:")
    print(f"A = \n{A}")
    print(f"B = \n{B}")
    print(f"C = \n{C}")
    print(f"D = \n{D}")

    # 2. 创建状态空间模型
    model = StateSpaceModel(A, B, C, D, dt=0.1)
    print(f"\n2. 模型信息: {model}")

    # 3. 系统分析
    print("\n3. 系统分析:")
    eigenvalues = model.get_eigenvalues()
    print(f"特征值: {eigenvalues}")
    print(f"系统稳定: {model.is_stable()}")

    # 可控性分析
    Co = controllability_matrix(A, B)
    print(f"\n可控性矩阵:\n{Co}")
    print(f"可控: {is_controllable(A, B)}")

    # 可观性分析
    Ob = observability_matrix(A, C)
    print(f"\n可观性矩阵:\n{Ob}")
    print(f"可观: {is_observable(A, C)}")

    # 4. 系统仿真
    print("\n4. 系统仿真:")

    # 阶跃响应
    x0 = np.array([0.0, 0.0])
    u_step = np.ones((50, 1))
    states_step, outputs_step = model.simulate(x0, u_step)
    print(f"阶跃响应最终输出: {outputs_step[-1, 0]:.4f}")

    # 脉冲响应
    u_impulse = np.zeros((50, 1))
    u_impulse[0, 0] = 1.0
    states_impulse, outputs_impulse = model.simulate(x0, u_impulse)
    print(f"脉冲响应最终输出: {outputs_impulse[-1, 0]:.4f}")

    # 零输入响应
    x0_free = np.array([1.0, 0.5])
    u_free = np.zeros((50, 1))
    states_free, outputs_free = model.simulate(x0_free, u_free)
    print(f"零输入响应最终状态: {states_free[-1]}")

    # 5. 可视化
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # 阶跃响应
    axes[0, 0].plot(outputs_step[:, 0], "b-", linewidth=2)
    axes[0, 0].set_xlabel("时间步")
    axes[0, 0].set_ylabel("输出")
    axes[0, 0].set_title("阶跃响应")
    axes[0, 0].grid(True)

    # 脉冲响应
    axes[0, 1].plot(outputs_impulse[:, 0], "r-", linewidth=2)
    axes[0, 1].set_xlabel("时间步")
    axes[0, 1].set_ylabel("输出")
    axes[0, 1].set_title("脉冲响应")
    axes[0, 1].grid(True)

    # 状态轨迹（零输入）
    axes[1, 0].plot(states_free[:, 0], "g-", label="x1", linewidth=2)
    axes[1, 0].plot(states_free[:, 1], "m-", label="x2", linewidth=2)
    axes[1, 0].set_xlabel("时间步")
    axes[1, 0].set_ylabel("状态值")
    axes[1, 0].set_title("零输入响应状态轨迹")
    axes[1, 0].legend()
    axes[1, 0].grid(True)

    # 相平面图
    axes[1, 1].plot(states_free[:, 0], states_free[:, 1], "b-", linewidth=2)
    axes[1, 1].plot(states_free[0, 0], states_free[0, 1], "go", markersize=10, label="起点")
    axes[1, 1].plot(states_free[-1, 0], states_free[-1, 1], "rs", markersize=10, label="终点")
    axes[1, 1].set_xlabel("x1")
    axes[1, 1].set_ylabel("x2")
    axes[1, 1].set_title("相平面图")
    axes[1, 1].legend()
    axes[1, 1].grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), "basic_response.png"), dpi=150)
    plt.close()

    print("\n5. 图表已保存到 examples/basic_response.png")
    print("\n示例完成!")


if __name__ == "__main__":
    main()
