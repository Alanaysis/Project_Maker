# 超分辨率测试文档

## 1. 测试概述

### 1.1 测试目标

- 验证模型实现的正确性
- 验证数据处理的正确性
- 验证训练流程的正确性
- 验证评估功能的正确性

### 1.2 测试范围

- 单元测试：测试各个模块的功能
- 集成测试：测试模块之间的交互
- 性能测试：测试性能指标

### 1.3 测试工具

- pytest：测试框架
- torch：深度学习框架
- numpy：数值计算

## 2. 单元测试

### 2.1 模型测试

#### 2.1.1 SRCNN 测试

**测试文件**：`tests/test_models.py::TestSRCNN`

**测试用例**：

```python
def test_init():
    """测试模型初始化"""
    model = SRCNN(num_channels=3, num_features=64, hidden_features=32)
    assert model is not None

def test_forward():
    """测试前向传播"""
    model = SRCNN(num_channels=3, num_features=64, hidden_features=32)
    x = torch.randn(2, 3, 64, 64)
    output = model(x)
    assert output.shape == (2, 3, 64, 64)

def test_different_channels():
    """测试不同通道数"""
    model_gray = SRCNN(num_channels=1)
    x_gray = torch.randn(1, 1, 32, 32)
    output_gray = model_gray(x_gray)
    assert output_gray.shape == (1, 1, 32, 32)

def test_gradient_flow():
    """测试梯度流动"""
    model = SRCNN()
    x = torch.randn(1, 3, 32, 32, requires_grad=True)
    output = model(x)
    loss = output.mean()
    loss.backward()
    assert x.grad is not None
```

#### 2.1.2 ESPCN 测试

**测试文件**：`tests/test_models.py::TestESPCN`

**测试用例**：

```python
def test_init():
    """测试模型初始化"""
    model = ESPCN(scale_factor=2, num_channels=3, num_features=64)
    assert model is not None

def test_forward():
    """测试前向传播"""
    model = ESPCN(scale_factor=2, num_channels=3, num_features=64)
    x = torch.randn(2, 3, 32, 32)
    output = model(x)
    assert output.shape == (2, 3, 64, 64)

def test_scale_factor_3():
    """测试 3 倍上采样"""
    model = ESPCN(scale_factor=3, num_channels=3, num_features=64)
    x = torch.randn(1, 3, 16, 16)
    output = model(x)
    assert output.shape == (1, 3, 48, 48)

def test_gradient_flow():
    """测试梯度流动"""
    model = ESPCN(scale_factor=2)
    x = torch.randn(1, 3, 16, 16, requires_grad=True)
    output = model(x)
    loss = output.mean()
    loss.backward()
    assert x.grad is not None
```

#### 2.1.3 PixelShuffle 测试

**测试文件**：`tests/test_models.py::TestPixelShuffle`

**测试用例**：

```python
def test_init():
    """测试初始化"""
    ps = PixelShuffle(scale_factor=2)
    assert ps.scale_factor == 2

def test_forward():
    """测试前向传播"""
    ps = PixelShuffle(scale_factor=2)
    x = torch.randn(1, 12, 4, 4)
    output = ps(x)
    assert output.shape == (1, 3, 8, 8)
```

#### 2.1.4 EDSR 测试

**测试文件**：`tests/test_models.py::TestEDSR`

**测试用例**：

```python
def test_init():
    """测试模型初始化"""
    model = EDSR(scale_factor=2, num_channels=3, num_features=64, num_blocks=16)
    assert model is not None

def test_forward():
    """测试前向传播"""
    model = EDSR(scale_factor=2, num_channels=3, num_features=64, num_blocks=4)
    x = torch.randn(1, 3, 16, 16)
    output = model(x)
    assert output.shape == (1, 3, 32, 32)
```

### 2.2 数据集测试

**测试文件**：`tests/test_dataset.py`

**测试用例**：

```python
def test_init():
    """测试数据集初始化"""
    dataset = SRDataset(hr_dir=temp_dir, scale_factor=2, patch_size=32)
    assert len(dataset) == 5

def test_getitem_training():
    """测试训练模式获取数据"""
    dataset = SRDataset(hr_dir=temp_dir, scale_factor=2, patch_size=32, is_training=True)
    lr, hr = dataset[0]
    assert lr.shape[0] == 3
    assert hr.shape[0] == 3
    assert hr.shape[1] == 32
    assert lr.shape[1] == 16

def test_getitem_evaluation():
    """测试评估模式获取数据"""
    dataset = SRDataset(hr_dir=temp_dir, scale_factor=2, patch_size=32, is_training=False)
    lr, hr = dataset[0]
    assert hr.shape[1] == lr.shape[1] * 2
```

### 2.3 训练器测试

**测试文件**：`tests/test_trainer.py`

**测试用例**：

```python
def test_init_srcnn():
    """测试 SRCNN 训练器初始化"""
    trainer = SRTrainer(model_name='srcnn', scale_factor=2, checkpoint_dir=checkpoint_dir)
    assert trainer.model_name == 'srcnn'

def test_train_srcnn():
    """测试训练 SRCNN 模型"""
    trainer = SRTrainer(model_name='srcnn', scale_factor=2, checkpoint_dir=checkpoint_dir)
    history = trainer.train(train_dir=train_dir, epochs=2, batch_size=2, patch_size=32)
    assert len(history['train_loss']) == 2

def test_save_checkpoint():
    """测试保存检查点"""
    trainer = SRTrainer(model_name='srcnn', scale_factor=2, checkpoint_dir=checkpoint_dir)
    trainer.train(train_dir=train_dir, epochs=1, batch_size=2, patch_size=32)
    assert os.path.exists(os.path.join(checkpoint_dir, 'latest.pth'))

def test_load_checkpoint():
    """测试加载检查点"""
    trainer1 = SRTrainer(model_name='srcnn', scale_factor=2, checkpoint_dir=checkpoint_dir)
    trainer1.train(train_dir=train_dir, epochs=1, batch_size=2, patch_size=32)

    trainer2 = SRTrainer(model_name='srcnn', scale_factor=2, checkpoint_dir=checkpoint_dir)
    trainer2.load_checkpoint(os.path.join(checkpoint_dir, 'latest.pth'))

    for p1, p2 in zip(trainer1.model.parameters(), trainer2.model.parameters()):
        assert torch.allclose(p1, p2)
```

## 3. 集成测试

### 3.1 端到端训练测试

**测试目标**：验证完整的训练流程

**测试步骤**：
1. 创建合成数据集
2. 创建训练器
3. 训练模型
4. 保存检查点
5. 加载检查点
6. 验证模型参数

**测试代码**：
```python
def test_end_to_end_training():
    # 创建合成数据集
    create_synthetic_dataset('test_data/train', num_images=10, image_size=64)
    create_synthetic_dataset('test_data/val', num_images=5, image_size=64)

    # 创建训练器
    trainer = SRTrainer(model_name='espcn', scale_factor=2, checkpoint_dir='test_checkpoints')

    # 训练模型
    history = trainer.train(
        train_dir='test_data/train',
        val_dir='test_data/val',
        epochs=2,
        batch_size=2,
        patch_size=32
    )

    # 验证训练历史
    assert len(history['train_loss']) == 2
    assert len(history['val_loss']) == 2

    # 验证检查点
    assert os.path.exists('test_checkpoints/latest.pth')
    assert os.path.exists('test_checkpoints/best.pth')
```

### 3.2 端到端评估测试

**测试目标**：验证完整的评估流程

**测试步骤**：
1. 创建合成数据集
2. 创建并训练模型
3. 保存检查点
4. 创建评估器
5. 加载检查点
6. 评估模型
7. 验证评估结果

**测试代码**：
```python
def test_end_to_end_evaluation():
    # 创建合成数据集
    create_synthetic_dataset('test_data/test', num_images=5, image_size=64)

    # 创建并训练模型
    trainer = SRTrainer(model_name='srcnn', scale_factor=2, checkpoint_dir='test_checkpoints')
    trainer.train(train_dir='test_data/train', epochs=1, batch_size=2, patch_size=32)

    # 创建评估器
    evaluator = SREvaluator(model_name='srcnn', scale_factor=2)
    evaluator.load_checkpoint('test_checkpoints/best.pth')

    # 评估模型
    results = evaluator.evaluate(test_dir='test_data/test')

    # 验证评估结果
    assert 'psnr' in results
    assert 'ssim' in results
    assert results['psnr'] > 0
    assert 0 <= results['ssim'] <= 1
```

## 4. 性能测试

### 4.1 训练性能测试

**测试目标**：验证训练速度和内存使用

**测试指标**：
- 训练速度（样本/秒）
- 内存使用（MB）
- GPU 使用率

**测试代码**：
```python
def test_training_performance():
    # 创建大型数据集
    create_synthetic_dataset('perf_data/train', num_images=100, image_size=256)

    # 创建训练器
    trainer = SRTrainer(model_name='espcn', scale_factor=2)

    # 测量训练时间
    import time
    start_time = time.time()

    trainer.train(
        train_dir='perf_data/train',
        epochs=1,
        batch_size=16,
        patch_size=96
    )

    end_time = time.time()
    training_time = end_time - start_time

    print(f"Training time: {training_time:.2f} seconds")
    print(f"Samples per second: {100 / training_time:.2f}")
```

### 4.2 推理性能测试

**测试目标**：验证推理速度

**测试指标**：
- 推理速度（毫秒/图像）
- 吞吐量（图像/秒）

**测试代码**：
```python
def test_inference_performance():
    # 创建模型
    model = get_model('espcn', scale_factor=2)
    model.eval()

    # 创建输入
    x = torch.randn(1, 3, 64, 64)

    # 预热
    for _ in range(10):
        with torch.no_grad():
            model(x)

    # 测量推理时间
    import time
    start_time = time.time()

    for _ in range(100):
        with torch.no_grad():
            model(x)

    end_time = time.time()
    inference_time = (end_time - start_time) / 100 * 1000

    print(f"Inference time: {inference_time:.2f} ms/image")
    print(f"Throughput: {1000 / inference_time:.2f} images/second")
```

## 5. 测试运行

### 5.1 运行所有测试

```bash
pytest tests/ -v
```

### 5.2 运行特定测试

```bash
# 运行模型测试
pytest tests/test_models.py -v

# 运行数据集测试
pytest tests/test_dataset.py -v

# 运行训练器测试
pytest tests/test_trainer.py -v
```

### 5.3 运行性能测试

```bash
pytest tests/test_performance.py -v -s
```

## 6. 测试覆盖率

### 6.1 生成覆盖率报告

```bash
pip install pytest-cov
pytest tests/ --cov=src --cov-report=html
```

### 6.2 覆盖率目标

- 语句覆盖率：>90%
- 分支覆盖率：>80%
- 函数覆盖率：>95%

## 7. 测试最佳实践

### 7.1 测试命名

- 使用描述性的测试名称
- 使用 `test_` 前缀
- 使用下划线分隔单词

### 7.2 测试结构

- 使用 `pytest.fixture` 共享测试数据
- 使用 `pytest.mark` 标记测试类型
- 使用 `pytest.raises` 测试异常

### 7.3 测试数据

- 使用合成数据集
- 使用临时目录
- 测试后清理数据

### 7.4 测试隔离

- 每个测试独立运行
- 不依赖外部资源
- 不修改全局状态

## 8. 常见问题

### 8.1 内存不足

**问题**：测试时内存不足

**解决**：
- 减小测试数据大小
- 使用 CPU 而不是 GPU
- 使用更小的模型

### 8.2 测试超时

**问题**：测试运行时间过长

**解决**：
- 减少训练轮数
- 使用更小的数据集
- 跳过长时间测试

### 8.3 随机性

**问题**：测试结果不一致

**解决**：
- 设置随机种子
- 使用固定的数据
- 使用确定性算法

## 9. 测试报告

### 9.1 报告格式

```
========================= test session starts ==========================
platform linux -- Python 3.8.10, pytest-7.3.0
collected 30 items

tests/test_models.py::TestSRCNN::test_init PASSED                [  3%]
tests/test_models.py::TestSRCNN::test_forward PASSED             [  6%]
tests/test_models.py::TestESPCN::test_init PASSED                [  9%]
...

========================= 30 passed in 45.23s =========================
```

### 9.2 报告分析

- 检查失败的测试
- 分析失败原因
- 修复问题
- 重新运行测试
