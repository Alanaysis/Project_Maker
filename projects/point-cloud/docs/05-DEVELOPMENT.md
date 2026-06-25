# 开发文档 - 点云处理

## 1. 开发环境

### 1.1 环境要求

- Python >= 3.8
- PyTorch >= 2.0
- NumPy >= 1.24
- Matplotlib >= 3.7
- Open3D >= 0.17 (可选)

### 1.2 安装步骤

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 1.3 开发工具

| 工具 | 用途 | 配置 |
|------|------|------|
| VS Code | IDE | Python 插件 |
| pytest | 测试 | pytest.ini |
| black | 格式化 | pyproject.toml |
| mypy | 类型检查 | mypy.ini |

## 2. 项目结构

```
point-cloud/
├── src/                    # 源代码
│   ├── __init__.py        # 包初始化
│   ├── pointnet.py        # PointNet 模型
│   ├── dataset.py         # 数据集
│   ├── trainer.py         # 训练器
│   ├── visualization.py   # 可视化
│   └── utils.py           # 工具函数
├── tests/                  # 测试代码
├── docs/                   # 文档
├── examples/               # 示例
├── train.py               # 训练脚本
├── requirements.txt       # 依赖
├── README.md              # 说明
└── LEARNING_NOTES.md      # 学习笔记
```

## 3. 开发流程

### 3.1 功能开发

1. **创建分支**
   ```bash
   git checkout -b feature/xxx
   ```

2. **编写代码**
   - 遵循 PEP 8 规范
   - 添加类型注解
   - 编写文档字符串

3. **编写测试**
   - 单元测试覆盖核心功能
   - 集成测试覆盖完整流程

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加 xxx 功能"
   ```

### 3.2 代码规范

#### 命名规范

- 类名: `PascalCase`
- 函数名: `snake_case`
- 变量名: `snake_case`
- 常量名: `UPPER_SNAKE_CASE`

#### 文档字符串

```python
def function_name(param1: int, param2: str) -> bool:
    """
    函数简短描述

    详细描述（如果需要）。

    Args:
        param1: 参数1描述
        param2: 参数2描述

    Returns:
        返回值描述

    Raises:
        ValueError: 异常描述
    """
    pass
```

#### 类型注解

```python
from typing import List, Tuple, Optional

def process_points(
    points: np.ndarray,
    labels: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    pass
```

## 4. 测试指南

### 4.1 测试命名

```python
class TestClassName:
    def test_method_name_scenario(self):
        """测试描述"""
        pass
```

### 4.2 测试结构

```python
def test_something():
    # 1. 准备 (Arrange)
    model = PointNetClassifier(num_classes=10)
    x = torch.randn(4, 3, 1024)

    # 2. 执行 (Act)
    logits, _, _ = model(x)

    # 3. 断言 (Assert)
    assert logits.shape == (4, 10)
```

### 4.3 运行测试

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/test_pointnet.py

# 运行特定测试
pytest tests/test_pointnet.py::TestTNet::test_output_shape

# 显示输出
pytest -v -s
```

## 5. 调试指南

### 5.1 常见问题

#### 问题 1: 形状不匹配

```python
# 错误: Expected 3D tensor, got 2D
x = torch.randn(1024, 3)
model(x)  # 错误

# 正确: 添加批次维度
x = torch.randn(1, 1024, 3)
x = x.transpose(1, 2)  # (1, 3, 1024)
model(x)
```

#### 问题 2: 梯度为 None

```python
# 检查 requires_grad
for name, param in model.named_parameters():
    print(f"{name}: requires_grad={param.requires_grad}")
```

#### 问题 3: CUDA 内存不足

```python
# 减小批次大小
batch_size = 16  # 而不是 32

# 或使用梯度累积
for i, (points, labels) in enumerate(dataloader):
    loss = compute_loss(points, labels)
    loss = loss / accumulation_steps
    loss.backward()

    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

### 5.2 调试技巧

1. **打印形状**
   ```python
   print(f"x.shape: {x.shape}")
   print(f"x.dtype: {x.dtype}")
   ```

2. **检查梯度**
   ```python
   loss.backward()
   for name, param in model.named_parameters():
       if param.grad is not None:
           print(f"{name}: grad_mean={param.grad.mean():.6f}")
   ```

3. **可视化中间结果**
   ```python
   import matplotlib.pyplot as plt
   plt.hist(x.detach().numpy().flatten())
   plt.show()
   ```

## 6. 性能优化

### 6.1 训练优化

1. **使用 GPU**
   ```python
   device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
   model = model.to(device)
   ```

2. **数据加载优化**
   ```python
   DataLoader(dataset, batch_size=32, num_workers=4, pin_memory=True)
   ```

3. **混合精度训练**
   ```python
   from torch.cuda.amp import autocast, GradScaler

   scaler = GradScaler()
   with autocast():
       logits, _, _ = model(points)
       loss = criterion(logits, labels)

   scaler.scale(loss).backward()
   scaler.step(optimizer)
   scaler.update()
   ```

### 6.2 推理优化

1. **模型评估模式**
   ```python
   model.eval()
   with torch.no_grad():
       logits, _, _ = model(points)
   ```

2. **批处理**
   ```python
   # 一次处理多个点云
   batch_points = torch.stack([points1, points2, points3])
   logits, _, _ = model(batch_points)
   ```

## 7. 部署指南

### 7.1 模型导出

```python
# 保存模型
torch.save(model.state_dict(), "model.pth")

# 加载模型
model = PointNetClassifier(num_classes=10)
model.load_state_dict(torch.load("model.pth"))
model.eval()
```

### 7.2 ONNX 导出

```python
dummy_input = torch.randn(1, 3, 1024)
torch.onnx.export(
    model,
    dummy_input,
    "pointnet.onnx",
    input_names=["points"],
    output_names=["logits"],
)
```

## 8. 贡献指南

### 8.1 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型:
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 其他

### 8.2 Pull Request

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 9. 常见问题

### Q1: Open3D 安装失败

```bash
# 尝试使用 conda
conda install -c open3d-admin open3d

# 或使用预编译版本
pip install open3d --no-cache-dir
```

### Q2: CUDA 版本不匹配

```bash
# 检查 CUDA 版本
nvcc --version

# 安装对应版本的 PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### Q3: 内存溢出

- 减小批次大小
- 减少点云点数
- 使用梯度累积
- 使用混合精度训练
