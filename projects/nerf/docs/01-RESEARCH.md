# NeRF 研究笔记

## 1. 背景知识

### 1.1 什么是 NeRF？

**NeRF (Neural Radiance Fields)** 是一种使用神经网络表示3D场景的方法，由 Mildenhall 等人在 2020 年 ECCV 会议上提出。

**核心思想**：
- 使用一个 MLP 网络表示连续的3D场景
- 输入：3D坐标 (x,y,z) + 观察方向 (θ,φ)
- 输出：颜色 (r,g,b) + 体积密度 (σ)

**主要应用**：
- 新视角合成（Novel View Synthesis）
- 3D 重建
- 场景编辑
- 虚拟现实

### 1.2 历史背景

**传统方法**：
- **多边形网格**：显式表示，需要手工建模
- **点云**：稀疏表示，难以渲染
- **体素**：规则网格，内存消耗大

**神经隐式表示**：
- **DeepSDF**（2019）：学习 SDF 函数
- **NeRF**（2020）：学习辐射场
- **后续工作**：Instant-NGP、Mip-NeRF、3D Gaussian Splatting 等

### 1.3 关键创新

1. **位置编码**：将低维坐标映射到高维，学习高频细节
2. **体渲染**：将3D体积渲染为2D图像
3. **视角依赖**：颜色依赖观察方向，实现视角相关效果
4. **连续表示**：MLP 表示连续函数，任意分辨率采样

## 2. 数学原理

### 2.1 辐射场表示

辐射场是一个连续函数：

```
F: (x, y, z, θ, φ) → (r, g, b, σ)
```

其中：
- (x, y, z)：3D 位置坐标
- (θ, φ)：观察方向（球坐标）
- (r, g, b)：颜色
- σ：体积密度

### 2.2 体渲染方程

光线穿过场景的颜色：

```
C(r) = ∫[t_n, t_f] T(t) · σ(r(t)) · c(r(t), d) dt
```

其中：
- T(t) = exp(-∫[t_n, t] σ(r(s)) ds)：累积透射率
- σ(r(t))：位置 r(t) 处的密度
- c(r(t), d)：位置 r(t) 处、方向 d 的颜色

### 2.3 离散化

实际实现中，使用离散求和：

```
Ĉ(r) = Σ[i=1, N] T_i · α_i · c_i
```

其中：
- T_i = Π[j=1, i-1] (1 - α_j)：累积透射率
- α_i = 1 - exp(-σ_i · δ_i)：alpha 不透明度
- δ_i = t_{i+1} - t_i：采样点间距

### 2.4 位置编码

低维坐标映射到高维空间：

```
γ(p) = (sin(2^0 π p), cos(2^0 π p), ..., sin(2^(L-1) π p), cos(2^(L-1) π p))
```

为什么需要位置编码？
- MLP 倾向于学习低频函数（平滑函数）
- 3D 场景包含高频细节（纹理、边缘）
- 位置编码将高频信息显式编码
- MLP 可以拟合高频函数

## 3. NeRF 架构

### 3.1 MLP 结构

```
输入 (x,y,z) → 位置编码 → 8层FC → 密度 σ
                     ↓
              中间特征 + 方向编码 → 1层FC → 颜色 (r,g,b)
```

**关键设计**：
- 密度只依赖位置，不依赖方向
- 颜色依赖位置和方向（视角相关效果）
- 使用 ReLU 激活函数
- 密度使用 Softplus 确保非负

### 3.2 训练流程

1. **数据准备**：
   - 多视角图像
   - 相机参数（内外参）
   - 通过 SfM（Structure from Motion）获取

2. **光线采样**：
   - 从每个像素发射光线
   - 在 [near, far] 区间采样

3. **前向传播**：
   - 位置编码
   - MLP 预测颜色和密度
   - 体渲染合成像素颜色

4. **损失计算**：
   - MSE 损失：渲染颜色 vs 真实颜色
   - L(r) = Σ ||Ĉ(r) - C(r)||²

5. **优化**：
   - Adam 优化器
   - 学习率调度

### 3.3 分层采样

**问题**：均匀采样效率低

**解决方案**：分层采样（Hierarchical Sampling）

1. **粗采样**：
   - 均匀采样 N_c 个点
   - 训练粗网络

2. **细采样**：
   - 根据粗网络权重，重要性采样 N_f 个点
   - 高权重区域密集采样
   - 训练细网络

## 4. 数据集

### 4.1 合成数据集

**Blender 数据集**：
- 8 个合成场景（椅子、鼓、热狗等）
- 100 训练视角 + 200 测试视角
- 800x800 分辨率
- 透明背景

**特点**：
- Ground truth 完美
- 光线简单
- 用于验证算法正确性

### 4.2 真实数据集

**LLFF 数据集**：
- 8 个真实场景
- 手持相机拍摄
- 前向相机
- 1008x756 分辨率

**特点**：
- 真实场景
- 相机参数通过 SfM 获取
- 用于验证实际应用

## 5. 变体和改进

### 5.1 Mip-NeRF（2021）

**改进**：
- 使用积分位置编码
- 避免锯齿伪影
- 多尺度表示

**效果**：
- 更少的伪影
- 更好的细节
- 更快的收敛

### 5.2 Instant-NGP（2022）

**改进**：
- 多分辨率哈希编码
- 1000x 加速
- 实时渲染

**效果**：
- 训练时间从小时缩短到秒
- 保持高质量
- 可以实时交互

### 5.3 3D Gaussian Splatting（2023）

**改进**：
- 显式点表示
- 可微分渲染
- 实时渲染

**效果**：
- 更快的渲染速度
- 更容易编辑
- 更好的质量

## 6. 应用场景

### 6.1 新视角合成

**应用**：
- 从少量照片生成新视角
- 虚拟现实
- 电影特效

**挑战**：
- 遮挡区域
- 反射和透明
- 动态场景

### 6.2 3D 重建

**应用**：
- 从图像重建3D模型
- 机器人导航
- 数字孪生

**挑战**：
- 稀疏视角
- 纹理缺失
- 计算成本

### 6.3 场景编辑

**应用**：
- 物体移除/添加
- 风格迁移
- 场景组合

**挑战**：
- 隐式表示难以编辑
- 一致性
- 实时性

## 7. 实现细节

### 7.1 位置编码参数

**位置编码**：
- num_freqs = 10（位置）
- num_freqs = 4（方向）
- log_sampling = True

**为什么位置比方向多？**
- 位置需要更高频率（细节）
- 方向通常变化平滑

### 7.2 网络参数

**标准 NeRF**：
- 隐藏层维度：256
- 层数：8
- 跳跃连接：第4层

**Tiny NeRF**：
- 隐藏层维度：128
- 层数：4
- 无跳跃连接

### 7.3 训练参数

**学习率**：
- 初始：5e-4
- 调度：指数衰减

**批量大小**：
- 光线数：4096
- 采样点数：64（粗）+ 128（细）

**训练时间**：
- 标准 NeRF：约 1-2 天（单 GPU）
- Instant-NGP：约 5-10 秒

## 8. 代码实现要点

### 8.1 位置编码实现

```python
class PositionalEncoding(nn.Module):
    def __init__(self, input_dim=3, num_freqs=10):
        # 计算频率 bands
        freq_bands = 2.0 ** torch.linspace(0, num_freqs-1, num_freqs)
        
    def forward(self, x):
        # 对每个频率进行 sin/cos 编码
        for freq in self.freq_bands:
            encoded.append(sin(freq * pi * x))
            encoded.append(cos(freq * pi * x))
        return cat(encoded)
```

### 8.2 体渲染实现

```python
def volume_render(colors, densities, distances):
    # 计算 alpha 不透明度
    alpha = 1 - exp(-densities * deltas)
    
    # 计算累积透射率
    transmittance = cumprod(1 - alpha)
    
    # 计算权重
    weights = transmittance * alpha
    
    # 合成颜色
    pixel_colors = sum(weights * colors)
    
    return pixel_colors
```

### 8.3 光线采样实现

```python
def sample_points_along_rays(rays_o, rays_d, near, far, num_samples):
    # 生成采样距离
    t = linspace(near, far, num_samples)
    
    # 添加随机扰动
    if perturb:
        t = t + rand() * (t[1] - t[0])
    
    # 计算3D点
    points = rays_o + t * rays_d
    
    return points, t
```

## 9. 常见问题

### 9.1 训练不收敛

**可能原因**：
- 学习率过大
- 数据预处理错误
- 网络结构问题

**解决方案**：
- 降低学习率
- 检查数据
- 简化网络

### 9.2 渲染质量差

**可能原因**：
- 采样点不足
- 位置编码频率不合适
- 训练时间不足

**解决方案**：
- 增加采样点
- 调整位置编码参数
- 延长训练时间

### 9.3 计算成本高

**可能原因**：
- 网络过大
- 采样点过多
- 图像分辨率过高

**解决方案**：
- 使用 Tiny NeRF
- 减少采样点
- 降低分辨率

## 10. 学习资源

### 10.1 论文

1. **NeRF**: Mildenhall et al., "NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis", ECCV 2020
2. **Mip-NeRF**: Barron et al., "Mip-NeRF: A Multiscale Representation for Anti-Aliasing Neural Radiance Fields", ICCV 2021
3. **Instant-NGP**: Müller et al., "Instant Neural Graphics Primitives with a Multiresolution Hash Encoding", SIGGRAPH 2022

### 10.2 代码库

1. **官方 NeRF**: https://github.com/bmild/nerf
2. **NeRF-pytorch**: https://github.com/yenchenlin/nerf-pytorch
3. **Instant-NGP**: https://github.com/NVlabs/instant-ngp

### 10.3 教程

1. **NeRF 论文解读**: 多篇博客文章
2. **NeRF 实现教程**: YouTube 视频教程
3. **NeRF 入门指南**: GitHub 项目

## 11. 总结

### 11.1 关键概念

1. **神经隐式表示**：用 MLP 表示3D场景
2. **位置编码**：学习高频细节
3. **体渲染**：3D 到 2D 的转换
4. **视角依赖**：实现反射等效果

### 11.2 优缺点

**优点**：
- 连续表示，任意分辨率
- 能够学习复杂外观
- 只需要图像作为监督

**缺点**：
- 训练时间长
- 推理速度慢
- 难以编辑

### 11.3 发展趋势

1. **加速**：Instant-NGP、3D Gaussian Splatting
2. **泛化**：pixelNeRF、IBRNet
3. **动态**：D-NeRF、Nerfies
4. **生成**：DreamFusion、Magic3D

## 12. 实践建议

### 12.1 入门路径

1. 理解体渲染原理
2. 实现简单版本（Tiny NeRF）
3. 在合成数据上测试
4. 逐步增加复杂度
5. 尝试真实数据

### 12.2 实验建议

1. 从合成场景开始
2. 使用小分辨率（64x64）
3. 减少训练迭代次数
4. 可视化中间结果
5. 对比不同参数

### 12.3 调试技巧

1. 检查光线方向
2. 可视化采样点
3. 监控损失曲线
4. 渲染深度图
5. 对比 ground truth
