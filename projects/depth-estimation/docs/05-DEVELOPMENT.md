# 开发指南 - 深度估计

## 1. 开发环境

### 1.1 依赖安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install torch torchvision numpy opencv-python matplotlib pytest
```

### 1.2 IDE 配置

推荐使用 VS Code + Python 扩展：

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"]
}
```

## 2. 项目结构

```
depth-estimation/
├── src/
│   ├── __init__.py      # 包初始化
│   ├── model.py         # 模型架构
│   ├── loss.py          # 损失函数
│   ├── dataset.py       # 数据集
│   ├── train.py         # 训练脚本
│   └── utils.py         # 工具函数
├── tests/
│   ├── __init__.py
│   ├── test_model.py
│   ├── test_loss.py
│   ├── test_dataset.py
│   └── test_utils.py
├── examples/
│   └── demo.py
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── README.md
├── LEARNING_NOTES.md
└── requirements.txt
```

## 3. 编码规范

### 3.1 Python 风格

- 遵循 PEP 8
- 使用类型注解
- 编写文档字符串

```python
def compute_depth_metrics(
    pred: torch.Tensor,
    target: torch.Tensor,
    valid_mask: Optional[torch.Tensor] = None,
) -> Dict[str, float]:
    """
    计算深度估计评估指标

    Args:
        pred: 预测深度图 (B, 1, H, W)
        target: 目标深度图 (B, 1, H, W)
        valid_mask: 有效像素掩码 (B, 1, H, W)

    Returns:
        指标字典
    """
    # 实现...
```

### 3.2 命名规范

- 类名: PascalCase
- 函数名: snake_case
- 变量名: snake_case
- 常量名: UPPER_CASE

### 3.3 文档规范

- 每个模块有模块级文档
- 每个类有类级文档
- 每个函数有函数级文档
- 复杂逻辑有注释

## 4. 开发流程

### 4.1 新功能开发

1. 创建功能分支
2. 编写代码
3. 编写测试
4. 运行测试
5. 提交代码
6. 创建 PR

### 4.2 测试驱动开发

1. 编写测试用例
2. 运行测试（失败）
3. 编写实现代码
4. 运行测试（通过）
5. 重构代码
6. 运行测试（通过）

### 4.3 代码审查

- 检查代码风格
- 检查测试覆盖
- 检查文档完整性
- 检查性能影响

## 5. 调试技巧

### 5.1 模型调试

```python
# 检查模型输出
model.eval()
with torch.no_grad():
    output = model(input_tensor)
    print(f"Output shape: {output.shape}")
    print(f"Output range: [{output.min():.4f}, {output.max():.4f}]")
    print(f"Output mean: {output.mean():.4f}")
```

### 5.2 梯度检查

```python
# 检查梯度流
loss.backward()
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad_mean={param.grad.mean():.6f}, grad_std={param.grad.std():.6f}")
    else:
        print(f"{name}: no gradient!")
```

### 5.3 损失调试

```python
# 打印各项损失
loss_dict = criterion(pred, target, mask)
for key, value in loss_dict.items():
    print(f"{key}: {value.item():.4f}")
```

### 5.4 数据调试

```python
# 可视化数据
for images, depths, masks in dataloader:
    print(f"Images: {images.shape}, {images.min():.4f}, {images.max():.4f}")
    print(f"Depths: {depths.shape}, {depths.min():.4f}, {depths.max():.4f}")
    print(f"Masks: {masks.shape}, {masks.sum()}")
    break
```

## 6. 性能优化

### 6.1 训练优化

```python
# 混合精度训练
scaler = torch.cuda.amp.GradScaler()
with torch.cuda.amp.autocast():
    output = model(input)
    loss = criterion(output, target)
scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

### 6.2 内存优化

```python
# 梯度累积
accumulation_steps = 4
for i, (images, depths, masks) in enumerate(dataloader):
    pred = model(images)
    loss = criterion(pred, depths, masks)
    loss = loss / accumulation_steps
    loss.backward()

    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

### 6.3 推理优化

```python
# 模型量化
quantized_model = torch.quantization.quantize_dynamic(
    model,
    {torch.nn.Linear, torch.nn.Conv2d},
    dtype=torch.qint8
)
```

## 7. 常见问题

### 7.1 CUDA 内存不足

**解决方案**:
- 减小批量大小
- 使用梯度累积
- 使用混合精度训练
- 清理不需要的张量

### 7.2 训练不收敛

**解决方案**:
- 检查学习率
- 检查损失函数
- 检查数据预处理
- 使用学习率调度

### 7.3 过拟合

**解决方案**:
- 增加数据增强
- 使用正则化（Dropout, Weight Decay）
- 减小模型容量
- 使用早停

### 7.4 欠拟合

**解决方案**:
- 增加模型容量
- 增加训练时间
- 调整学习率
- 检查数据质量

## 8. 扩展开发

### 8.1 添加新模型

```python
class NewDepthNet(nn.Module):
    def __init__(self, in_channels=3, base_channels=64):
        super().__init__()
        # 定义网络结构

    def forward(self, x):
        # 前向传播
        return depth
```

### 8.2 添加新损失函数

```python
class NewDepthLoss(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, pred, target, valid_mask=None):
        # 计算损失
        return loss
```

### 8.3 添加新数据集

```python
class NewDepthDataset(Dataset):
    def __init__(self, root, transform=None):
        super().__init__()
        # 初始化数据集

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # 返回 (image, depth, mask)
        return image, depth, mask
```

## 9. 发布流程

### 9.1 版本管理

```bash
# 更新版本号
# src/__init__.py
__version__ = "1.1.0"

# 提交
git add .
git commit -m "release: v1.1.0"
git tag v1.1.0
git push origin v1.1.0
```

### 9.2 文档更新

- 更新 README.md
- 更新 LEARNING_NOTES.md
- 更新 docs/ 文件

### 9.3 测试验证

```bash
# 运行所有测试
pytest tests/ -v

# 运行演示
python examples/demo.py

# 检查代码风格
flake8 src/ tests/
```

## 10. 最佳实践

### 10.1 代码质量

- 编写清晰的文档
- 保持函数简洁
- 遵循单一职责原则
- 使用有意义的命名

### 10.2 测试质量

- 测试覆盖核心功能
- 测试边界条件
- 测试异常情况
- 保持测试简洁

### 10.3 性能考虑

- 使用向量化操作
- 避免不必要的循环
- 合理使用 GPU
- 监控内存使用

### 10.4 可维护性

- 模块化设计
- 清晰的接口
- 完整的文档
- 良好的测试覆盖
