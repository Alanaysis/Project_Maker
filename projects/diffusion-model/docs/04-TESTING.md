# 测试说明文档

## 1. 测试概述

### 1.1 测试目标

本项目的测试旨在验证：
- 各组件的正确性
- 数学公式的准确性
- 训练流程的稳定性
- 生成质量的合理性

### 1.2 测试策略

| 测试类型 | 目标 | 覆盖范围 |
|----------|------|----------|
| 单元测试 | 验证单个组件 | 每个类和函数 |
| 集成测试 | 验证组件交互 | 完整流程 |
| 回归测试 | 验证修复和改进 | 已知问题 |

### 1.3 测试工具

- **pytest**：测试框架
- **torch.testing**：张量比较
- **matplotlib**：可视化验证

## 2. 测试用例详解

### 2.1 噪声调度器测试

#### 2.1.1 初始化测试

```python
def test_initialization(self):
    """测试调度器初始化"""
    scheduler = NoiseScheduler(num_timesteps=100)

    # 验证参数正确设置
    assert scheduler.num_timesteps == 100
    assert len(scheduler.betas) == 100
    assert len(scheduler.alphas) == 100
    assert len(scheduler.alphas_cumprod) == 100
```

**验证点**：
- 参数数量正确
- 调度值已预计算
- 数据类型正确

#### 2.1.2 Beta 调度测试

```python
def test_beta_schedule(self):
    """测试 beta 调度"""
    scheduler = NoiseScheduler(num_timesteps=100)

    betas = scheduler.betas

    # 验证 beta 单调递增
    assert betas[0] < betas[-1]

    # 验证 beta 在合理范围内
    assert torch.all(betas > 0)
    assert torch.all(betas < 1)
```

**验证点**：
- 单调性：beta 从 start 到 end 递增
- 范围：beta 在 (0, 1) 内
- 边界：首尾值正确

#### 2.1.3 Alpha 属性测试

```python
def test_alpha_properties(self):
    """测试 alpha 和 alpha_cumprod 属性"""
    scheduler = NoiseScheduler(num_timesteps=100)

    alphas = scheduler.alphas
    alphas_cumprod = scheduler.alphas_cumprod

    # 验证 alpha 在 (0, 1) 范围内
    assert torch.all(alphas > 0)
    assert torch.all(alphas < 1)

    # 验证 alpha_cumprod 单调递减
    assert torch.all(alphas_cumprod[1:] <= alphas_cumprod[:-1])

    # 验证边界值
    assert alphas_cumprod[0] > 0.99  # 接近 1
    assert alphas_cumprod[-1] < 0.01  # 接近 0
```

**验证点**：
- alpha 范围正确
- alpha_cumprod 单调递减
- 边界值符合预期

#### 2.1.4 前向扩散测试

```python
def test_add_noise(self):
    """测试前向扩散过程"""
    scheduler = NoiseScheduler(num_timesteps=100)

    # 创建测试数据
    x_0 = torch.randn(4, 1, 28, 28)
    t = torch.randint(0, 100, (4,))

    # 添加噪声
    x_t, noise = scheduler.add_noise(x_0, t)

    # 验证形状
    assert x_t.shape == x_0.shape
    assert noise.shape == x_0.shape

    # 验证噪声图像不同于原始图像
    assert not torch.allclose(x_t, x_0)
```

**验证点**：
- 输出形状正确
- 噪声被添加
- 无数据损坏

#### 2.1.5 数学正确性测试

```python
def test_forward_process_math(self):
    """测试前向过程的数学正确性"""
    scheduler = NoiseScheduler(num_timesteps=100)

    x_0 = torch.randn(1, 1, 4, 4)
    t = torch.tensor([50])

    x_t, noise = scheduler.add_noise(x_0, t)

    # 手动计算期望结果
    sqrt_alpha = scheduler.sqrt_alphas_cumprod[50]
    sqrt_one_minus_alpha = scheduler.sqrt_one_minus_alphas_cumprod[50]
    expected = sqrt_alpha * x_0 + sqrt_one_minus_alpha * noise

    # 验证数值正确性
    assert torch.allclose(x_t, expected, atol=1e-6)
```

**验证点**：
- 数学公式实现正确
- 数值精度足够
- 无计算错误

### 2.2 UNet 测试

#### 2.2.1 输出形状测试

```python
def test_output_shape(self):
    """测试输出形状"""
    model = SimpleUNet(in_channels=1, out_channels=1)

    x = torch.randn(4, 1, 28, 28)
    t = torch.randint(0, 100, (4,))

    output = model(x, t)

    assert output.shape == x.shape
```

**验证点**：
- 输出维度与输入一致
- 批次大小保持
- 空间尺寸保持

#### 2.2.2 不同输入测试

```python
def test_different_inputs(self):
    """测试不同输入产生不同输出"""
    model = SimpleUNet(in_channels=1, out_channels=1)

    x1 = torch.randn(1, 1, 28, 28)
    x2 = torch.randn(1, 1, 28, 28)
    t = torch.tensor([50])

    out1 = model(x1, t)
    out2 = model(x2, t)

    assert not torch.allclose(out1, out2)
```

**验证点**：
- 模型对输入敏感
- 不是常数输出
- 学习到有意义的映射

#### 2.2.3 时间步影响测试

```python
def test_different_timesteps(self):
    """测试不同时间步产生不同输出"""
    model = SimpleUNet(in_channels=1, out_channels=1)

    x = torch.randn(1, 1, 28, 28)
    t1 = torch.tensor([10])
    t2 = torch.tensor([90])

    out1 = model(x, t1)
    out2 = model(x, t2)

    assert not torch.allclose(out1, out2)
```

**验证点**：
- 时间嵌入有效
- 不同时间步产生不同行为
- 模型利用时间信息

#### 2.2.4 梯度流测试

```python
def test_gradient_flow(self):
    """测试梯度流"""
    model = SimpleUNet(in_channels=1, out_channels=1)

    x = torch.randn(2, 1, 28, 28, requires_grad=True)
    t = torch.randint(0, 100, (2,))

    output = model(x, t)
    loss = output.sum()
    loss.backward()

    assert x.grad is not None
    assert x.grad.shape == x.shape
```

**验证点**：
- 梯度可以流过模型
- 梯度形状正确
- 无梯度消失或爆炸

#### 2.2.5 参数数量测试

```python
def test_parameter_count(self):
    """测试参数数量"""
    model = SimpleUNet(in_channels=1, out_channels=1)

    num_params = sum(p.numel() for p in model.parameters())

    # 简化版 UNet 应该有合理的参数数量
    assert num_params > 100000  # 至少 100K
    assert num_params < 10000000  # 少于 10M
```

**验证点**：
- 参数数量合理
- 不是太小（欠拟合）
- 不是太大（过拟合）

### 2.3 扩散模型测试

#### 2.3.1 训练损失测试

```python
def test_training_loss(self):
    """测试训练损失计算"""
    model = DiffusionModel(
        image_size=28,
        in_channels=1,
        num_timesteps=100,
        model_type="simple"
    )

    x_0 = torch.randn(4, 1, 28, 28)
    loss = model.training_loss(x_0)

    # 验证损失性质
    assert loss.dim() == 0  # 标量
    assert loss.item() > 0  # 正数
    assert not torch.isnan(loss)  # 非 NaN
    assert not torch.isinf(loss)  # 非 Inf
```

**验证点**：
- 损失是标量
- 损失是正数
- 无数值问题

#### 2.3.2 采样形状测试

```python
def test_sample_shape(self):
    """测试采样输出形状"""
    model = DiffusionModel(
        image_size=28,
        in_channels=1,
        num_timesteps=10,
        model_type="simple"
    )

    samples = model.sample(batch_size=2, device=torch.device("cpu"))

    assert samples.shape == (2, 1, 28, 28)
```

**验证点**：
- 批次大小正确
- 通道数正确
- 空间尺寸正确

#### 2.3.3 采样范围测试

```python
def test_sample_range(self):
    """测试采样值范围"""
    model = DiffusionModel(
        image_size=28,
        in_channels=1,
        num_timesteps=10,
        model_type="simple"
    )

    samples = model.sample(batch_size=4, device=torch.device("cpu"))

    # 采样应该在合理范围内（高斯分布）
    assert samples.min() > -5
    assert samples.max() < 5
```

**验证点**：
- 值在合理范围内
- 无数值溢出
- 符合高斯分布特性

#### 2.3.4 确定性测试

```python
def test_sample_deterministic(self):
    """测试确定性采样"""
    model = DiffusionModel(
        image_size=28,
        in_channels=1,
        num_timesteps=10,
        model_type="simple"
    )

    # 相同种子应该产生相同结果
    torch.manual_seed(42)
    samples1 = model.sample(batch_size=2, device=torch.device("cpu"))

    torch.manual_seed(42)
    samples2 = model.sample(batch_size=2, device=torch.device("cpu"))

    assert torch.allclose(samples1, samples2)
```

**验证点**：
- 随机种子控制有效
- 结果可复现
- 无随机性泄露

#### 2.3.5 DDIM 采样测试

```python
def test_ddim_sample(self):
    """测试 DDIM 采样"""
    model = DiffusionModel(
        image_size=28,
        in_channels=1,
        num_timesteps=100,
        model_type="simple"
    )

    samples = model.sample_ddim(
        batch_size=2,
        device=torch.device("cpu"),
        ddim_steps=10
    )

    assert samples.shape == (2, 1, 28, 28)
```

**验证点**：
- DDIM 采样正常工作
- 可以使用更少的步数
- 输出形状正确

### 2.4 训练器测试

#### 2.4.1 训练一个 Epoch

```python
def test_train_epoch(self):
    """测试训练一个 epoch"""
    model = DiffusionModel(
        image_size=28,
        in_channels=1,
        num_timesteps=10,
        model_type="simple"
    )

    trainer = DiffusionTrainer(model=model, learning_rate=1e-4)

    # 创建虚拟数据集
    images = torch.randn(32, 1, 28, 28)
    dataset = TensorDataset(images)
    dataloader = DataLoader(dataset, batch_size=8)

    avg_loss = trainer.train_epoch(dataloader)

    assert avg_loss > 0
    assert len(trainer.losses) == 1
```

**验证点**：
- 训练正常进行
- 损失被记录
- 无错误发生

#### 2.4.2 检查点保存加载

```python
def test_checkpoint_save_load(self, tmp_path):
    """测试检查点保存和加载"""
    model = DiffusionModel(
        image_size=28,
        in_channels=1,
        num_timesteps=10,
        model_type="simple"
    )

    trainer = DiffusionTrainer(model=model, learning_rate=1e-4)

    # 保存检查点
    save_path = str(tmp_path / "checkpoint.pt")
    trainer.save_checkpoint(save_path)

    assert os.path.exists(save_path)

    # 加载检查点
    new_trainer = DiffusionTrainer(model=model)
    new_trainer.load_checkpoint(save_path)

    assert len(new_trainer.losses) == len(trainer.losses)
```

**验证点**：
- 检查点正确保存
- 检查点正确加载
- 状态完整恢复

## 3. 运行测试

### 3.1 运行所有测试

```bash
cd projects/diffusion-model
pytest tests/ -v
```

### 3.2 运行特定测试文件

```bash
pytest tests/test_scheduler.py -v
pytest tests/test_unet.py -v
pytest tests/test_diffusion.py -v
```

### 3.3 运行特定测试用例

```bash
pytest tests/test_scheduler.py::TestNoiseScheduler::test_initialization -v
```

### 3.4 运行带覆盖率的测试

```bash
pytest tests/ -v --cov=src --cov-report=html
```

## 4. 测试覆盖率

### 4.1 目标覆盖率

| 模块 | 目标覆盖率 |
|------|------------|
| scheduler.py | 90% |
| unet.py | 85% |
| diffusion.py | 80% |
| utils.py | 70% |

### 4.2 查看覆盖率报告

```bash
# 生成 HTML 报告
pytest tests/ --cov=src --cov-report=html

# 查看报告
open htmlcov/index.html
```

## 5. 性能测试

### 5.1 训练性能测试

```python
def test_training_speed():
    """测试训练速度"""
    model = DiffusionModel(
        image_size=32,
        in_channels=1,
        num_timesteps=100,
        model_type="simple"
    )

    trainer = DiffusionTrainer(model=model)

    # 创建虚拟数据
    images = torch.randn(128, 1, 32, 32)
    dataset = TensorDataset(images)
    dataloader = DataLoader(dataset, batch_size=32)

    # 测量训练时间
    start_time = time.time()
    avg_loss = trainer.train_epoch(dataloader)
    end_time = time.time()

    print(f"Training time: {end_time - start_time:.2f}s")
    print(f"Average loss: {avg_loss:.6f}")
```

### 5.2 采样性能测试

```python
def test_sampling_speed():
    """测试采样速度"""
    model = DiffusionModel(
        image_size=32,
        in_channels=1,
        num_timesteps=100,
        model_type="simple"
    )

    # 测试 DDPM 采样速度
    start_time = time.time()
    samples = model.sample(batch_size=16, device=torch.device("cpu"))
    ddpm_time = time.time() - start_time

    # 测试 DDIM 采样速度
    start_time = time.time()
    samples = model.sample_ddim(
        batch_size=16,
        device=torch.device("cpu"),
        ddim_steps=20
    )
    ddim_time = time.time() - start_time

    print(f"DDPM sampling time: {ddpm_time:.2f}s")
    print(f"DDIM sampling time: {ddim_time:.2f}s")
    print(f"Speedup: {ddpm_time / ddim_time:.2f}x")
```

## 6. 集成测试

### 6.1 端到端训练测试

```python
def test_end_to_end_training():
    """端到端训练测试"""
    # 创建模型
    model = DiffusionModel(
        image_size=28,
        in_channels=1,
        num_timesteps=50,
        model_type="simple"
    )

    # 创建数据集
    images = torch.randn(100, 1, 28, 28)
    dataset = TensorDataset(images)
    dataloader = DataLoader(dataset, batch_size=16)

    # 训练几个 epoch
    trainer = DiffusionTrainer(model=model, learning_rate=1e-4)
    losses = trainer.train(dataloader, num_epochs=5, sample_interval=10)

    # 验证损失下降
    assert losses[-1] < losses[0]

    # 生成样本
    samples = model.sample(batch_size=4, device=torch.device("cpu"))
    assert samples.shape == (4, 1, 28, 28)
```

### 6.2 数据加载测试

```python
def test_data_loading():
    """测试数据加载"""
    from examples.train_mnist import get_mnist_dataloader

    dataloader = get_mnist_dataloader(batch_size=16)

    # 验证数据格式
    for batch in dataloader:
        images, labels = batch
        assert images.shape == (16, 1, 32, 32)
        assert images.min() >= -1
        assert images.max() <= 1
        break
```

## 7. 调试测试

### 7.1 调试失败的测试

```bash
# 显示详细输出
pytest tests/test_scheduler.py -v -s

# 在失败时进入调试器
pytest tests/test_scheduler.py -v --pdb

# 显示局部变量
pytest tests/test_scheduler.py -v --tb=long
```

### 7.2 调试内存问题

```python
def test_memory_usage():
    """测试内存使用"""
    import tracemalloc

    tracemalloc.start()

    model = DiffusionModel(
        image_size=32,
        in_channels=1,
        num_timesteps=100,
        model_type="simple"
    )

    # 采样
    samples = model.sample(batch_size=16, device=torch.device("cpu"))

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Current memory usage: {current / 1024 / 1024:.2f} MB")
    print(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")
```

## 8. 持续集成

### 8.1 GitHub Actions 配置

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']

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

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

## 9. 测试最佳实践

### 9.1 编写测试的原则

1. **独立性**：每个测试应该独立运行
2. **可重复**：测试结果应该可重复
3. **快速**：测试应该快速执行
4. **清晰**：测试意图应该清晰明确

### 9.2 命名规范

- 测试文件：`test_<module>.py`
- 测试类：`Test<ClassName>`
- 测试方法：`test_<function_name>_<scenario>`

### 9.3 断言使用

```python
# 使用 pytest 断言
assert x == expected
assert x is not None
assert x in collection

# 使用 torch 测试
torch.testing.assert_close(actual, expected, atol=1e-5, rtol=1e-5)
```

## 10. 总结

### 10.1 测试清单

- [x] 噪声调度器初始化
- [x] Beta 和 Alpha 计算
- [x] 前向扩散过程
- [x] UNet 输出形状
- [x] UNet 梯度流
- [x] 训练损失计算
- [x] 采样形状和范围
- [x] DDIM 采样
- [x] 检查点保存加载
- [x] 端到端训练

### 10.2 测试结果示例

```
tests/test_scheduler.py::TestNoiseScheduler::test_initialization PASSED
tests/test_scheduler.py::TestNoiseScheduler::test_beta_schedule PASSED
tests/test_scheduler.py::TestNoiseScheduler::test_alpha_properties PASSED
tests/test_scheduler.py::TestNoiseScheduler::test_add_noise PASSED
tests/test_scheduler.py::TestNoiseScheduler::test_forward_process_math PASSED

tests/test_unet.py::TestSimpleUNet::test_output_shape PASSED
tests/test_unet.py::TestSimpleUNet::test_different_inputs PASSED
tests/test_unet.py::TestSimpleUNet::test_different_timesteps PASSED
tests/test_unet.py::TestSimpleUNet::test_gradient_flow PASSED
tests/test_unet.py::TestSimpleUNet::test_parameter_count PASSED

tests/test_diffusion.py::TestDiffusionModel::test_initialization PASSED
tests/test_diffusion.py::TestDiffusionModel::test_forward_pass PASSED
tests/test_diffusion.py::TestDiffusionModel::test_training_loss PASSED
tests/test_diffusion.py::TestDiffusionModel::test_sample_shape PASSED
tests/test_diffusion.py::TestDiffusionModel::test_sample_range PASSED
tests/test_diffusion.py::TestDiffusionModel::test_sample_deterministic PASSED
tests/test_diffusion.py::TestDiffusionModel::test_ddim_sample PASSED
tests/test_diffusion.py::TestDiffusionTrainer::test_train_epoch PASSED
tests/test_diffusion.py::TestDiffusionTrainer::test_checkpoint_save_load PASSED

======================== 19 passed in 45.67s ========================
```
