# NeRF 测试文档

## 1. 测试概述

本文档描述 NeRF 项目的测试策略、测试用例和测试方法。

### 1.1 测试目标

1. **功能正确性**：验证各组件按预期工作
2. **数值稳定性**：确保无 NaN/Inf 和梯度问题
3. **性能验证**：检查计算效率和内存使用
4. **集成测试**：验证组件间协作正确

### 1.2 测试层次

```
单元测试 (Unit Tests)
├── 位置编码测试
├── NeRF 模型测试
├── 体渲染器测试
└── 光线工具测试

集成测试 (Integration Tests)
├── 模型 + 编码器
├── 渲染器 + 采样
└── 完整流程测试

物理测试 (Physics Tests)
├── 能量守恒
├── 遮挡关系
└── 透明度测试
```

## 2. 测试环境

### 2.1 依赖

```bash
# 测试依赖
pytest>=7.0.0
pytest-cov>=4.0.0
torch>=2.0.0
numpy>=1.24.0
```

### 2.2 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_positional_encoding.py -v

# 运行带覆盖率的测试
pytest tests/ -v --cov=src --cov-report=html

# 运行特定测试类
pytest tests/test_positional_encoding.py::TestPositionalEncoding -v

# 运行特定测试方法
pytest tests/test_positional_encoding.py::TestPositionalEncoding::test_output_shape -v
```

### 2.3 测试配置

```python
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## 3. 单元测试

### 3.1 位置编码测试

**测试文件**：`tests/test_positional_encoding.py`

**测试类**：`TestPositionalEncoding`

#### 测试用例

| 测试方法 | 描述 | 验证点 |
|---------|------|--------|
| test_output_shape | 输出形状 | 维度正确 |
| test_output_shape_without_input | 不包含输入 | 维度正确 |
| test_direction_encoding | 方向编码 | 2D 输入 |
| test_encoding_values | 编码值 | sin/cos 正确 |
| test_include_input_flag | 包含输入标志 | 前3维是原始输入 |
| test_log_sampling | 对数采样 | 频率是 2 的幂 |
| test_linear_sampling | 线性采样 | 频率线性间隔 |
| test_batch_independence | 批次独立性 | 单独处理一致 |
| test_gradient_flow | 梯度流 | 梯度存在 |
| test_device_compatibility | 设备兼容 | CUDA 支持 |
| test_different_num_freqs | 不同频率数 | 各种配置正确 |

**示例测试**：

```python
def test_output_shape(self):
    """测试输出形状是否正确"""
    # 3D 位置编码，10 个频率
    pe = PositionalEncoding(input_dim=3, num_freqs=10, include_input=True)
    # 输出维度 = 3 + 10 * 2 * 3 = 63
    assert pe.output_dim == 63
    
    # 测试不同输入形状
    x = torch.randn(10, 3)
    encoded = pe(x)
    assert encoded.shape == (10, 63)
    
    x = torch.randn(5, 10, 3)
    encoded = pe(x)
    assert encoded.shape == (5, 10, 63)

def test_encoding_values(self):
    """测试编码值是否正确"""
    pe = PositionalEncoding(input_dim=1, num_freqs=3, include_input=False)
    
    # 单点输入
    x = torch.tensor([[0.5]])
    encoded = pe(x)
    
    # 验证 sin 和 cos 值
    expected_sin = torch.sin(torch.tensor([1.0, 2.0, 4.0]) * np.pi * 0.5)
    expected_cos = torch.cos(torch.tensor([1.0, 2.0, 4.0]) * np.pi * 0.5)
    
    assert encoded.shape == (1, 6)
    assert torch.allclose(encoded[0, 0::2], expected_sin, atol=1e-6)
    assert torch.allclose(encoded[0, 1::2], expected_cos, atol=1e-6)
```

**边界情况测试**：

```python
class TestPositionalEncodingEdgeCases:
    def test_zero_input(self):
        """测试零输入"""
        pe = PositionalEncoding(input_dim=3, num_freqs=10)
        x = torch.zeros(5, 3)
        encoded = pe(x)
        
        # sin(0) = 0, cos(0) = 1
        assert torch.allclose(encoded[:, :3], torch.zeros(5, 3), atol=1e-6)
    
    def test_large_input(self):
        """测试大输入值"""
        pe = PositionalEncoding(input_dim=3, num_freqs=10)
        x = torch.randn(5, 3) * 100
        encoded = pe(x)
        
        # 不应该有 NaN 或 Inf
        assert not torch.isnan(encoded).any()
        assert not torch.isinf(encoded).any()
```

### 3.2 NeRF 模型测试

**测试文件**：`tests/test_nerf_model.py`

**测试类**：`TestNeRFModel`, `TestTinyNeRF`

#### 测试用例

| 测试方法 | 描述 | 验证点 |
|---------|------|--------|
| test_output_shape | 输出形状 | (density, color) 形状正确 |
| test_batch_processing | 批量处理 | 不同批量大小 |
| test_density_non_negative | 密度非负 | Softplus 确保 |
| test_color_range | 颜色范围 | [0, 1] |
| test_skip_connection | 跳跃连接 | 网络正确 |
| test_without_viewdirs | 无方向 | 简化模式 |
| test_gradient_flow | 梯度流 | 梯度存在 |
| test_parameter_count | 参数数量 | 合理范围 |
| test_device_compatibility | 设备兼容 | CUDA 支持 |

**示例测试**：

```python
def test_density_non_negative(self):
    """测试密度非负"""
    model = NeRFModel(pos_encoding_dim=63, dir_encoding_dim=27)
    
    positions = torch.randn(100, 63)
    directions = torch.randn(100, 27)
    density, _ = model(positions, directions)
    
    # Softplus 确保非负
    assert (density >= 0).all()

def test_color_range(self):
    """测试颜色范围 [0, 1]"""
    model = NeRFModel(pos_encoding_dim=63, dir_encoding_dim=27)
    
    positions = torch.randn(100, 63)
    directions = torch.randn(100, 27)
    _, color = model(positions, directions)
    
    # Sigmoid 确保在 [0, 1]
    assert (color >= 0).all()
    assert (color <= 1).all()
```

**集成测试**：

```python
class TestModelIntegration:
    def test_with_positional_encoding(self):
        """测试与位置编码的集成"""
        from projects.nerf.src.positional_encoding import PositionalEncoding
        
        pos_enc = PositionalEncoding(input_dim=3, num_freqs=10)
        dir_enc = PositionalEncoding(input_dim=3, num_freqs=6)
        model = NeRFModel(
            pos_encoding_dim=pos_enc.output_dim,
            dir_encoding_dim=dir_enc.output_dim,
        )
        
        # 原始坐标
        positions = torch.randn(10, 3)
        directions = torch.randn(10, 3)
        
        # 编码
        pos_encoded = pos_enc(positions)
        dir_encoded = dir_enc(directions)
        
        # 模型预测
        density, color = model(pos_encoded, dir_encoded)
        
        assert density.shape == (10, 1)
        assert color.shape == (10, 3)
```

### 3.3 体渲染器测试

**测试文件**：`tests/test_volume_renderer.py`

**测试类**：`TestVolumeRenderer`, `TestVolumeRenderingPhysics`

#### 测试用例

| 测试方法 | 描述 | 验证点 |
|---------|------|--------|
| test_output_shape | 输出形状 | (colors, depth, extras) |
| test_transparency | 透明区域 | 背景颜色 |
| test_opaque_object | 不透明物体 | 前面颜色 |
| test_accumulation | 累积不透明度 | [0, 1] |
| test_transmittance | 透射率 | [0, 1]，初始为 1 |
| test_weights | 权重 | [0, 1] |
| test_black_background | 黑色背景 | 零密度时黑色 |
| test_custom_background | 自定义背景 | 自定义颜色 |
| test_gradient_flow | 梯度流 | 梯度存在 |
| test_single_sample | 单采样点 | 边界情况 |

**物理测试**：

```python
class TestVolumeRenderingPhysics:
    def test_energy_conservation(self):
        """测试能量守恒"""
        renderer = VolumeRenderer(white_background=False)
        
        # 模拟一条光线穿过均匀介质
        num_samples = 100
        colors = torch.ones(1, num_samples, 3) * 0.5
        densities = torch.ones(1, num_samples, 1) * 0.1
        distances = torch.linspace(0.0, 10.0, num_samples).expand(1, num_samples)
        
        pixel_colors, _, extras = renderer(colors, densities, distances)
        
        # 累积不透明度应该小于等于 1
        acc = extras["accumulation"]
        assert acc <= 1.0 + 1e-5
    
    def test_front_blocking(self):
        """测试前方物体阻挡后方"""
        renderer = VolumeRenderer(white_background=False)
        
        num_samples = 32
        # 前半部分高密度，后半部分不同颜色
        densities = torch.zeros(1, num_samples, 1)
        densities[0, :16, 0] = 100.0  # 前面很高密度
        
        colors = torch.zeros(1, num_samples, 3)
        colors[0, :16, 0] = 1.0   # 前面红色
        colors[0, 16:, 1] = 1.0   # 后面绿色
        
        distances = torch.linspace(2.0, 6.0, num_samples).expand(1, num_samples)
        
        pixel_colors, _, _ = renderer(colors, densities, distances)
        
        # 应该主要显示红色（前面阻挡）
        assert pixel_colors[0, 0] > pixel_colors[0, 1]  # R > G
```

### 3.4 光线工具测试

**测试文件**：`tests/test_ray_utils.py`

**测试类**：`TestRayGenerator`, `TestSamplePointsAlongRays`

#### 测试用例

| 测试方法 | 描述 | 验证点 |
|---------|------|--------|
| test_initialization | 初始化 | 参数正确 |
| test_directions_shape | 方向形状 | (H, W, 3) |
| test_directions_center | 中心方向 | 指向 -z |
| test_get_rays_simple | 简化版 | 形状正确 |
| test_rays_normalized | 归一化 | 单位向量 |
| test_get_rays_with_pose | 带位姿 | 变换正确 |
| test_camera_pose_generation | 位姿生成 | 刚体变换 |
| test_different_azimuths | 不同方位角 | 不同位姿 |

**采样测试**：

```python
class TestSamplePointsAlongRays:
    def test_points_on_ray(self):
        """测试点在光线上"""
        rays_o = torch.tensor([[0, 0, 0]]).float()
        rays_d = torch.tensor([[0, 0, -1]]).float()
        
        points, distances = sample_points_along_rays(
            rays_o, rays_d, near=2.0, far=6.0, num_samples=32, perturb=False
        )
        
        # 点应该在 z 轴负方向上
        assert torch.allclose(points[0, :, 0], torch.zeros(32), atol=1e-5)
        assert torch.allclose(points[0, :, 1], torch.zeros(32), atol=1e-5)
        assert (points[0, :, 2] < 0).all()  # z 应该是负的
    
    def test_distance_range(self):
        """测试距离范围"""
        near, far = 2.0, 6.0
        num_samples = 64
        
        rays_o = torch.zeros(5, 3)
        rays_d = torch.randn(5, 3)
        rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)
        
        _, distances = sample_points_along_rays(
            rays_o, rays_d, near=near, far=far, num_samples=num_samples, perturb=False
        )
        
        # 距离应该在 [near, far] 范围内
        assert (distances >= near - 1e-5).all()
        assert (distances <= far + 1e-5).all()
```

## 4. 集成测试

### 4.1 完整流程测试

```python
class TestFullPipeline:
    def test_training_loop(self):
        """测试完整训练循环"""
        # 创建组件
        pos_enc = PositionalEncoding(input_dim=3, num_freqs=10)
        dir_enc = PositionalEncoding(input_dim=3, num_freqs=6)
        model = NeRFModel(
            pos_encoding_dim=pos_enc.output_dim,
            dir_encoding_dim=dir_enc.output_dim,
            hidden_dim=128,
            num_layers=4,
        )
        renderer = VolumeRenderer(white_background=True)
        
        # 创建训练器
        trainer = NeRFTrainer(
            model=model,
            pos_encoding=pos_enc,
            dir_encoding=dir_enc,
            renderer=renderer,
            learning_rate=5e-4,
        )
        
        # 生成训练数据
        scene = SphereScene()
        rays_o = torch.randn(100, 3)
        rays_d = torch.randn(100, 3)
        rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)
        colors, _ = scene.render_rays(rays_o, rays_d, 2.0, 6.0, 32)
        
        # 训练一步
        metrics = trainer.train_step(rays_o, rays_d, colors)
        
        assert "loss" in metrics
        assert "psnr" in metrics
        assert metrics["loss"] >= 0
    
    def test_render_image(self):
        """测试渲染图像"""
        # 创建组件
        pos_enc = PositionalEncoding(input_dim=3, num_freqs=10)
        dir_enc = PositionalEncoding(input_dim=3, num_freqs=6)
        model = NeRFModel(
            pos_encoding_dim=pos_enc.output_dim,
            dir_encoding_dim=dir_enc.output_dim,
            hidden_dim=64,
            num_layers=4,
        )
        renderer = VolumeRenderer(white_background=True)
        
        # 创建训练器
        trainer = NeRFTrainer(
            model=model,
            pos_encoding=pos_enc,
            dir_encoding=dir_enc,
            renderer=renderer,
        )
        
        # 生成光线
        generator = RayGenerator(height=32, width=32, focal_length=16.0)
        rays_o, rays_d = generator.get_rays_simple()
        rays_o = rays_o.reshape(-1, 3)
        rays_d = rays_d.reshape(-1, 3)
        
        # 渲染图像
        image = trainer.render_image(rays_o, rays_d, chunk_size=512)
        
        assert image.shape == (32 * 32, 3)
        assert (image >= 0).all()
        assert (image <= 1).all()
```

### 4.2 场景测试

```python
class TestSceneIntegration:
    def test_sphere_rendering(self):
        """测试球体渲染"""
        scene = SphereScene(radius=1.0, color=(1.0, 0.0, 0.0))
        
        # 查询球体内的点
        points_inside = torch.tensor([[0.0, 0.0, 0.0]])
        colors, densities = scene.query(points_inside)
        
        assert colors.shape == (1, 3)
        assert densities.shape == (1, 1)
        assert densities[0, 0] > 0
        
        # 查询球体外的点
        points_outside = torch.tensor([[2.0, 0.0, 0.0]])
        colors, densities = scene.query(points_outside)
        
        assert densities[0, 0] == 0
    
    def test_cube_rendering(self):
        """测试立方体渲染"""
        scene = CubeScene(size=1.0, color=(0.0, 1.0, 0.0))
        
        # 查询立方体内的点
        points_inside = torch.tensor([[0.5, 0.5, 0.5]])
        colors, densities = scene.query(points_inside)
        
        assert densities[0, 0] > 0
        
        # 查询立方体外的点
        points_outside = torch.tensor([[2.0, 0.0, 0.0]])
        colors, densities = scene.query(points_outside)
        
        assert densities[0, 0] == 0
```

## 5. 性能测试

### 5.1 内存测试

```python
class TestMemoryUsage:
    def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建大模型
        model = NeRFModel(hidden_dim=256, num_layers=8)
        
        # 前向传播
        positions = torch.randn(10000, 63)
        directions = torch.randn(10000, 27)
        density, color = model(positions, directions)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"内存增加: {memory_increase:.2f} MB")
        assert memory_increase < 1000  # 不超过 1GB
```

### 5.2 速度测试

```python
class TestSpeed:
    def test_training_speed(self):
        """测试训练速度"""
        import time
        
        # 创建组件
        model = NeRFModel(hidden_dim=128, num_layers=4)
        pos_enc = PositionalEncoding(input_dim=3, num_freqs=10)
        dir_enc = PositionalEncoding(input_dim=3, num_freqs=6)
        renderer = VolumeRenderer()
        
        # 准备数据
        positions = torch.randn(1024, 63)
        directions = torch.randn(1024, 27)
        
        # 测试速度
        start = time.time()
        for _ in range(100):
            density, color = model(positions, directions)
        elapsed = time.time() - start
        
        print(f"100 次前向传播: {elapsed:.3f}s")
        print(f"平均每次: {elapsed/100*1000:.3f}ms")
        
        assert elapsed < 10  # 不超过 10 秒
```

## 6. 边界情况测试

### 6.1 数值边界

```python
class TestNumericalEdgeCases:
    def test_zero_density(self):
        """测试零密度"""
        renderer = VolumeRenderer(white_background=False)
        
        colors = torch.randn(10, 32, 3)
        densities = torch.zeros(10, 32, 1)
        distances = torch.linspace(2.0, 6.0, 32).expand(10, 32)
        
        pixel_colors, _, extras = renderer(colors, densities, distances)
        
        # 应该是黑色背景
        assert torch.allclose(pixel_colors, torch.zeros_like(pixel_colors), atol=1e-5)
        assert not torch.isnan(pixel_colors).any()
    
    def test_very_high_density(self):
        """测试非常高密度"""
        renderer = VolumeRenderer(white_background=False)
        
        colors = torch.ones(10, 32, 3)
        densities = torch.ones(10, 32, 1) * 1000.0
        distances = torch.linspace(2.0, 6.0, 32).expand(10, 32)
        
        pixel_colors, _, extras = renderer(colors, densities, distances)
        
        # 应该接近第一个采样点的颜色
        assert not torch.isnan(pixel_colors).any()
        assert not torch.isinf(pixel_colors).any()
    
    def test_very_small_density(self):
        """测试非常小的密度"""
        renderer = VolumeRenderer(white_background=False)
        
        colors = torch.ones(10, 32, 3)
        densities = torch.ones(10, 32, 1) * 1e-10
        distances = torch.linspace(2.0, 6.0, 32).expand(10, 32)
        
        pixel_colors, _, extras = renderer(colors, densities, distances)
        
        # 应该接近背景
        assert not torch.isnan(pixel_colors).any()
```

### 6.2 形状边界

```python
class TestShapeEdgeCases:
    def test_single_ray(self):
        """测试单条光线"""
        rays_o = torch.randn(1, 3)
        rays_d = torch.randn(1, 3)
        rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)
        
        points, distances = sample_points_along_rays(
            rays_o, rays_d, near=2.0, far=6.0, num_samples=32
        )
        
        assert points.shape == (1, 32, 3)
        assert distances.shape == (1, 32)
    
    def test_single_sample(self):
        """测试单个采样点"""
        rays_o = torch.randn(10, 3)
        rays_d = torch.randn(10, 3)
        rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)
        
        points, distances = sample_points_along_rays(
            rays_o, rays_d, near=2.0, far=6.0, num_samples=1
        )
        
        assert points.shape == (10, 1, 3)
        assert distances.shape == (10, 1)
    
    def test_large_batch(self):
        """测试大批量"""
        rays_o = torch.randn(10000, 3)
        rays_d = torch.randn(10000, 3)
        rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)
        
        points, distances = sample_points_along_rays(
            rays_o, rays_d, near=2.0, far=6.0, num_samples=32
        )
        
        assert points.shape == (10000, 32, 3)
```

## 7. 设备兼容性测试

### 7.1 CPU 测试

```python
class TestCPU:
    def test_cpu_training(self):
        """测试 CPU 训练"""
        device = torch.device("cpu")
        
        model = NeRFModel().to(device)
        pos_enc = PositionalEncoding().to(device)
        dir_enc = PositionalEncoding().to(device)
        renderer = VolumeRenderer().to(device)
        
        # 训练一步
        positions = torch.randn(100, 63).to(device)
        directions = torch.randn(100, 27).to(device)
        
        density, color = model(positions, directions)
        
        assert density.device == device
        assert color.device == device
```

### 7.2 CUDA 测试

```python
class TestCUDA:
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA 不可用")
    def test_cuda_training(self):
        """测试 CUDA 训练"""
        device = torch.device("cuda")
        
        model = NeRFModel().to(device)
        pos_enc = PositionalEncoding().to(device)
        dir_enc = PositionalEncoding().to(device)
        renderer = VolumeRenderer().to(device)
        
        # 训练一步
        positions = torch.randn(100, 63).to(device)
        directions = torch.randn(100, 27).to(device)
        
        density, color = model(positions, directions)
        
        assert density.device == device
        assert color.device == device
```

## 8. 回归测试

### 8.1 结果一致性

```python
class TestConsistency:
    def test_deterministic_output(self):
        """测试确定性输出"""
        torch.manual_seed(42)
        
        model = NeRFModel()
        pos_enc = PositionalEncoding()
        dir_enc = PositionalEncoding()
        
        positions = torch.randn(10, 3)
        directions = torch.randn(10, 3)
        
        pos_encoded = pos_enc(positions)
        dir_encoded = dir_enc(directions)
        
        density1, color1 = model(pos_encoded, dir_encoded)
        
        # 再次运行
        density2, color2 = model(pos_encoded, dir_encoded)
        
        assert torch.allclose(density1, density2, atol=1e-6)
        assert torch.allclose(color1, color2, atol=1e-6)
```

## 9. 测试覆盖率

### 9.1 覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| positional_encoding | 95% |
| nerf_model | 90% |
| volume_renderer | 95% |
| ray_utils | 90% |
| scene | 85% |
| trainer | 80% |

### 9.2 生成覆盖率报告

```bash
# 生成覆盖率报告
pytest tests/ -v --cov=src --cov-report=html

# 查看报告
open htmlcov/index.html
```

## 10. 持续集成

### 10.1 CI 配置

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10]
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src --cov-report=xml
```

## 11. 测试最佳实践

### 11.1 测试原则

1. **独立性**：每个测试独立运行
2. **可重复**：测试结果一致
3. **快速**：测试应该快速执行
4. **清晰**：测试意图明确

### 11.2 命名规范

```python
# 测试文件
test_<module_name>.py

# 测试类
Test<ClassName>

# 测试方法
test_<what_is_tested>
```

### 11.3 断言规范

```python
# 使用明确的断言
assert result.shape == expected_shape
assert (result >= 0).all()
assert torch.allclose(result, expected, atol=1e-6)
assert not torch.isnan(result).any()
```

## 12. 总结

### 12.1 测试清单

- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 物理测试通过
- [ ] 边界情况测试通过
- [ ] 设备兼容性测试通过
- [ ] 性能测试通过
- [ ] 覆盖率达标

### 12.2 测试策略

1. **自底向上**：先测试基础组件
2. **逐步集成**：逐步组合组件
3. **物理验证**：验证物理正确性
4. **性能监控**：监控性能变化

### 12.3 常见问题

1. **测试失败**：检查输入数据和期望输出
2. **数值不稳定**：检查 eps 和激活函数
3. **内存问题**：减小测试数据规模
4. **设备问题**：检查 CUDA 可用性
