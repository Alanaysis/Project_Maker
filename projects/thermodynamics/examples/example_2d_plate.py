"""
示例 2: 二维平板的温度分布

演示二维热传导：
- 方形平板，不同边界条件
- 中心点热源
- 稳态温度分布

物理场景：
    一块正方形金属板，四边保持不同温度，
    中心有一个热源。观察达到稳态后的温度分布。

热传导方程：
    ∂T/∂t = α(∂²T/∂x² + ∂²T/∂y²) + Q/(ρc)

边界条件：
    左边: T = 100°C
    右边: T = 0°C
    上边: T = 50°C
    下边: T = 50°C
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import matplotlib.pyplot as plt
from src.heat_conduction import heat_conduction_2d
from src.heat_source import UniformHeatSource, PointHeatSource
from src.analysis import thermal_time_constant

# ===== 物理参数 =====
Lx = 0.2  # 板宽 (m)
Ly = 0.2  # 板高 (m)
nx, ny = 40, 40  # 网格数
alpha = 1e-5  # 热扩散系数 (m²/s)

# ===== 计算参数 =====
tau = thermal_time_constant(max(Lx, Ly), alpha)
print(f"热时间常数 τ = {tau:.1f} s")

dx = Lx / (nx - 1)
dt = 0.25 * dx ** 2 / alpha  # Fo = 0.25 for 2D stability
nt = 300

print(f"网格: {nx} x {ny}")
print(f"空间步长 dx = {dx*1000:.2f} mm")
print(f"总模拟时间 = {nt * dt:.1f} s = {nt * dt / tau:.1f}τ")

# ===== 热源 =====
# 在中心放置一个热源
center_x, center_y = Lx / 2, Ly / 2
Q0 = 5000  # 峰值热功率密度 (W/m³)
sigma = 0.02  # 热源宽度 (m)

def point_source(x, y):
    """高斯点热源"""
    r2 = (x - center_x) ** 2 + (y - center_y) ** 2
    return Q0 * np.exp(-r2 / (2 * sigma ** 2))

# ===== 求解 =====
x, y, T_history = heat_conduction_2d(
    Lx=Lx,
    Ly=Ly,
    nx=nx,
    ny=ny,
    alpha=alpha,
    dt=dt,
    nt=nt,
    T_left=100.0,
    T_right=0.0,
    T_top=50.0,
    T_bottom=50.0,
    T_initial=20.0,
    heat_source=point_source,
    method="crank_nicolson",
)

# ===== 可视化 =====
X, Y = np.meshgrid(x, y, indexing="ij")

fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# 图 1: 初始温度分布
ax1 = axes[0, 0]
im1 = ax1.pcolormesh(X * 1000, Y * 1000, T_history[0], cmap="hot", shading="auto")
ax1.set_xlabel("x (mm)")
ax1.set_ylabel("y (mm)")
ax1.set_title("初始温度分布")
plt.colorbar(im1, ax=ax1, label="°C")

# 图 2: 中间时刻温度分布
mid_step = nt // 4
ax2 = axes[0, 1]
im2 = ax2.pcolormesh(X * 1000, Y * 1000, T_history[mid_step], cmap="hot", shading="auto")
ax2.set_xlabel("x (mm)")
ax2.set_ylabel("y (mm)")
ax2.set_title(f"中间时刻 t = {mid_step * dt:.1f}s")
plt.colorbar(im2, ax=ax2, label="°C")

# 图 3: 稳态温度分布
ax3 = axes[1, 0]
im3 = ax3.pcolormesh(X * 1000, Y * 1000, T_history[-1], cmap="hot", shading="auto")
ax3.set_xlabel("x (mm)")
ax3.set_ylabel("y (mm)")
ax3.set_title("稳态温度分布")
plt.colorbar(im3, ax=ax3, label="°C")

# 图 4: 稳态等温线
ax4 = axes[1, 1]
levels = np.linspace(T_history[-1].min(), T_history[-1].max(), 20)
contour = ax4.contour(X * 1000, Y * 1000, T_history[-1], levels=levels, cmap="coolwarm")
ax4.clabel(contour, inline=True, fontsize=8)
ax4.set_xlabel("x (mm)")
ax4.set_ylabel("y (mm)")
ax4.set_title("稳态等温线")
ax4.set_aspect("equal")

plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(__file__), "example2_2d_plate.png"), dpi=150, bbox_inches="tight")
plt.show()

print(f"\n稳态最高温度: {T_history[-1].max():.2f} °C")
print(f"稳态最低温度: {T_history[-1].min():.2f} °C")
print(f"稳态平均温度: {T_history[-1].mean():.2f} °C")
