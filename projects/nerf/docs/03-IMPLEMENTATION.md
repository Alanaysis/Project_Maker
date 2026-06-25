# NeRF 实现文档

## 1. 实现概述

本文档详细描述 NeRF 的实现过程，包括代码结构、关键算法、实现细节和注意事项。

## 2. 代码结构

### 2.1 目录结构

```
projects/nerf/
├── src/                        # 源代码
│   ├── __init__.py            # 模块导出
│   ├── positional_encoding.py # 位置编码
│   ├── nerf_model.py          # NeRF 模型
│   ├── volume_renderer.py     # 体渲染器
│   ├── ray_utils.py           # 光线工具
│   ├── scene.py               # 简单场景
│   └── trainer.py             # 训练器
├── tests/                      # 测试代码
│   ├── __init__.py
│   ├── test_positional_encoding.py
│   ├── test_nerf_model.py
│   ├── test_volume_renderer.py
│   └── test_ray_utils.py
├── examples/                   # 示例代码
│   ├── simple_demo.py
│   ├── visualize_positional_encoding.py
│   └── volume_rendering_demo.py
├── docs/                       # 文档
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── README.md                   # 项目说明
└── LEARNING_NOTES.md           # 学习笔记
```

### 2.2 模块职责

| 模块 | 职责 | 主要类/函数 |
|------|------|-------------|
| positional_encoding | 位置编码 | PositionalEncoding |
| nerf_model | NeRF 模型 | NeRFModel, TinyNeRF |
| volume_renderer | 体渲染 | VolumeRenderer |
| ray_utils | 光线处理 | RayGenerator, sample_points_along_rays |
| scene | 场景定义 | SphereScene, CubeScene |
| trainer | 训练流程 | NeRFTrainer |

## 3. 核心算法实现

### 3.1 位置编码

**实现代码**：

```python
class PositionalEncoding(nn.Module):
    def __init__(self, input_dim=3, num_freqs=10, include_input=True, log_sampling=True):
        super().__init__()
        self.input_dim = input_dim
        self.num_freqs = num_freqs
        self.include_input = include_input
        
        # 计算频率 bands
        if log_sampling:
            freq_bands = 2.0 ** torch.linspace(0.0, num_freqs - 1, num_freqs)
        else:
            freq_bands = torch.linspace(1.0, 2.0 ** (num_freqs - 1), num_freqs)
        
        self.register_buffer("freq_bands", freq_bands)
        
        # 计算输出维度
        self.output_dim = num_freqs * 2 * input_dim
        if include_input:
            self.output_dim += input_dim
    
    def forward(self, x):
        encoded_parts = []
        
        # 包含原始输入
        if self.include_input:
            encoded_parts.append(x)
        
        # 对每个频率进行编码
        for freq in self.freq_bands:
            encoded_parts.append(torch.sin(freq * np.pi * x))
            encoded_parts.append(torch.cos(freq * np.pi * x))
        
        return torch.cat(encoded_parts, dim=-1)
```

**关键实现细节**：

1. **频率计算**：
   - 对数采样：`2^0, 2^1, ..., 2^(L-1)`
   - 线性采样：等间隔
   - 使用 `register_buffer` 存储，不作为参数

2. **编码过程**：
   - 对每个频率计算 sin 和 cos
   - 拼接所有编码
   - 包含原始输入（可选）

3. **输出维度**：
   - 无原始输入：`num_freqs * 2 * input_dim`
   - 有原始输入：`num_freqs * 2 * input_dim + input_dim`

### 3.2 NeRF 模型

**实现代码**：

```python
class NeRFModel(nn.Module):
    def __init__(self, pos_encoding_dim=63, dir_encoding_dim=27, 
                 hidden_dim=256, num_layers=8, skip_layer=4, use_viewdirs=True):
        super().__init__()
        
        # 主干网络
        backbone_layers = []
        for i in range(num_layers):
            if i == 0:
                in_dim = pos_encoding_dim
            elif i == skip_layer:
                in_dim = hidden_dim + pos_encoding_dim  # 跳跃连接
            else:
                in_dim = hidden_dim
            backbone_layers.append(nn.Linear(in_dim, hidden_dim))
        
        self.backbone = nn.ModuleList(backbone_layers)
        
        # 密度头
        self.density_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Softplus(),  # 确保非负
        )
        
        # 颜色头
        if use_viewdirs:
            self.feature_layer = nn.Linear(hidden_dim, hidden_dim)
            self.color_head = nn.Sequential(
                nn.Linear(hidden_dim + dir_encoding_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, 3),
                nn.Sigmoid(),  # 输出 [0, 1]
            )
    
    def forward(self, positions, directions=None):
        # 主干网络
        h = positions
        for i, layer in enumerate(self.backbone):
            if i == self.skip_layer:
                h = torch.cat([h, positions], dim=-1)  # 跳跃连接
            h = F.relu(layer(h))
        
        # 密度预测
        density = self.density_head(h)
        
        # 颜色预测
        if self.use_viewdirs and directions is not None:
            feature = self.feature_layer(h)
            color_input = torch.cat([feature, directions], dim=-1)
            color = self.color_head(color_input)
        else:
            color = self.color_head(h)
        
        return density, color
```

**关键实现细节**：

1. **跳跃连接**：
   - 在第4层后拼接原始输入
   - 帮助梯度流动
   - 保留低频信息

2. **激活函数**：
   - ReLU：隐藏层
   - Softplus：密度输出（确保非负）
   - Sigmoid：颜色输出（范围 [0, 1]）

3. **方向依赖**：
   - 密度只依赖位置
   - 颜色依赖位置和方向
   - 通过拼接实现

### 3.3 体渲染器

**实现代码**：

```python
class VolumeRenderer(nn.Module):
    def __init__(self, background_color=None, white_background=True):
        super().__init__()
        
        if background_color is not None:
            self.register_buffer("background_color", background_color)
        elif white_background:
            self.register_buffer("background_color", torch.tensor([1.0, 1.0, 1.0]))
        else:
            self.register_buffer("background_color", torch.tensor([0.0, 0.0, 0.0]))
    
    def forward(self, colors, densities, distances, rays_d=None):
        # 计算采样点间距
        deltas = distances[:, 1:] - distances[:, :-1]
        last_delta = torch.full_like(deltas[:, :1], 1e10)
        deltas = torch.cat([deltas, last_delta], dim=-1)
        
        # 计算 alpha 不透明度
        densities = densities.squeeze(-1)  # (num_rays, num_samples)
        alpha = 1.0 - torch.exp(-densities * deltas)
        
        # 计算累积透射率
        transmittance = torch.cumprod(
            torch.cat([
                torch.ones_like(alpha[:, :1]),  # T_0 = 1
                1.0 - alpha[:, :-1],
            ], dim=-1),
            dim=-1,
        )
        
        # 计算权重
        weights = transmittance * alpha
        
        # 合成颜色
        pixel_colors = (weights.unsqueeze(-1) * colors).sum(dim=1)
        
        # 计算深度图
        depth_map = (weights * distances).sum(dim=1, keepdim=True)
        
        # 添加背景颜色
        acc_map = weights.sum(dim=-1, keepdim=True)
        pixel_colors = pixel_colors + (1.0 - acc_map) * self.background_color
        
        # 收集额外信息
        extras = {
            "weights": weights,
            "alpha": alpha,
            "transmittance": transmittance,
            "accumulation": acc_map,
        }
        
        return pixel_colors, depth_map, extras
```

**关键实现细节**：

1. **间距计算**：
   - 相邻采样点距离
   - 最后一个点使用大值
   - 考虑光线方向缩放

2. **Alpha 计算**：
   - `α = 1 - exp(-σ * δ)`
   - 确保在 [0, 1] 范围

3. **透射率计算**：
   - 使用 `cumprod` 高效计算
   - 初始值为 1

4. **权重计算**：
   - `w = T * α`
   - 表示每个点的贡献

5. **背景处理**：
   - 累积权重 < 1 时使用背景颜色
   - 支持自定义背景

### 3.4 光线采样

**实现代码**：

```python
def sample_points_along_rays(rays_o, rays_d, near, far, num_samples, 
                             perturb=True, lindisp=False):
    num_rays = rays_o.shape[0]
    device = rays_o.device
    
    # 生成采样距离
    t = torch.linspace(near, far, num_samples, device=device)
    t = t.expand(num_rays, num_samples)
    
    if lindisp:
        # 视差空间采样
        t = 1.0 / (
            1.0 / near
            + (1.0 / far - 1.0 / near)
            * torch.linspace(0.0, 1.0, num_samples, device=device)
        )
        t = t.expand(num_rays, num_samples)
    
    # 添加随机扰动
    if perturb:
        midpoints = 0.5 * (t[:, :-1] + t[:, 1:])
        upper = torch.cat([midpoints, t[:, -1:]], dim=-1)
        lower = torch.cat([t[:, :1], midpoints], dim=-1)
        random_offsets = torch.rand_like(t)
        t = lower + (upper - lower) * random_offsets
    
    # 计算3D点坐标
    points = (
        rays_o.unsqueeze(1) + t.unsqueeze(-1) * rays_d.unsqueeze(1)
    )
    
    return points, t
```

**关键实现细节**：

1. **均匀采样**：
   - 在 [near, far] 等间隔
   - 扩展到所有光线

2. **视差空间采样**：
   - 在 1/t 空间采样
   - 近处更密集

3. **分层采样**：
   - 将区间分成 N 份
   - 每份中随机采样
   - 更好的覆盖

4. **3D 点计算**：
   - `points = rays_o + t * rays_d`
   - 广播机制

## 4. 训练流程实现

### 4.1 训练器

```python
class NeRFTrainer:
    def __init__(self, model, pos_encoding, dir_encoding, renderer, 
                 learning_rate=5e-4, device="cpu", near=2.0, far=6.0, num_samples=64):
        self.model = model.to(device)
        self.pos_encoding = pos_encoding.to(device)
        self.dir_encoding = dir_encoding.to(device)
        self.renderer = renderer.to(device)
        
        # 优化器
        self.optimizer = optim.Adam(
            list(model.parameters()) + list(pos_encoding.parameters()),
            lr=learning_rate
        )
        
        # 学习率调度器
        self.scheduler = optim.lr_scheduler.ExponentialLR(
            self.optimizer, gamma=0.1 ** (1.0 / 200000)
        )
    
    def train_step(self, rays_o, rays_d, target_colors):
        # 1. 采样点
        points, distances = sample_points_along_rays(
            rays_o, rays_d, self.near, self.far, self.num_samples
        )
        
        # 2. 位置编码
        pos_encoded = self.pos_encoding(points.reshape(-1, 3))
        dir_encoded = self.dir_encoding(
            rays_d.unsqueeze(1).expand(-1, self.num_samples, -1).reshape(-1, 3)
        )
        
        # 3. MLP 预测
        densities, colors = self.model(pos_encoded, dir_encoded)
        
        # 4. 体渲染
        pixel_colors, _, _ = self.renderer(
            colors.reshape(-1, self.num_samples, 3),
            densities.reshape(-1, self.num_samples, 1),
            distances, rays_d
        )
        
        # 5. 计算损失
        loss = nn.MSELoss()(pixel_colors, target_colors)
        
        # 6. 反向传播
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        self.optimizer.step()
        self.scheduler.step()
        
        return {"loss": loss.item(), "psnr": -10.0 * torch.log10(loss).item()}
```

### 4.2 渲染流程

```python
def render_image(self, rays_o, rays_d, chunk_size=1024):
    self.model.eval()
    
    all_colors = []
    for i in range(0, rays_o.shape[0], chunk_size):
        rays_o_chunk = rays_o[i:i + chunk_size]
        rays_d_chunk = rays_d[i:i + chunk_size]
        
        # 采样
        points, distances = sample_points_along_rays(
            rays_o_chunk, rays_d_chunk, self.near, self.far, self.num_samples, perturb=False
        )
        
        # 位置编码
        pos_encoded = self.pos_encoding(points.reshape(-1, 3))
        dir_encoded = self.dir_encoding(
            rays_d_chunk.unsqueeze(1).expand(-1, self.num_samples, -1).reshape(-1, 3)
        )
        
        # MLP 预测
        densities, colors = self.model(pos_encoded, dir_encoded)
        
        # 体渲染
        pixel_colors, _, _ = self.renderer(
            colors.reshape(-1, self.num_samples, 3),
            densities.reshape(-1, self.num_samples, 1),
            distances, rays_d_chunk
        )
        
        all_colors.append(pixel_colors.cpu())
    
    return torch.cat(all_colors, dim=0)
```

## 5. 场景实现

### 5.1 球体场景

```python
class SphereScene(SimpleScene):
    def __init__(self, radius=1.0, color=(1.0, 0.0, 0.0), density=10.0, center=(0.0, 0.0, 0.0)):
        self.radius = radius
        self.color = torch.tensor(color)
        self.density = density
        self.center = torch.tensor(center)
    
    def query(self, points):
        # 计算距离
        dist = torch.norm(points - self.center, dim=-1)
        inside = dist < self.radius
        
        # 颜色
        colors = self.color.expand_as(points).clone()
        colors[~inside] = 0.0
        
        # 密度
        densities = torch.full((*points.shape[:-1], 1), self.density)
        densities[~inside] = 0.0
        
        return colors, densities
```

### 5.2 立方体场景

```python
class CubeScene(SimpleScene):
    def __init__(self, size=1.0, color=(0.0, 1.0, 0.0), density=10.0, center=(0.0, 0.0, 0.0)):
        self.size = size
        self.color = torch.tensor(color)
        self.density = density
        self.center = torch.tensor(center)
    
    def query(self, points):
        rel = points - self.center
        inside = (
            (rel[..., 0].abs() < self.size) &
            (rel[..., 1].abs() < self.size) &
            (rel[..., 2].abs() < self.size)
        )
        
        colors = self.color.expand_as(points).clone()
        colors[~inside] = 0.0
        
        densities = torch.full((*points.shape[:-1], 1), self.density)
        densities[~inside] = 0.0
        
        return colors, densities
```

## 6. 实现注意事项

### 6.1 数值稳定性

1. **避免 log(0)**：
   ```python
   eps = 1e-10
   log_value = torch.log(value + eps)
   ```

2. **避免除零**：
   ```python
   denom = torch.where(denom < eps, torch.ones_like(denom), denom)
   ```

3. **梯度裁剪**：
   ```python
   nn.utils.clip_grad_norm_(parameters, max_norm=1.0)
   ```

4. **激活函数选择**：
   - Softplus 而非 ReLU（更平滑）
   - Sigmoid 而非 Tanh（更稳定）

### 6.2 性能优化

1. **分块处理**：
   - 避免内存溢出
   - 支持大图像渲染

2. **批量处理**：
   - 并行处理多个光线
   - 利用 GPU 并行性

3. **缓存优化**：
   - 预计算位置编码
   - 避免重复计算

### 6.3 设备兼容性

```python
# 检查 CUDA 可用性
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 移动到设备
model = model.to(device)
tensor = tensor.to(device)
```

### 6.4 内存管理

```python
# 及时释放不需要的张量
del intermediate_tensor

# 使用 torch.no_grad()
with torch.no_grad():
    result = model(input)

# 清空缓存
torch.cuda.empty_cache()
```

## 7. 常见问题和解决方案

### 7.1 训练不收敛

**问题**：损失不下降或震荡

**可能原因**：
- 学习率过大
- 数据预处理错误
- 网络结构问题

**解决方案**：
```python
# 降低学习率
optimizer = optim.Adam(lr=1e-4)

# 检查数据
print(f"数据范围: [{data.min()}, {data.max()}]")
print(f"数据均值: {data.mean()}")

# 简化网络
model = TinyNeRF(hidden_dim=64, num_layers=4)
```

### 7.2 渲染质量差

**问题**：渲染结果模糊或有伪影

**可能原因**：
- 采样点不足
- 位置编码频率不合适
- 训练时间不足

**解决方案**：
```python
# 增加采样点
num_samples = 128

# 调整位置编码
pe = PositionalEncoding(num_freqs=12)

# 延长训练
num_epochs = 200
```

### 7.3 计算成本高

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
num_samples = 32

# 降低分辨率
height, width = 64, 64
```

### 7.4 内存不足

**问题**：OOM (Out of Memory)

**可能原因**：
- 批量过大
- 分辨率过高
- 采样点过多

**解决方案**：
```python
# 减小批量
batch_size = 512

# 分块处理
chunk_size = 512

# 降低分辨率
height, width = 64, 64
```

## 8. 调试技巧

### 8.1 可视化中间结果

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

### 8.2 检查梯度

```python
# 检查梯度是否流动
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad norm = {param.grad.norm()}")
    else:
        print(f"{name}: no gradient")
```

### 8.3 监控训练

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

### 8.4 对比 Ground Truth

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

## 9. 实现检查清单

### 9.1 功能检查

- [ ] 位置编码输出维度正确
- [ ] 位置编码值范围正确
- [ ] 模型输出形状正确
- [ ] 密度非负
- [ ] 颜色在 [0, 1] 范围
- [ ] 体渲染公式正确
- [ ] 背景颜色正确
- [ ] 光线方向归一化

### 9.2 性能检查

- [ ] 无内存泄漏
- [ ] GPU 利用率正常
- [ ] 训练速度合理
- [ ] 渲染速度可接受

### 9.3 稳定性检查

- [ ] 无 NaN 或 Inf
- [ ] 梯度正常流动
- [ ] 数值稳定
- [ ] 设备兼容

## 10. 总结

### 10.1 关键实现点

1. **位置编码**：使用 sin/cos 函数，支持不同频率
2. **跳跃连接**：帮助梯度流动，保留低频信息
3. **体渲染**：实现离散化的渲染公式
4. **分层采样**：提高采样效率

### 10.2 实现建议

1. **从小开始**：先实现 Tiny NeRF
2. **逐步验证**：每个组件单独测试
3. **可视化调试**：检查中间结果
4. **参考实现**：对比官方代码

### 10.3 常见错误

1. **坐标系错误**：注意相机坐标系
2. **归一化错误**：方向向量需要归一化
3. **激活函数错误**：密度用 Softplus，颜色用 Sigmoid
4. **数值问题**：注意 eps 的使用
