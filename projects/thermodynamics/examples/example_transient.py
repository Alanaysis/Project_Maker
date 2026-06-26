"""
示例 3: 瞬态热传递

演示瞬态热传导过程：
- 初始温度分布
- 随时间演化的温度场
- 达到稳态的过程

物理场景：
    一根金属杆，一端突然加热，观察温度波沿杆的传播。
    这类似于热波的传播过程。

关键概念：
- 热扩散深度 δ ≈ √(αt)
- 温度扰动以有限速度传播
- 傅里叶数 Fo = αt/L²
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import matplotlib.pyplot as plt
from src.heat_conduction import heat_conduction_1d
from src.heat_source import UniformHeatSource, TimeVaryingHeatSource
from src.analysis import thermal_time_constant, fourier_number

# ===== 物理参数 =====
L = 0.05      # 杆长 (m)
nx = 100      # 网格数
alpha = 1e-5  # 热扩散系数 (m²/s)

# ===== 计算参数 =====
tau = thermal_time_constant(L, alpha)
print(f"热时间常数 τ = {tau:.1f} s")

dx = L / (nx - 1)
dt = 0.49 * dx ** 2 / alpha  # Fo = 0.49 (接近稳定极限)
nt = 1000

print(f"空间步长 dx = {dx*1000:.3f} mm")
print(f"时间步长 dt = {dt:.4f} s")
print(f"傅里叶数 Fo = {fourier_number(L, alpha, nt * dt):.2f}")
print(f"总模拟时间 = {nt * dt:.1f} s = {nt * dt / tau:.1f}τ")

# ===== 热源: 周期性变化的热源 =====
# 在杆的左半部分施加周期性热源
def periodic_source(x):
    """在 x < L/2 区域施加正弦热源"""
    if x < L / 2:
        return 2000 * np.sin(2 * np.pi * 0.01 * nt * dt) ** 2
    return 0

# ===== 求解 =====
x, T_history = heat_conduction_1d(
    L=L,
    nx=nx,
    alpha=alpha,
    dt=dt,
    nt=nt,
    T_left=100.0,
    T_right=0.0,
    T_initial=20.0,
    heat_source=periodic_source,
    method="explicit",
)

# ===== 可视化 =====
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 图 1: 温度随时间和空间的演化
ax1 = axes[0, 0]
time_array = np.arange(nt + 1) * dt
X_grid, Y_grid = np.meshgrid(x * 1000, time_array, indexing="ij")
im1 = ax1.pcolormesh(X_grid, Y_grid, T_history, cmap="hot", shading="auto", origin="lower")
ax1.set_xlabel("距离 x (mm)")
ax1.set_ylabel("时间 (s)")
ax1.set_title("温度场随时间和空间演化")
plt.colorbar(im1, ax=ax1, label="°C")

# 图 2: 不同位置温度随时间变化
ax2 = axes[0, 1]
positions = [0.1, 0.3, 0.5, 0.7, 0.9]  # 归一化位置
colors = plt.cm.viridis(np.linspace(0, 1, len(positions)))
for pos, color in zip(positions, colors):
    idx = int(pos * (nx - 1))
    t_axis = np.arange(nt + 1) * dt
    ax2.plot(t_axis, T_history[:, idx], color=color, linewidth=1.5, label=f"x={pos*L*1000:.1f}mm")
ax2.set_xlabel("时间 (s)")
ax2.set_ylabel("温度 (°C)")
ax2.set_title("各位置温度随时间变化")
ax2.legend()
ax2.grid(True, alpha=0.3)

# 图 3: 几个关键时间点的温度分布
ax3 = axes[1, 0]
time_steps = [0, nt // 10, nt // 5, nt // 2, nt]
for step in time_steps:
    ax3.plot(x * 1000, T_history[step], linewidth=1.5, label=f"t={step*dt:.1f}s")
ax3.set_xlabel("距离 x (mm)")
ax3.set_ylabel("温度 T (°C)")
ax3.set_title("关键时间点的温度分布")
ax3.legend()
ax3.grid(True, alpha=0.3)

# 图 4: 热流密度随时间变化
ax4 = axes[1, 1]
# 计算边界热流: q = -k * dT/dx
k = alpha * 1000 * 7800 * 500  # 假设钢: ρ=7800, c=500, 反推 k
# 简化: 直接计算温度梯度
dT_dx_left = (T_history[:, 1] - T_history[:, 0]) / dx
dT_dx_right = (T_history[:, -1] - T_history[:, -2]) / dx

t_axis = np.arange(nt + 1) * dt
ax4.plot(t_axis, -alpha * 1000 * dT_dx_left, "b-", linewidth=1.5, label="左边界热流")
ax4.plot(t_axis, -alpha * 1000 * dT_dx_right, "r-", linewidth=1.5, label="右边界热流")
ax4.set_xlabel("时间 (s)")
ax4.set_ylabel("热流密度 (W/m²)")
ax4.set_title("边界热流密度随时间")
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(__file__), "example3_transient.png"), dpi=150, bbox_inches="tight")
plt.show()

print(f"\n最终稳态温度范围: [{T_history[-1].min():.2f}, {T_history[-1].max():.2f}] °C")
print(f"最终平均温度: {T_history[-1].mean():.2f} °C")
