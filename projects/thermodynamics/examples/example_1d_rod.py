"""
示例 1: 一维杆的热传导

演示一维热传导的基本过程：
- 初始均匀温度
- 两端保持不同温度
- 观察温度场随时间的演化

物理场景：
    一根长度为 L 的金属杆，左端加热到 T_hot，右端冷却到 T_cold。
    观察热量如何从热端传导到冷端。

热传导方程：
    ∂T/∂t = α ∂²T/∂x²

边界条件 (Dirichlet):
    T(0,t) = T_hot
    T(L,t) = T_cold

初始条件：
    T(x,0) = T_initial
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import matplotlib.pyplot as plt
from src.heat_conduction import heat_conduction_1d
from src.analysis import thermal_time_constant, fourier_number

# ===== 物理参数 =====
L = 0.1          # 杆长 (m)
nx = 50          # 空间网格数
alpha = 1e-5     # 铝的热扩散系数 ≈ 1e-5 m²/s
T_hot = 100.0    # 热端温度 (°C)
T_cold = 0.0     # 冷端温度 (°C)
T_initial = 20.0 # 初始温度 (°C)

# ===== 计算参数 =====
# 使用热时间常数来确定时间步长和步数
tau = thermal_time_constant(L, alpha)  # ≈ 1000 s
print(f"热时间常数 τ = {tau:.1f} s")

# 显式方法的稳定性要求: Fo ≤ 0.5
dx = L / (nx - 1)
dt = 0.5 * dx ** 2 / alpha  # 取 Fo = 0.5
nt = 500  # 模拟 500 个时间步

print(f"空间步长 dx = {dx*1000:.2f} mm")
print(f"时间步长 dt = {dt:.2f} s")
print(f"傅里叶数 Fo = {0.5 * alpha * dt / dx**2:.4f}")
print(f"总模拟时间 = {nt * dt:.1f} s = {nt * dt / tau:.1f}τ")

# ===== 求解 =====
x, T_history = heat_conduction_1d(
    L=L,
    nx=nx,
    alpha=alpha,
    dt=dt,
    nt=nt,
    T_left=T_hot,
    T_right=T_cold,
    T_initial=T_initial,
    method="explicit",
)

# ===== 可视化 =====
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 图 1: 温度随时间和空间的变化 (瀑布图)
ax1 = axes[0, 0]
time_steps = [0, nt // 4, nt // 2, 3 * nt // 4, nt]
labels = [f"t = {i * dt:.0f}s"]
for i, step in enumerate(time_steps):
    if i > 0:
        labels.append(f"t = {step * dt:.0f}s")
    ax1.plot(x * 1000, T_history[step], linewidth=1.5)
ax1.set_xlabel("距离 x (mm)")
ax1.set_ylabel("温度 T (°C)")
ax1.set_title("温度分布随时间演化")
ax1.legend(labels)
ax1.grid(True, alpha=0.3)

# 图 2: 中心线温度随时间变化
ax2 = axes[0, 1]
t_axis = np.arange(nt + 1) * dt
center_idx = nx // 2
ax2.plot(t_axis, T_history[:, center_idx], "r-", linewidth=2, label=f"中心 (x={x[center_idx]*1000:.1f}mm)")
ax2.plot(t_axis, T_history[:, nx // 4], "b-", linewidth=2, label=f"x={x[nx//4]*1000:.1f}mm")
ax2.plot(t_axis, T_history[:, 3 * nx // 4], "g-", linewidth=2, label=f"x={x[3*nx//4]*1000:.1f}mm")
ax2.set_xlabel("时间 (s)")
ax2.set_ylabel("温度 (°C)")
ax2.set_title("各位置温度随时间变化")
ax2.legend()
ax2.grid(True, alpha=0.3)

# 图 3: 稳态温度分布 vs 解析解
ax3 = axes[1, 0]
# 解析解: T(x) = T_hot + (T_cold - T_hot) * x/L
T_analytical = T_hot + (T_cold - T_hot) * x / L
ax3.plot(x * 1000, T_history[-1], "ro", markersize=4, label="数值解 (稳态)")
ax3.plot(x * 1000, T_analytical, "b--", linewidth=2, label="解析解")
ax3.set_xlabel("距离 x (mm)")
ax3.set_ylabel("温度 T (°C)")
ax3.set_title("稳态温度分布 vs 解析解")
ax3.legend()
ax3.grid(True, alpha=0.3)

# 图 4: 温度热力图
ax4 = axes[1, 1]
time_display = np.arange(nt + 1) * dt
im = ax4.imshow(
    T_history.T,
    extent=[0, nt * dt, L * 1000, 0],
    aspect="auto",
    cmap="hot",
    origin="lower",
)
ax4.set_xlabel("时间 (s)")
ax4.set_ylabel("距离 x (mm)")
ax4.set_title("温度场热力图")
plt.colorbar(im, ax=ax4, label="温度 (°C)")

plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(__file__), "example1_1d_rod.png"), dpi=150, bbox_inches="tight")
plt.show()

print(f"\n稳态最大温度: {T_history[-1].max():.2f} °C")
print(f"稳态最小温度: {T_history[-1].min():.2f} °C")
print(f"稳态平均温度: {T_history[-1].mean():.2f} °C")
