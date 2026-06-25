# 神经风格迁移 - 测试文档

## 1. 测试概述

### 1.1 测试目标

- 验证 Gram 矩阵计算的正确性
- 验证损失函数的正确性
- 验证风格迁移算法的正确性
- 验证工具函数的正确性
- 确保代码的健壮性和可靠性

### 1.2 测试策略

1. **单元测试**：测试每个函数和类的方法
2. **集成测试**：测试模块间的交互
3. **端到端测试**：测试完整的风格迁移流程
4. **性能测试**：测试内存使用和计算速度

### 1.3 测试工具

- **pytest**：测试框架
- **torch**：深度学习框架
- **numpy**：数值计算

## 2. Gram 矩阵测试

### 2.1 测试用例

```python
class TestGramMatrix:
    """Gram 矩阵函数测试"""

    def test_gram_matrix_shape(self):
        """测试 Gram 矩阵的输出形状"""
        batch_size = 2
        channels = 64
        height = 32
        width = 32

        features = torch.randn(batch_size, channels, height, width)
        gram = gram_matrix(features)

        assert gram.shape == (batch_size, channels, channels)

    def test_gram_matrix_symmetric(self):
        """测试 Gram 矩阵的对称性"""
        features = torch.randn(1, 32, 16, 16)
        gram = gram_matrix(features)

        # Gram 矩阵应该是对称的
        assert torch.allclose(gram, gram.transpose(1, 2), atol=1e-6)

    def test_gram_matrix_positive_semidefinite(self):
        """测试 Gram 矩阵是半正定的"""
        features = torch.randn(1, 16, 8, 8)
        gram = gram_matrix(features)

        # 计算特征值
        eigenvalues = torch.linalg.eigvalsh(gram)

        # 所有特征值应该非负
        assert torch.all(eigenvalues >= -1e-6)

    def test_gram_matrix_normalize(self):
        """测试 Gram 矩阵归一化"""
        features = torch.randn(1, 16, 8, 8)

        gram_normalized = gram_matrix(features, normalize=True)
        gram_unnormalized = gram_matrix(features, normalize=False)

        # 归一化后的应该更小
        num_elements = 8 * 8
        assert torch.allclose(gram_normalized * num_elements, gram_unnormalized, atol=1e-6)

    def test_gram_matrix_gradient(self):
        """测试 Gram 矩阵的梯度计算"""
        features = torch.randn(1, 16, 8, 8, requires_grad=True)
        gram = gram_matrix(features)
        loss = gram.sum()
        loss.backward()

        assert features.grad is not None
        assert features.grad.shape == features.shape
```

### 2.2 测试要点

1. **形状测试**：验证输出形状正确
2. **数学性质**：验证对称性和半正定性
3. **归一化**：验证归一化逻辑
4. **梯度传播**：验证梯度可以正确传播

## 3. 损失函数测试

### 3.1 内容损失测试

```python
class TestContentLoss:
    """内容损失测试"""

    def test_content_loss_zero(self):
        """测试相同特征的内容损失应该为 0"""
        loss_layer = ContentLoss(weight=1.0)
        features = torch.randn(1, 64, 32, 32)

        loss_layer.set_target(features)
        output = loss_layer(features)

        # 输出应该等于输入
        assert torch.allclose(output, features)
        # 损失应该接近 0
        assert torch.allclose(loss_layer.get_loss(), torch.tensor(0.0), atol=1e-6)

    def test_content_loss_positive(self):
        """测试不同特征的内容损失应该大于 0"""
        loss_layer = ContentLoss(weight=1.0)
        features1 = torch.randn(1, 64, 32, 32)
        features2 = torch.randn(1, 64, 32, 32)

        loss_layer.set_target(features1)
        loss_layer(features2)

        assert loss_layer.get_loss() > 0

    def test_content_loss_weight(self):
        """测试内容损失的权重"""
        features1 = torch.randn(1, 64, 32, 32)
        features2 = torch.randn(1, 64, 32, 32)

        loss1 = ContentLoss(weight=1.0)
        loss1.set_target(features1)
        loss1(features2)

        loss2 = ContentLoss(weight=2.0)
        loss2.set_target(features1)
        loss2(features2)

        # 权重加倍，损失应该加倍
        assert torch.allclose(loss2.get_loss(), loss1.get_loss() * 2.0, atol=1e-6)

    def test_content_loss_gradient(self):
        """测试内容损失的梯度传播"""
        loss_layer = ContentLoss(weight=1.0)
        target = torch.randn(1, 64, 32, 32)
        features = torch.randn(1, 64, 32, 32, requires_grad=True)

        loss_layer.set_target(target)
        output = loss_layer(features)
        loss = loss_layer.get_loss()
        loss.backward()

        assert features.grad is not None

    def test_content_loss_no_target_error(self):
        """测试未设置目标时的错误"""
        loss_layer = ContentLoss(weight=1.0)
        features = torch.randn(1, 64, 32, 32)

        with pytest.raises(ValueError, match="请先调用 set_target"):
            loss_layer(features)
```

### 3.2 风格损失测试

```python
class TestStyleLoss:
    """风格损失测试"""

    def test_style_loss_zero(self):
        """测试相同特征的风格损失应该接近 0"""
        loss_layer = StyleLoss(weight=1.0)
        features = torch.randn(1, 64, 32, 32)

        loss_layer.set_target(features)
        loss_layer(features)

        assert torch.allclose(loss_layer.get_loss(), torch.tensor(0.0), atol=1e-5)

    def test_style_loss_scale_invariance(self):
        """测试风格损失的缩放不变性"""
        loss_layer = StyleLoss(weight=1.0)
        features1 = torch.randn(1, 64, 32, 32)
        features2 = features1 * 2.0  # 缩放版本

        loss_layer.set_target(features1)
        loss_layer(features2)

        # 归一化后应该接近 0
        assert torch.allclose(loss_layer.get_loss(), torch.tensor(0.0), atol=1e-5)

    def test_style_loss_gradient(self):
        """测试风格损失的梯度传播"""
        loss_layer = StyleLoss(weight=1.0)
        target = torch.randn(1, 64, 32, 32)
        features = torch.randn(1, 64, 32, 32, requires_grad=True)

        loss_layer.set_target(target)
        loss_layer(features)
        loss = loss_layer.get_loss()
        loss.backward()

        assert features.grad is not None
```

### 3.3 全变分损失测试

```python
class TestTotalVariationLoss:
    """全变分损失测试"""

    def test_tv_loss_zero(self):
        """测试平滑图像的全变分损失应该接近 0"""
        loss_layer = TotalVariationLoss(weight=1.0)

        # 创建平滑图像（所有像素相同）
        image = torch.ones(1, 3, 32, 32)
        loss_layer(image)

        assert torch.allclose(loss_layer.get_loss(), torch.tensor(0.0), atol=1e-6)

    def test_tv_loss_positive(self):
        """测试噪声图像的全变分损失应该大于 0"""
        loss_layer = TotalVariationLoss(weight=1.0)

        # 创建噪声图像
        image = torch.randn(1, 3, 32, 32)
        loss_layer(image)

        assert loss_layer.get_loss() > 0

    def test_tv_loss_horizontal(self):
        """测试水平方向的全变分损失"""
        loss_layer = TotalVariationLoss(weight=1.0)

        # 创建只有水平变化的图像
        image = torch.zeros(1, 1, 4, 4)
        image[0, 0, :, 1] = 1.0  # 第二列设为 1

        loss_layer(image)

        # 应该有水平变化
        assert loss_layer.get_loss() > 0
```

## 4. 风格迁移测试

### 4.1 初始化测试

```python
class TestStyleTransfer:
    """风格迁移类测试"""

    @pytest.fixture
    def style_transfer(self):
        """创建风格迁移实例"""
        return StyleTransfer(
            content_layers=["conv4_2"],
            style_layers=["conv1_1", "conv2_1", "conv3_1"],
            content_weight=1.0,
            style_weight=1e6,
            tv_weight=1e-5,
            device="cpu",
        )

    def test_style_transfer_init(self, style_transfer):
        """测试风格迁移初始化"""
        assert style_transfer.content_layers == ["conv4_2"]
        assert style_transfer.style_layers == ["conv1_1", "conv2_1", "conv3_1"]
        assert style_transfer.content_weight == 1.0
        assert style_transfer.style_weight == 1e6
        assert style_transfer.tv_weight == 1e-5

    def test_style_transfer_model_build(self, style_transfer):
        """测试模型构建"""
        assert style_transfer.model is not None
        assert len(style_transfer.content_losses) > 0
        assert len(style_transfer.style_losses) > 0
```

### 4.2 前向传播测试

```python
    def test_style_transfer_set_targets(self, style_transfer, content_image, style_image):
        """测试设置目标特征"""
        style_transfer._set_targets(content_image, style_image)

        # 检查目标是否被设置
        for loss in style_transfer.content_losses:
            assert loss.target is not None

        for loss in style_transfer.style_losses:
            assert loss.target_gram is not None

    def test_style_transfer_forward(self, style_transfer, content_image, style_image):
        """测试前向传播"""
        style_transfer._set_targets(content_image, style_image)

        # 前向传播
        output = style_transfer.model(content_image)

        # 输出应该存在
        assert output is not None
        assert output.shape[0] == 1
```

### 4.3 风格迁移测试

```python
    def test_style_transfer_content_init(self, style_transfer, content_image, style_image):
        """测试内容初始化方法"""
        output = style_transfer.transfer(
            content_image=content_image,
            style_image=style_image,
            num_steps=5,
            init_method="content",
        )

        assert output.shape == content_image.shape

    def test_style_transfer_noise_init(self, style_transfer, content_image, style_image):
        """测试噪声初始化方法"""
        output = style_transfer.transfer(
            content_image=content_image,
            style_image=style_image,
            num_steps=5,
            init_method="noise",
            noise_ratio=0.6,
        )

        assert output.shape == content_image.shape

    def test_style_transfer_callback(self, style_transfer, content_image, style_image):
        """测试回调函数"""
        callback_calls = []

        def callback(step, loss_dict):
            callback_calls.append((step, loss_dict))

        style_transfer.transfer(
            content_image=content_image,
            style_image=style_image,
            num_steps=20,
            callback=callback,
        )

        # 应该有回调调用
        assert len(callback_calls) > 0

        # 检查回调参数
        for step, loss_dict in callback_calls:
            assert isinstance(step, int)
            assert "total_loss" in loss_dict
            assert "content_loss" in loss_dict
            assert "style_loss" in loss_dict
            assert "tv_loss" in loss_dict
```

### 4.4 错误处理测试

```python
    def test_style_transfer_invalid_optimizer(self, style_transfer, content_image, style_image):
        """测试无效优化器"""
        with pytest.raises(ValueError, match="未知的优化器类型"):
            style_transfer.transfer(
                content_image=content_image,
                style_image=style_image,
                num_steps=5,
                optimizer_type="invalid",
            )

    def test_style_transfer_invalid_init(self, style_transfer, content_image, style_image):
        """测试无效初始化方法"""
        with pytest.raises(ValueError, match="未知的初始化方法"):
            style_transfer.transfer(
                content_image=content_image,
                style_image=style_image,
                num_steps=5,
                init_method="invalid",
            )
```

## 5. 工具函数测试

### 5.1 噪声图像测试

```python
class TestCreateNoiseImage:
    """噪声图像创建测试"""

    def test_noise_ratio_zero(self):
        """测试噪声比例为 0"""
        content = torch.randn(1, 3, 32, 32)
        noise_image = create_noise_image(content, noise_ratio=0.0)

        # 应该完全等于内容图像
        assert torch.allclose(noise_image, content)

    def test_noise_ratio_one(self):
        """测试噪声比例为 1"""
        content = torch.randn(1, 3, 32, 32)
        noise_image = create_noise_image(content, noise_ratio=1.0)

        # 应该不等于内容图像
        assert not torch.allclose(noise_image, content)

    def test_noise_ratio_half(self):
        """测试噪声比例为 0.5"""
        content = torch.randn(1, 3, 32, 32)
        noise_image = create_noise_image(content, noise_ratio=0.5)

        # 应该在内容和噪声之间
        assert noise_image.shape == content.shape
```

### 5.2 设备测试

```python
class TestGetDevice:
    """设备获取测试"""

    def test_cpu_device(self):
        """测试 CPU 设备"""
        device = get_device("cpu")
        assert device == torch.device("cpu")

    def test_auto_device(self):
        """测试自动设备选择"""
        device = get_device("auto")
        assert device in [torch.device("cpu"), torch.device("cuda"), torch.device("mps")]
```

## 6. 测试运行

### 6.1 运行所有测试

```bash
# 运行所有测试
pytest tests/

# 运行所有测试并显示详细输出
pytest tests/ -v

# 运行所有测试并显示覆盖率
pytest tests/ --cov=src
```

### 6.2 运行特定测试

```bash
# 运行 Gram 矩阵测试
pytest tests/test_gram_matrix.py

# 运行损失函数测试
pytest tests/test_losses.py

# 运行风格迁移测试
pytest tests/test_style_transfer.py
```

### 6.3 运行特定测试用例

```bash
# 运行特定测试类
pytest tests/test_gram_matrix.py::TestGramMatrix

# 运行特定测试方法
pytest tests/test_gram_matrix.py::TestGramMatrix::test_gram_matrix_shape
```

## 7. 测试覆盖率

### 7.1 生成覆盖率报告

```bash
# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html

# 查看报告
open htmlcov/index.html
```

### 7.2 覆盖率目标

- **总体覆盖率**：> 80%
- **核心模块**：> 90%
- **关键函数**：100%

## 8. 持续集成

### 8.1 GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

## 9. 测试最佳实践

### 9.1 测试命名

- 使用描述性的测试名称
- 遵循 `test_<功能>_<场景>` 格式
- 例如：`test_gram_matrix_symmetric`

### 9.2 测试结构

- 使用 Arrange-Act-Assert 模式
- 每个测试只测试一个功能
- 使用 fixtures 共享测试数据

### 9.3 测试数据

- 使用随机数据测试一般情况
- 使用边界值测试边界情况
- 使用真实数据测试实际场景

### 9.4 测试隔离

- 每个测试独立运行
- 不依赖外部状态
- 清理测试产生的数据

## 10. 常见问题

### 10.1 测试失败

- 检查测试数据是否正确
- 检查期望值是否正确
- 检查代码逻辑是否正确

### 10.2 测试超时

- 减少测试数据大小
- 使用更快的优化器
- 减少优化步数

### 10.3 内存不足

- 减少测试数据大小
- 使用 CPU 而不是 GPU
- 及时清理不需要的张量
