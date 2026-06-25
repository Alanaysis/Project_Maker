"""
位置编码可视化
===============

演示位置编码的效果:
1. 展示不同频率的编码
2. 可视化编码后的特征
3. 理解为什么需要位置编码

运行方式:
    python examples/visualize_positional_encoding.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import torch
import numpy as np

from src import PositionalEncoding


def main():
    print("=" * 60)
    print("位置编码可视化")
    print("=" * 60)

    # ===== 1. 基本位置编码 =====
    print("\n1. 基本位置编码演示")
    print("-" * 40)

    # 创建位置编码器
    pe = PositionalEncoding(
        input_dim=3,
        num_freqs=10,
        include_input=True,
        log_sampling=True,
    )

    print(f"输入维度: {pe.input_dim}")
    print(f"频率层数: {pe.num_freqs}")
    print(f"输出维度: {pe.output_dim}")
    print(f"频率 bands: {pe.freq_bands}")

    # ===== 2. 单点编码 =====
    print("\n2. 单点编码")
    print("-" * 40)

    # 单个 3D 点
    point = torch.tensor([[0.5, 0.3, 0.1]])
    encoded = pe(point)

    print(f"输入: {point}")
    print(f"编码后形状: {encoded.shape}")
    print(f"编码后前10维: {encoded[0, :10]}")

    # ===== 3. 多点编码 =====
    print("\n3. 多点编码")
    print("-" * 40)

    # 多个 3D 点
    points = torch.tensor([
        [0.0, 0.0, 0.0],  # 原点
        [1.0, 0.0, 0.0],  # x 轴
        [0.0, 1.0, 0.0],  # y 轴
        [0.0, 0.0, 1.0],  # z 轴
    ])

    encoded = pe(points)

    print(f"输入点数: {points.shape[0]}")
    print(f"编码后形状: {encoded.shape}")

    # 原点的编码应该是特殊的（sin=0, cos=1）
    origin_encoded = encoded[0]
    print(f"\n原点编码:")
    print(f"  前3维（原始输入）: {origin_encoded[:3]}")
    print(f"  第4维（sin(2^0*pi*0)）: {origin_encoded[3]:.6f}")  # 应该是 0
    print(f"  第5维（cos(2^0*pi*0)）: {origin_encoded[4]:.6f}")  # 应该是 1

    # ===== 4. 不同频率的效果 =====
    print("\n4. 不同频率的效果")
    print("-" * 40)

    # 沿 x 轴移动
    x_values = torch.linspace(0, 1, 11).reshape(-1, 1)
    points_1d = torch.cat([
        x_values,
        torch.zeros_like(x_values),
        torch.zeros_like(x_values),
    ], dim=1)

    encoded = pe(points_1d)

    # 查看不同频率的编码
    print("x 值 | sin(2^0*pi*x) | cos(2^0*pi*x) | sin(2^1*pi*x) | cos(2^1*pi*x)")
    print("-" * 70)
    for i in range(0, 11, 2):
        x = points_1d[i, 0].item()
        sin1 = encoded[i, 3].item()  # sin(2^0*pi*x)
        cos1 = encoded[i, 4].item()  # cos(2^0*pi*x)
        sin2 = encoded[i, 5].item()  # sin(2^1*pi*x)
        cos2 = encoded[i, 6].item()  # cos(2^1*pi*x)
        print(f"{x:.1f}   | {sin1:12.4f} | {cos1:12.4f} | {sin2:12.4f} | {cos2:12.4f}")

    # ===== 5. 为什么需要位置编码 =====
    print("\n5. 为什么需要位置编码？")
    print("-" * 40)

    print("""
    问题：MLP 倾向于学习低频函数（平滑函数）

    例如，如果直接输入坐标 (x, y, z)：
    - MLP 可能无法学习高频细节（纹理、边缘）
    - 输出会过于平滑

    解决方案：位置编码
    - 将低维坐标映射到高维空间
    - 使用不同频率的 sin/cos 函数
    - MLP 可以学习高频函数

    效果：
    - 低频层（2^0, 2^1）：捕捉大尺度结构
    - 高频层（2^8, 2^9）：捕捉细节和纹理
    """)

    # ===== 6. 对比有无位置编码 =====
    print("6. 对比有无位置编码")
    print("-" * 40)

    # 无位置编码
    pe_none = PositionalEncoding(input_dim=3, num_freqs=0, include_input=True)
    # 有位置编码
    pe_full = PositionalEncoding(input_dim=3, num_freqs=10, include_input=True)

    point = torch.tensor([[0.5, 0.3, 0.1]])

    encoded_none = pe_none(point)
    encoded_full = pe_full(point)

    print(f"无位置编码输出维度: {pe_none.output_dim}")
    print(f"有位置编码输出维度: {pe_full.output_dim}")
    print(f"维度增加: {pe_full.output_dim / pe_none.output_dim:.1f}x")

    # ===== 7. 方向编码 =====
    print("\n7. 方向编码")
    print("-" * 40)

    # 方向编码（2D：theta, phi）
    dir_pe = PositionalEncoding(input_dim=2, num_freqs=6, include_input=True)

    print(f"方向编码输入维度: {dir_pe.input_dim}")
    print(f"方向编码输出维度: {dir_pe.output_dim}")

    # 方向向量
    theta = torch.tensor([[np.pi / 4]])  # 45度
    phi = torch.tensor([[np.pi / 3]])    # 60度
    direction = torch.cat([theta, phi], dim=1)

    encoded_dir = dir_pe(direction)
    print(f"方向编码后形状: {encoded_dir.shape}")

    print("\n" + "=" * 60)
    print("可视化完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
