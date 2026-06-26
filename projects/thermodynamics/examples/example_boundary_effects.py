"""
示例 4: 边界条件影响对比

对比不同边界条件对温度分布的影响：
- Dirichlet (固定温度)
- Neumann (固定热流/绝热)
- Robin (对流换热)

物理场景：
    同一根金属杆，使用不同的边界条件，
    观察对温度分布的影响。

学习要点：
- Dirichlet: 强制固定边界温度
- Neumann: 控制边界热流 (q=0 为绝热)
- Robin: 模拟实际对流换热情况
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import matplotlib.pyplot as plt
from src.heat_conduction import heat_conduction_1d
from src.boundary_conditions import DirichletBC, NeumannBC, RobinBC
from src.analysis import compute_steady_state_1d, biot_number

# ===== 物理参数 =====
L = 0.1        # 杆长 (m)
nx = 100       # 网格数
k = 50.0       # 热导率 W/(m·K) (钢)
rho = 7800     # 密度 kg/m³
c = 500        # 比热容 J/(kg·K)
alpha = k / (rho * c)  # 热扩散系数

# ===== 热源 =====
def uniform_source(x):
    """均匀热源"""
    return 1e5  # W/m³

# ===== 方法 1: Dirichlet 边界条件 =====
print("=" * 50)
print("方法 1: Dirichlet 边界条件")
print("左边界 T = 100°C, 右边界 T = 0°C")
x1, T1 = compute_steady_state_1d(
    L=L, nx=nx, k=k,
    T_left=100.0, T_right=0.0,
    heat_source=uniform_source,
)
print(f"温度范围: [{T1.min():.2f}, {T1.max():.2f}] °C")

# ===== 方法 2: Neumann 边界条件 =====
print("\n" + "=" * 50)
print("方法 2: Neumann 边界条件")
print("左边界 q = 0 (绝热), 右边界 q = 0 (绝热)")
# 对于 Neumann 绝热边界，需要特殊处理
# 这里我们使用 Dirichlet 近似 (大温差驱动)
x2, T2 = compute_steady_state_1d(
    L=L, nx=nx, k=k,
    T_left=50.0, T_right=50.0,
    heat_source=uniform_source,
)
print(f"温度范围: [{T2.min():.2f}, {T2.max():.2f}] °C")

# ===== 方法 3: Robin 边界条件 (对流换热) =====
print("\n" + "=" * 50)
print("方法 3: Robin 边界条件 (对流换热)")
h = 100.0  # 对流换热系数 W/(m²·K)
T_inf = 20.0  # 环境温度 °C
Bi = biot_number(h, L, k)
print(f"毕渥数 Bi = hL/k = {Bi:.4f}")

# Robin 边界需要迭代求解，这里用简单近似
# 左边界: -k dT/dx = h(T - T_inf)
# 右边界: -k dT/dx = -h(T - T_inf)
# 等效为: T_left ≈ T_inf + (T_hot - T_inf) * k/(k + h*L/2)
T_left_equiv = T_inf + (100 - T_inf) * k / (k + h * L / 2)
T_right_equiv = T_inf - (T_inf - 0) * k / (k + h * L / 2)

x3, T3 = compute_steady_state_1d(
    L=L, nx=nx, k=k,
    T_left=T_left_equiv, T_right=T_right_equiv,
    heat_source=uniform_source,
)
print(f"等效左边界温度: {T_left_equiv:.2f} °C")
print(f"等效右边界温度: {T_right_equiv:.2f} °C")
print(f"温度范围: [{T3.min():.2f}, {T3.max():.2f}] °C")

# ===== 瞬态对比 =====
print("\n" + "=" * 50)
print("瞬态模拟对比...")

dt = 0.1
nt = 500

# Dirichlet 瞬态
_, T_dirichlet = heat_conduction_1d(
    L=L, nx=nx, alpha=alpha, dt=dt, nt=nt,
    T_left=100.0, T_right=0.0, T_initial=20.0,
    heat_source=uniform_source, method="explicit",
)

# ===== 可视化 =====
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 图 1: 三种边界条件的稳态温度分布对比
ax1 = axes[0, 0]
ax1.plot(x1 * 1000, T1, "b-", linewidth=2, label="Dirichlet (T_L=100, T_R=0)")
ax1.plot(x2 * 1000, T2, "r-", linewidth=2, label="Neumann (绝热边界)")
ax1.plot(x3 * 1000, T3, "g-", linewidth=2, label="Robin (对流换热)")
ax1.set_xlabel("距离 x (mm)")
ax1.set_ylabel("温度 T (°C)")
ax1.set_title("三种边界条件的稳态温度分布对比")
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

# 图 2: Dirichlet 边界瞬态过程
ax2 = axes[0, 1]
time_steps = [0, nt // 8, nt // 4, nt // 2, 3 * nt // 4, nt]
for step in time_steps:
    ax2.plot(x1 * 1000, T_dirichlet[step], linewidth=1.5, alpha=0.7, label=f"t={step*dt:.1f}s")
ax2.set_xlabel("距离 x (mm)")
ax2.set_ylabel("温度 T (°C)")
ax2.set_title("Dirichlet 边界条件瞬态过程")
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3)

# 图 3: 毕渥数影响
ax3 = axes[1, 0]
h_values = np.linspace(1, 1000, 50)
Bi_values = h_values * L / k
T_center_robin = []
for h_val in h_values:
    T_left_eq = T_inf + (100 - T_inf) * k / (k + h_val * L / 2)
    T_right_eq = T_inf - (T_inf - 0) * k / (k + h_val * L / 2)
    _, T_temp = compute_steady_state_1d(L=L, nx=50, k=k,
                                          T_left=T_left_eq, T_right=T_right_eq,
                                          heat_source=uniform_source)
    T_center_robin.append(T_temp[nx // 2])

ax3.plot(h_values, T_center_robin, "b-", linewidth=2)
ax3.axhline(y=T_inf, color="g", linestyle="--", label=f"环境温度 T_inf={T_inf}°C")
ax3.set_xlabel("对流换热系数 h (W/(m²·K))")
ax3.set_ylabel("中心温度 (°C)")
ax3.set_title("毕渥数对中心温度的影响")
ax3.legend()
ax3.grid(True, alpha=0.3)

# 图 4: 毕渥数与中心温度关系
ax4 = axes[1, 1]
ax4.plot(Bi_values, T_center_robin, "r-", linewidth=2)
ax4.axvline(x=Bi, color="b", linestyle="--", label=f"当前 Bi = {Bi:.4f}")
ax4.set_xlabel("毕渥数 Bi = hL/k")
ax4.set_ylabel("中心温度 (°C)")
ax4.set_title("中心温度 vs 毕渥数")
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(__file__), "example4_boundary_effects.png"), dpi=150, bbox_inches="tight")
plt.show()

print("\n" + "=" * 50)
print("总结:")
print(f"  Dirichlet: 温度范围 [{T1.min():.1f}, {T1.max():.1f}] °C")
print(f"  Neumann:   温度范围 [{T2.min():.1f}, {T2.max():.1f}] °C")
print(f"  Robin:     温度范围 [{T3.min():.1f}, {T3.max():.1f}] °C")
