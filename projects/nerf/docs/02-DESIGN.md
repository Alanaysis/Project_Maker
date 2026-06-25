# NeRF 设计文档

## 1. 架构概览

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    NeRF 系统架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │ 光线生成器   │───▶│ 采样点生成   │───▶│ 位置编码器   │    │
│  │ (RayGenerator)│    │ (Sampler)   │    │ (PosEncoding)│    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         │                  │                   │           │
│         ▼                  ▼                   ▼           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │ 相机参数     │    │ 3D 坐标      │    │ 高维特征     │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│                                            │               │
│                                            ▼               │
│                                    ┌─────────────┐        │
│                                    │ NeRF 模型    │        │
│                                    │ (MLP)        │        │
│                                    └─────────────┘        │
│                                            │               │
│                          ┌─────────────────┼──────────┐   │
│                          ▼                 ▼          │   │
│                  ┌─────────────┐   ┌─────────────┐   │   │
│                  │ 密度 σ      │   │ 颜色 RGB    │   │   │
│                  └─────────────┘   └─────────────┘   │   │
│                          │                 │          │   │
│                          ▼                 ▼          │   │
│                  ┌─────────────────────────────┐     │   │
│                  │        体渲染器              │     │   │
│                  │   (Volume Renderer)          │     │   │
│                  └─────────────────────────────┘     │   │
│                                    │                  │   │
│                                    ▼                  │   │
│                            ┌─────────────┐           │   │
│                            │ 2D 图像      │           │   │
│                            └─────────────┘           │   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
src/
├── __init__.py                 # 模块导出
├── positional_encoding.py      # 位置编码
├── nerf_model.py               # NeRF 模型 (MLP)
├── volume_renderer.py          # 体渲染器
├── ray_utils.py                # 光线工具
├── scene.py                    # 简单场景
└── trainer.py                  # 训练器
```

## 2. 核心组件设计

### 2.1 位置编码器 (PositionalEncoding)

**职责**：
- 将低维坐标映射到高维空间
- 支持不同频率的编码
- 支持位置和方向编码

**接口设计**：

```python
class PositionalEncoding(nn.Module):
    def __init__(
        self,
        input_dim: int = 3,      # 输入维度
        num_freqs: int = 10,     # 频率层数
        include_input: bool = True,  # 是否包含原始输入
        log_sampling: bool = True,   # 是否对数采样
    ):
        # 计算输出维度
        # output_dim = input_dim + num_freqs * 2 * input_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (..., input_dim)
        # 返回: (..., output_dim)
```

**设计决策**：

1. **对数采样 vs 线性采样**：
   - 对数采样：2^0, 2^1, ..., 2^(L-1)
   - 线性采样：等间隔频率
   - 默认使用对数采样（效果更好）

2. **是否包含原始输入**：
   - 包含：保留低频信息
   - 不包含：只使用编码后的特征
   - 默认包含

3. **位置编码 vs 方向编码**：
   - 位置编码：num_freqs = 10（高频细节）
   - 方向编码：num_freqs = 4（平滑变化）

### 2.2 NeRF 模型 (NeRFModel)

**职责**：
- 接收编码后的坐标
- 预测密度和颜色
- 支持视角依赖

**接口设计**：

```python
class NeRFModel(nn.Module):
    def __init__(
        self,
        pos_encoding_dim: int = 63,   # 位置编码维度
        dir_encoding_dim: int = 27,   # 方向编码维度
        hidden_dim: int = 256,        # 隐藏层维度
        num_layers: int = 8,          # 层数
        skip_layer: int = 4,          # 跳跃连接位置
        use_viewdirs: bool = True,    # 是否使用方向
    ):
        # 主干网络：处理位置
        # 密度头：预测密度
        # 颜色头：预测颜色

    def forward(
        self,
        positions: torch.Tensor,   # 编码后的位置 (batch, pos_dim)
        directions: torch.Tensor = None,  # 编码后的方向 (batch, dir_dim)
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        # 返回: (density, color)
```

**网络结构**：

```
输入: 位置编码 (63维) + 方向编码 (27维)

主干网络 (8层):
  Layer 0: Linear(63, 256) + ReLU
  Layer 1: Linear(256, 256) + ReLU
  Layer 2: Linear(256, 256) + ReLU
  Layer 3: Linear(256, 256) + ReLU
  Layer 4: Linear(256+63, 256) + ReLU  ← 跳跃连接
  Layer 5: Linear(256, 256) + ReLU
  Layer 6: Linear(256, 256) + ReLU
  Layer 7: Linear(256, 256) + ReLU

密度头:
  Linear(256, 128) + ReLU
  Linear(128, 1) + Softplus

颜色头:
  Linear(256, 128) + ReLU
  Linear(128+27, 128) + ReLU  ← 拼接方向
  Linear(128, 3) + Sigmoid
```

**设计决策**：

1. **跳跃连接**：
   - 在第4层后拼接原始输入
   - 帮助梯度流动
   - 保留低频信息

2. **密度激活函数**：
   - Softplus：确保非负
   - 比 ReLU 更平滑

3. **颜色激活函数**：
   - Sigmoid：输出 [0, 1]
   - 比 Tanh 更稳定

4. **方向依赖**：
   - 密度只依赖位置
   - 颜色依赖位置和方向
   - 实现视角相关效果

### 2.3 体渲染器 (VolumeRenderer)

**职责**：
- 将3D信息合成2D图像
- 计算 alpha、透射率、权重
- 支持背景颜色

**接口设计**：

```python
class VolumeRenderer(nn.Module):
    def __init__(
        self,
        background_color: Optional[torch.Tensor] = None,
        white_background: bool = True,
    ):
        # 背景颜色

    def forward(
        self,
        colors: torch.Tensor,      # 采样点颜色 (rays, samples, 3)
        densities: torch.Tensor,    # 采样点密度 (rays, samples, 1)
        distances: torch.Tensor,    # 采样点距离 (rays, samples)
        rays_d: Optional[torch.Tensor] = None,  # 光线方向
    ) -> Tuple[torch.Tensor, torch.Tensor, dict]:
        # 返回: (pixel_colors, depth_map, extras)
```

**渲染公式实现**：

```python
# 1. 计算采样点间距
deltas = distances[:, 1:] - distances[:, :-1]

# 2. 计算 alpha 不透明度
alpha = 1 - exp(-densities * deltas)

# 3. 计算累积透射率
transmittance = cumprod(1 - alpha)

# 4. 计算权重
weights = transmittance * alpha

# 5. 合成颜色
pixel_colors = sum(weights * colors)

# 6. 添加背景
pixel_colors = pixel_colors + (1 - sum(weights)) * background_color
```

**设计决策**：

1. **背景颜色**：
   - 白色背景：合成数据常用
   - 黑色背景：真实数据常用
   - 自定义背景：灵活配置

2. **深度图**：
   - 权重加权的距离
   - 用于调试和可视化

3. **额外信息**：
   - alpha：每个点的不透明度
   - transmittance：累积透射率
   - weights：渲染权重
   - accumulation：总不透明度

### 2.4 光线工具 (RayGenerator)

**职责**：
- 生成相机光线
- 支持不同相机模型
- 采样光线上点

**接口设计**：

```python
class RayGenerator:
    def __init__(
        self,
        height: int,
        width: int,
        focal_length: float,
        near: float = 2.0,
        far: float = 6.0,
    ):
        # 生成像素坐标网格

    def get_rays(
        self,
        camera_to_world: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        # 生成世界坐标系下的光线

    def generate_camera_pose(
        self,
        azimuth: float,
        elevation: float,
        radius: float = 4.0,
        target: torch.Tensor = None,
    ) -> torch.Tensor:
        # 生成相机位姿矩阵
```

**相机模型**：

```
针孔相机模型:
- 相机位于原点
- 看向 -z 方向
- x 轴向右，y 轴向上
- 图像平面在 z = -f 处

光线方向:
- x = (i - width/2) / f
- y = -(j - height/2) / f
- z = -1
```

**设计决策**：

1. **坐标系**：
   - 右手坐标系
   - 相机看向 -z
   - 与 OpenGL 一致

2. **归一化**：
   - 方向向量归一化
   - 确保光线方向正确

3. **相机位姿**：
   - 球坐标生成
   - 支持不同视角
   - 方便数据生成

### 2.5 采样函数 (sample_points_along_rays)

**职责**：
- 沿光线采样3D点
- 支持均匀采样和分层采样
- 支持扰动

**接口设计**：

```python
def sample_points_along_rays(
    rays_o: torch.Tensor,      # 光线原点 (rays, 3)
    rays_d: torch.Tensor,      # 光线方向 (rays, 3)
    near: float,               # 近裁剪面
    far: float,                # 远裁剪面
    num_samples: int,          # 采样点数
    perturb: bool = True,      # 是否扰动
    lindisp: bool = False,     # 是否视差空间
) -> Tuple[torch.Tensor, torch.Tensor]:
    # 返回: (points, distances)
```

**采样策略**：

1. **均匀采样**：
   - 在 [near, far] 等间隔采样
   - 简单但效率低

2. **分层采样**：
   - 将区间分成 N 份
   - 每份中随机采样
   - 更好的覆盖

3. **视差空间采样**：
   - 在 1/t 空间采样
   - 近处更密集
   - 适合前向场景

### 2.6 场景 (SimpleScene)

**职责**：
- 定义简单3D场景
- 查询颜色和密度
- 生成训练数据

**接口设计**：

```python
class SimpleScene:
    def query(
        self,
        points: torch.Tensor,  # 3D点 (..., 3)
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        # 返回: (colors, densities)

    def render_rays(
        self,
        rays_o: torch.Tensor,
        rays_d: torch.Tensor,
        near: float,
        far: float,
        num_samples: int,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        # 返回: (colors, distances)
```

**场景类型**：

1. **SphereScene**：球体
2. **CubeScene**：立方体
3. **ColorfulSphereScene**：彩色球体
4. **MultiObjectScene**：多物体组合

## 3. 数据流设计

### 3.1 训练数据流

```
输入数据:
├── train_rays_o: (num_rays, 3)
├── train_rays_d: (num_rays, 3)
└── train_colors: (num_rays, 3)

处理流程:
1. 采样光线批次
   └── batch_rays_o, batch_rays_d, batch_colors

2. 采样点生成
   └── points (batch, samples, 3)
   └── distances (batch, samples)

3. 位置编码
   └── pos_encoded (batch*samples, pos_dim)
   └── dir_encoded (batch*samples, dir_dim)

4. MLP 预测
   └── densities (batch, samples, 1)
   └── colors (batch, samples, 3)

5. 体渲染
   └── pixel_colors (batch, 3)

6. 损失计算
   └── loss = MSE(pixel_colors, target_colors)

7. 反向传播
   └── 更新参数
```

### 3.2 渲染数据流

```
输入:
├── rays_o: (height*width, 3)
├── rays_d: (height*width, 3)
└── chunk_size: 1024

处理流程:
1. 分块处理
   └── 对每个 chunk:
       a. 采样点
       b. 位置编码
       c. MLP 预测
       d. 体渲染
   └── 合并结果

2. 重塑为图像
   └── image (height, width, 3)
```

## 4. 接口设计

### 4.1 模块接口

```python
# 位置编码器
pe = PositionalEncoding(input_dim=3, num_freqs=10)
encoded = pe(x)  # (..., 3) -> (..., 63)

# NeRF 模型
model = NeRFModel(pos_encoding_dim=63, dir_encoding_dim=27)
density, color = model(pos_encoded, dir_encoded)

# 体渲染器
renderer = VolumeRenderer(white_background=True)
pixel_colors, depth_map, extras = renderer(colors, densities, distances, rays_d)

# 光线生成器
generator = RayGenerator(height, width, focal_length, near, far)
rays_o, rays_d = generator.get_rays(c2w)

# 采样函数
points, distances = sample_points_along_rays(rays_o, rays_d, near, far, num_samples)

# 场景
scene = SphereScene(radius=1.0, color=(1,0,0))
colors, densities = scene.query(points)

# 训练器
trainer = NeRFTrainer(model, pos_encoding, dir_encoding, renderer)
trainer.train(train_rays_o, train_rays_d, train_colors)
```

### 4.2 配置接口

```python
# 训练配置
config = {
    "model": {
        "hidden_dim": 256,
        "num_layers": 8,
        "skip_layer": 4,
        "use_viewdirs": True,
    },
    "encoding": {
        "pos_num_freqs": 10,
        "dir_num_freqs": 6,
    },
    "rendering": {
        "white_background": True,
        "num_samples": 64,
        "near": 2.0,
        "far": 6.0,
    },
    "training": {
        "learning_rate": 5e-4,
        "batch_size": 4096,
        "num_epochs": 100,
    },
}
```

## 5. 错误处理设计

### 5.1 输入验证

```python
def validate_input(x, expected_dim):
    if x.dim() < 1:
        raise ValueError("输入至少需要1维")
    if x.shape[-1] != expected_dim:
        raise ValueError(f"期望维度 {expected_dim}, 实际 {x.shape[-1]}")
```

### 5.2 数值稳定性

```python
# 避免 log(0)
eps = 1e-10
log_weights = torch.log(weights + eps)

# 避免除零
denom = torch.where(denom < eps, torch.ones_like(denom), denom)

# 梯度裁剪
nn.utils.clip_grad_norm_(parameters, max_norm=1.0)
```

### 5.3 设备兼容性

```python
def to_device(tensor, device):
    if device == "cuda" and not torch.cuda.is_available():
        warnings.warn("CUDA 不可用，使用 CPU")
        device = "cpu"
    return tensor.to(device)
```

## 6. 性能优化设计

### 6.1 分块处理

```python
def render_chunks(rays_o, rays_d, chunk_size=1024):
    all_colors = []
    for i in range(0, len(rays_o), chunk_size):
        chunk = rays_o[i:i+chunk_size]
        colors = render_chunk(chunk)
        all_colors.append(colors)
    return torch.cat(all_colors)
```

### 6.2 批量处理

```python
# 并行处理多个光线
batch_rays_o = rays_o[indices]  # (batch, 3)
batch_rays_d = rays_d[indices]  # (batch, 3)
points, distances = sample_points(batch_rays_o, batch_rays_d)
```

### 6.3 缓存优化

```python
# 预计算位置编码
pos_encoded = pos_encoding(points)  # 避免重复计算
```

## 7. 测试设计

### 7.1 单元测试

```python
def test_positional_encoding():
    pe = PositionalEncoding(input_dim=3, num_freqs=10)
    x = torch.randn(10, 3)
    encoded = pe(x)
    assert encoded.shape == (10, 63)

def test_volume_renderer():
    renderer = VolumeRenderer()
    colors = torch.randn(10, 32, 3)
    densities = torch.randn(10, 32, 1)
    distances = torch.linspace(2, 6, 32).expand(10, 32)
    pixel_colors, _, _ = renderer(colors, densities, distances)
    assert pixel_colors.shape == (10, 3)
```

### 7.2 集成测试

```python
def test_full_pipeline():
    # 创建组件
    pe = PositionalEncoding()
    model = NeRFModel()
    renderer = VolumeRenderer()

    # 生成数据
    rays_o, rays_d = generate_rays()
    points, distances = sample_points(rays_o, rays_d)

    # 前向传播
    pos_encoded = pe(points)
    density, color = model(pos_encoded)
    pixel_colors, _, _ = renderer(color, density, distances)

    assert pixel_colors.shape == (num_rays, 3)
```

### 7.3 物理测试

```python
def test_energy_conservation():
    renderer = VolumeRenderer(white_background=False)
    # 空场景应该是黑色
    densities = torch.zeros(1, 32, 1)
    colors, _, _ = renderer(torch.randn(1, 32, 3), densities, distances)
    assert torch.allclose(colors, torch.zeros_like(colors), atol=1e-5)

def test_front_blocking():
    # 前面高密度阻挡后面
    densities = torch.zeros(1, 32, 1)
    densities[0, :16, 0] = 100.0
    # 渲染结果应该主要是前面的颜色
```

## 8. 扩展性设计

### 8.1 新场景类型

```python
class CustomScene(SimpleScene):
    def query(self, points):
        # 自定义场景逻辑
        return colors, densities
```

### 8.2 新编码方式

```python
class CustomEncoding(nn.Module):
    def forward(self, x):
        # 自定义编码逻辑
        return encoded
```

### 8.3 新渲染器

```python
class CustomRenderer(nn.Module):
    def forward(self, colors, densities, distances):
        # 自定义渲染逻辑
        return pixel_colors, depth_map, extras
```

## 9. 依赖关系

### 9.1 内部依赖

```
PositionalEncoding
    └── 被 NeRFModel 使用

NeRFModel
    └── 被 Trainer 使用

VolumeRenderer
    └── 被 Trainer 使用

RayGenerator
    └── 被 Trainer 和 Scene 使用

SimpleScene
    └── 被 Trainer 使用
```

### 9.2 外部依赖

```
torch
├── nn.Module
├── Tensor 操作
└── 优化器

numpy
└── 数学函数
```

## 10. 配置管理

### 10.1 默认配置

```python
DEFAULT_CONFIG = {
    "pos_encoding": {
        "input_dim": 3,
        "num_freqs": 10,
        "include_input": True,
        "log_sampling": True,
    },
    "model": {
        "pos_encoding_dim": 63,
        "dir_encoding_dim": 27,
        "hidden_dim": 256,
        "num_layers": 8,
        "skip_layer": 4,
        "use_viewdirs": True,
    },
    "renderer": {
        "white_background": True,
    },
    "training": {
        "near": 2.0,
        "far": 6.0,
        "num_samples": 64,
        "learning_rate": 5e-4,
    },
}
```

### 10.2 配置验证

```python
def validate_config(config):
    assert config["model"]["hidden_dim"] > 0
    assert config["training"]["near"] < config["training"]["far"]
    assert config["training"]["num_samples"] > 0
```

## 11. 日志和监控

### 11.1 训练日志

```python
log = {
    "epoch": epoch,
    "loss": loss,
    "psnr": psnr,
    "learning_rate": lr,
    "time": elapsed,
}
```

### 11.2 可视化

```python
def visualize_results(image, depth_map, extras):
    # 渲染图像
    # 深度图
    # 权重分布
    # Alpha 不透明度
```

## 12. 总结

### 12.1 设计原则

1. **模块化**：每个组件独立，易于测试和替换
2. **可配置**：参数化设计，适应不同需求
3. **可扩展**：支持新场景、新编码、新渲染器
4. **数值稳定**：避免 NaN 和梯度问题

### 12.2 关键设计

1. **位置编码**：学习高频细节的关键
2. **跳跃连接**：帮助梯度流动
3. **体渲染**：3D 到 2D 的桥梁
4. **分块处理**：节省内存

### 12.3 设计权衡

1. **精度 vs 速度**：更多采样点 = 更好质量，更慢速度
2. **内存 vs 质量**：更高分辨率 = 更好质量，更多内存
3. **简单 vs 灵活**：简单接口 vs 灵活配置
