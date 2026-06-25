# NeRF 学习笔记

## 1. NeRF 核心概念

### 1.1 什么是 NeRF？

NeRF (Neural Radiance Fields) 是一种使用神经网络表示 3D 场景的方法。

**核心思想**：
- 用一个 MLP 网络表示连续的 3D 辐射场
- 输入：3D 坐标 (x, y, z) + 观察方向 (θ, φ)
- 输出：颜色 (r, g, b) + 体积密度 (σ)
- 通过体渲染将 3D 信息合成 2D 图像

**为什么 NeRF 重要？**
- 可以从少量照片生成新视角
- 不需要显式的 3D 模型
- 能够学习复杂的外观和几何

### 1.2 关键创新

1. **位置编码**：将低维坐标映射到高维，学习高频细节
2. **体渲染**：将 3D 体积渲染为 2D 图像
3. **视角依赖**：颜色依赖观察方向，实现视角相关效果
4. **连续表示**：MLP 表示连续函数，任意分辨率采样

### 1.3 应用场景

1. **新视角合成**：从少量照片生成新视角
2. **3D 重建**：从图像重建 3D 模型
3. **虚拟现实**：创建沉浸式体验
4. **电影特效**：场景重建和编辑

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

**为什么需要位置编码？**
- MLP 倾向于学习低频函数（平滑函数）
- 3D 场景包含高频细节（纹理、边缘）
- 位置编码将高频信息显式编码
- MLP 可以拟合高频函数

## 3. 实现细节

### 3.1 位置编码实现

```python
class PositionalEncoding(nn.Module):
    def __init__(self, input_dim=3, num_freqs=10):
        # 计算频率 bands: 2^0, 2^1, ..., 2^(L-1)
        freq_bands = 2.0 ** torch.linspace(0, num_freqs-1, num_freqs)
        
    def forward(self, x):
        # 对每个频率进行 sin/cos 编码
        encoded = []
        if self.include_input:
            encoded.append(x)
        for freq in self.freq_bands:
            encoded.append(sin(freq * pi * x))
            encoded.append(cos(freq * pi * x))
        return cat(encoded)
```

**关键点**：
- 对数采样频率：2^0, 2^1, ..., 2^(L-1)
- 位置编码：10 个频率（高频细节）
- 方向编码：4-6 个频率（平滑变化）
- 包含原始输入（保留低频信息）

### 3.2 NeRF 模型实现

```python
class NeRFModel(nn.Module):
    def __init__(self, pos_encoding_dim=63, dir_encoding_dim=27, hidden_dim=256):
        # 主干网络：8层全连接
        # 跳跃连接：第4层后拼接原始输入
        # 密度头：Softplus 确保非负
        # 颜色头：Sigmoid 确保 [0, 1]
        
    def forward(self, positions, directions):
        # 主干网络处理位置
        # 密度预测：只依赖位置
        # 颜色预测：依赖位置和方向
```

**关键点**：
- 密度只依赖位置，不依赖方向
- 颜色依赖位置和方向（视角相关效果）
- 跳跃连接帮助梯度流动
- 激活函数选择很重要

### 3.3 体渲染实现

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
    
    # 添加背景
    pixel_colors = pixel_colors + (1 - sum(weights)) * background_color
    
    return pixel_colors
```

**关键点**：
- Alpha 不透明度：σ 越大，α 越接近 1
- 累积透射率：前面的点阻挡后面的点
- 权重：T_i * α_i，表示每个点的贡献
- 背景颜色：填充透明区域

### 3.4 光线采样实现

```python
def sample_points_along_rays(rays_o, rays_d, near, far, num_samples):
    # 生成采样距离
    t = linspace(near, far, num_samples)
    
    # 添加随机扰动（分层采样）
    if perturb:
        t = t + rand() * (t[1] - t[0])
    
    # 计算 3D 点
    points = rays_o + t * rays_d
    
    return points, t
```

**关键点**：
- 均匀采样：在 [near, far] 等间隔
- 分层采样：每份中随机采样
- 视差空间：近处更密集
- 公式：r(t) = o + t * d

## 4. 训练流程

### 4.1 数据准备

```python
# 1. 创建场景
scene = SphereScene(radius=1.0, color=(1.0, 0.0, 0.0))

# 2. 生成多视角数据
for azimuth in range(0, 360, 10):
    c2w = generate_camera_pose(azimuth, elevation)
    rays_o, rays_d = get_rays(c2w)
    colors = scene.render_rays(rays_o, rays_d)
```

### 4.2 训练循环

```python
for epoch in range(num_epochs):
    # 1. 采样光线批次
    batch_rays_o, batch_rays_d, batch_colors = sample_batch()
    
    # 2. 采样点
    points, distances = sample_points_along_rays(batch_rays_o, batch_rays_d)
    
    # 3. 位置编码
    pos_encoded = pos_encoding(points)
    dir_encoded = dir_encoding(batch_rays_d)
    
    # 4. MLP 预测
    densities, colors = model(pos_encoded, dir_encoded)
    
    # 5. 体渲染
    pixel_colors, _, _ = renderer(colors, densities, distances)
    
    # 6. 计算损失
    loss = MSE(pixel_colors, batch_colors)
    
    # 7. 反向传播
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
```

### 4.3 评估指标

```python
# PSNR (Peak Signal-to-Noise Ratio)
psnr = -10 * log10(MSE)

# SSIM (Structural Similarity Index)
ssim = compute_ssim(predicted, ground_truth)

# LPIPS (Learned Perceptual Image Patch Similarity)
lpips = compute_lpips(predicted, ground_truth)
```

## 5. 常见问题和解决方案

### 5.1 训练不收敛

**问题**：损失不下降或震荡

**可能原因**：
- 学习率过大
- 数据预处理错误
- 网络结构问题

**解决方案**：
```python
# 降低学习率
optimizer = Adam(lr=1e-4)  # 从 5e-4 降到 1e-4

# 检查数据
print(f"数据范围: [{data.min()}, {data.max()}]")
print(f"数据均值: {data.mean()}")

# 简化网络
model = TinyNeRF(hidden_dim=64, num_layers=4)
```

### 5.2 渲染质量差

**问题**：渲染结果模糊或有伪影

**可能原因**：
- 采样点不足
- 位置编码频率不合适
- 训练时间不足

**解决方案**：
```python
# 增加采样点
num_samples = 128  # 从 64 增加到 128

# 调整位置编码
pe = PositionalEncoding(num_freqs=12)  # 从 10 增加到 12

# 延长训练
num_epochs = 200  # 从 100 增加到 200
```

### 5.3 计算成本高

**问题**：训练时间过长

**可能原因**：
- 网络过大
- 采样点过多
- 图像分辨率过高

**解决方案**：
```python
# 使用 Tiny NeRF
model = TinyNeRF(hidden_dim=128, num_layers=4)

# 减少采样点
num_samples = 32  # 从 64 减少到 32

# 降低分辨率
height, width = 64, 64  # 从 800 减少到 64
```

### 5.4 内存不足

**问题**：OOM (Out of Memory)

**可能原因**：
- 批量过大
- 分辨率过高
- 采样点过多

**解决方案**：
```python
# 减小批量
batch_size = 512  # 从 4096 减少到 512

# 分块处理
chunk_size = 512

# 降低分辨率
height, width = 64, 64
```

## 6. 进阶主题

### 6.1 分层采样

**问题**：均匀采样效率低

**解决方案**：分层采样（Hierarchical Sampling）

```python
# 1. 粗采样
points_coarse = sample_uniform(rays_o, rays_d, near, far, N_c)
densities_coarse, colors_coarse = model_coarse(points_coarse)
weights_coarse = compute_weights(densities_coarse)

# 2. 细采样（根据粗网络权重）
points_fine = sample_pdf(bins, weights_coarse, N_f)
densities_fine, colors_fine = model_fine(points_fine)

# 3. 合并渲染
colors = volume_render(colors_coarse, colors_fine, weights_coarse, weights_fine)
```

**关键点**：
- 高权重区域密集采样
- 低权重区域稀疏采样
- 提高采样效率

### 6.2 Mip-NeRF

**改进**：使用积分位置编码

```python
# 标准位置编码
gamma(x) = (sin(2^0 π x), cos(2^0 π x), ...)

# 积分位置编码
gamma(x, var) = (sin(2^0 π x) * exp(-0.5 * (2^0 π)^2 * var), ...)
```

**效果**：
- 减少锯齿伪影
- 更好的多尺度表示
- 更快的收敛

### 6.3 Instant-NGP

**改进**：多分辨率哈希编码

```python
# 使用哈希表存储特征
hash_table = HashTable(size=2^19)

# 多分辨率网格
for resolution in [16, 32, 64, 128, 256, 512]:
    features = lookup_hash_table(points * resolution)
```

**效果**：
- 1000x 加速
- 实时渲染
- 保持高质量

## 7. 调试技巧

### 7.1 可视化中间结果

```python
# 可视化采样点
points, _ = sample_points_along_rays(rays_o, rays_d, 2.0, 6.0, 32)
print(f"采样点形状: {points.shape}")
print(f"采样点范围: [{points.min()}, {points.max()}]")

# 可视化位置编码
pe = PositionalEncoding()
encoded = pe(points.reshape(-1, 3))
print(f"编码后形状: {encoded.shape}")
print(f"编码后范围: [{encoded.min()}, {encoded.max()}]")

# 可视化模型输出
density, color = model(encoded)
print(f"密度范围: [{density.min()}, {density.max()}]")
print(f"颜色范围: [{color.min()}, {color.max()}]")
```

### 7.2 检查梯度

```python
# 检查梯度是否流动
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad norm = {param.grad.norm()}")
    else:
        print(f"{name}: no gradient")
```

### 7.3 监控训练

```python
# 记录训练历史
history = {
    "loss": [],
    "psnr": [],
    "learning_rate": [],
}

# 绘制损失曲线
plt.plot(history["loss"])
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.show()
```

### 7.4 对比 Ground Truth

```python
# 渲染预测图像
predicted = render_image(model, rays_o, rays_d)

# 渲染 Ground Truth
ground_truth = scene.render_rays(rays_o, rays_d)

# 计算误差
error = (predicted - ground_truth).abs()
print(f"平均误差: {error.mean()}")
print(f"最大误差: {error.max()}")
```

## 8. 实践建议

### 8.1 入门路径

1. **理解体渲染原理**
   - 学习体渲染方程
   - 理解 alpha、透射率、权重
   - 实现简单的体渲染器

2. **实现简单版本**
   - Tiny NeRF（4层，128维）
   - 简单场景（球体）
   - 低分辨率（64x64）

3. **逐步增加复杂度**
   - 完整 NeRF 模型
   - 分层采样
   - 更复杂场景

4. **尝试真实数据**
   - 下载 NeRF 数据集
   - 处理真实照片
   - 评估渲染质量

### 8.2 实验建议

1. **从合成场景开始**
   - 球体、立方体
   - Ground truth 可用
   - 容易调试

2. **使用小分辨率**
   - 64x64 或 128x128
   - 快速迭代
   - 节省内存

3. **减少训练迭代次数**
   - 先验证流程正确
   - 再增加训练时间
   - 避免浪费时间

4. **可视化中间结果**
   - 检查采样点
   - 检查编码
   - 检查渲染结果

5. **对比不同参数**
   - 学习率
   - 采样点数
   - 位置编码频率

### 8.3 学习资源

1. **论文**
   - NeRF: Mildenhall et al., ECCV 2020
   - Mip-NeRF: Barron et al., ICCV 2021
   - Instant-NGP: Müller et al., SIGGRAPH 2022

2. **代码库**
   - 官方 NeRF: https://github.com/bmild/nerf
   - NeRF-pytorch: https://github.com/yenchenlin/nerf-pytorch

3. **教程**
   - NeRF 论文解读（多篇博客）
   - NeRF 实现教程（YouTube）
   - NeRF 入门指南（GitHub）

## 9. 常见错误

### 9.1 坐标系错误

**问题**：相机坐标系不一致

**解决**：
```python
# 确保使用右手坐标系
# 相机看向 -z 方向
# x 轴向右，y 轴向上
directions = torch.stack([
    (i - width/2) / focal_length,
    -(j - height/2) / focal_length,
    -torch.ones_like(i),
], dim=-1)
```

### 9.2 归一化错误

**问题**：方向向量未归一化

**解决**：
```python
# 归一化方向向量
rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)
```

### 9.3 激活函数错误

**问题**：密度使用 ReLU，可能出现负值

**解决**：
```python
# 使用 Softplus 确保非负
density_head = nn.Sequential(
    nn.Linear(hidden_dim, 1),
    nn.Softplus(),  # 而非 ReLU
)
```

### 9.4 数值问题

**问题**：log(0) 导致 NaN

**解决**：
```python
# 使用 eps 避免 log(0)
eps = 1e-10
log_value = torch.log(value + eps)
```

## 10. 总结

### 10.1 关键概念

1. **神经隐式表示**：用 MLP 表示 3D 场景
2. **位置编码**：学习高频细节
3. **体渲染**：3D 到 2D 的转换
4. **视角依赖**：实现反射等效果

### 10.2 实现要点

1. **位置编码**：对数采样频率，10 个频率层
2. **NeRF 模型**：8层全连接，跳跃连接
3. **体渲染**：离散化公式，背景颜色
4. **训练流程**：采样点、编码、预测、渲染

### 10.3 学习建议

1. **从小开始**：先实现 Tiny NeRF
2. **逐步验证**：每个组件单独测试
3. **可视化调试**：检查中间结果
4. **参考实现**：对比官方代码
5. **理解原理**：不只是复制代码

### 10.4 进阶方向

1. **加速**：Instant-NGP、3D Gaussian Splatting
2. **泛化**：pixelNeRF、IBRNet
3. **动态**：D-NeRF、Nerfies
4. **生成**：DreamFusion、Magic3D

## 11. 实践清单

### 11.1 基础实现

- [ ] 理解体渲染方程
- [ ] 实现位置编码
- [ ] 实现 NeRF 模型
- [ ] 实现体渲染器
- [ ] 实现光线采样
- [ ] 实现简单场景

### 11.2 训练流程

- [ ] 生成训练数据
- [ ] 实现训练循环
- [ ] 监控训练过程
- [ ] 评估渲染质量

### 11.3 优化改进

- [ ] 分层采样
- [ ] 学习率调度
- [ ] 梯度裁剪
- [ ] 性能优化

### 11.4 进阶主题

- [ ] Mip-NeRF
- [ ] Instant-NGP
- [ ] 3D Gaussian Splatting
- [ ] 动态场景

## 12. 参考代码

### 12.1 最小实现

```python
import torch
import torch.nn as nn

# 位置编码
class PosEnc(nn.Module):
    def __init__(self, L=10):
        super().__init__()
        self.L = L
        self.freqs = 2.0 ** torch.arange(L)
    
    def forward(self, x):
        encoded = [x]
        for freq in self.freqs:
            encoded.append(torch.sin(freq * x))
            encoded.append(torch.cos(freq * x))
        return torch.cat(encoded, dim=-1)

# NeRF 模型
class NeRF(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(63, 256), nn.ReLU(),
            nn.Linear(256, 256), nn.ReLU(),
            nn.Linear(256, 256), nn.ReLU(),
            nn.Linear(256, 256), nn.ReLU(),
        )
        self.density = nn.Sequential(nn.Linear(256, 1), nn.Softplus())
        self.color = nn.Sequential(nn.Linear(256, 3), nn.Sigmoid())
    
    def forward(self, x):
        h = self.net(x)
        return self.density(h), self.color(h)

# 体渲染
def render(colors, densities, distances):
    deltas = distances[:, 1:] - distances[:, :-1]
    alpha = 1 - torch.exp(-densities * deltas)
    transmittance = torch.cumprod(1 - alpha, dim=1)
    weights = transmittance * alpha
    return (weights * colors).sum(dim=1)
```

### 12.2 完整流程

```python
# 1. 创建组件
pos_enc = PosEnc(L=10)
model = NeRF()

# 2. 生成数据
rays_o, rays_d = generate_rays()
points, distances = sample_points(rays_o, rays_d)

# 3. 前向传播
encoded = pos_enc(points)
density, color = model(encoded)

# 4. 渲染
pixel_colors = render(color, density, distances)

# 5. 计算损失
loss = MSE(pixel_colors, target_colors)

# 6. 反向传播
loss.backward()
optimizer.step()
```

## 13. 学习心得

### 13.1 理解难点

1. **体渲染方程**：需要理解物理背景
2. **位置编码**：需要理解为什么需要
3. **视角依赖**：需要理解如何实现

### 13.2 实现技巧

1. **从小开始**：先实现简单版本
2. **逐步验证**：每个组件单独测试
3. **可视化调试**：检查中间结果
4. **参考实现**：对比官方代码

### 13.3 常见陷阱

1. **坐标系错误**：注意相机坐标系
2. **归一化错误**：方向向量需要归一化
3. **激活函数错误**：密度用 Softplus，颜色用 Sigmoid
4. **数值问题**：注意 eps 的使用

### 13.4 进阶方向

1. **加速**：Instant-NGP、3D Gaussian Splatting
2. **泛化**：pixelNeRF、IBRNet
3. **动态**：D-NeRF、Nerfies
4. **生成**：DreamFusion、Magic3D
