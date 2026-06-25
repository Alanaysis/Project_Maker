# 超分辨率开发文档

## 1. 开发环境

### 1.1 系统要求

**操作系统**：
- Linux (推荐 Ubuntu 20.04+)
- macOS
- Windows

**Python 版本**：
- Python 3.8+

**硬件要求**：
- CPU：任意
- 内存：8GB+
- GPU（可选）：NVIDIA GPU with CUDA

### 1.2 依赖安装

**创建虚拟环境**：
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

**安装依赖**：
```bash
pip install -r requirements.txt
```

**依赖列表**：
- torch>=2.0.0
- torchvision>=0.15.0
- numpy>=1.24.0
- Pillow>=9.0.0
- matplotlib>=3.7.0
- scikit-image>=0.21.0
- tqdm>=4.65.0
- pytest>=7.3.0

### 1.3 开发工具

**推荐 IDE**：
- VS Code + Python 扩展
- PyCharm
- Vim/Neovim + LSP

**代码格式化**：
- black
- isort

**代码检查**：
- flake8
- pylint

**类型检查**：
- mypy

## 2. 项目结构

### 2.1 目录结构

```
super-resolution/
├── src/                    # 源代码
│   ├── __init__.py        # 包初始化
│   ├── models.py          # 模型实现
│   ├── dataset.py         # 数据集
│   ├── trainer.py         # 训练器
│   ├── evaluator.py       # 评估器
│   └── utils.py           # 工具函数
├── tests/                  # 测试代码
│   ├── test_models.py     # 模型测试
│   ├── test_dataset.py    # 数据集测试
│   └── test_trainer.py    # 训练器测试
├── docs/                   # 文档
│   ├── 01-RESEARCH.md     # 研究文档
│   ├── 02-REQUIREMENTS.md # 需求文档
│   ├── 03-DESIGN.md       # 设计文档
│   ├── 04-TESTING.md      # 测试文档
│   └── 05-DEVELOPMENT.md  # 开发文档
├── examples/               # 示例
│   └── demo.py            # 演示脚本
├── train.py                # 训练脚本
├── evaluate.py             # 评估脚本
├── requirements.txt        # 依赖包
├── README.md               # 项目说明
└── LEARNING_NOTES.md       # 学习笔记
```

### 2.2 模块说明

**src/models.py**：
- SRCNN 模型
- ESPCN 模型
- EDSR 模型
- PixelShuffle 模块
- 模型工厂函数

**src/dataset.py**：
- SRDataset（训练数据集）
- SRTestDataset（测试数据集）
- 数据增强函数
- 合成数据集生成

**src/trainer.py**：
- SRTrainer（训练器）
- 训练循环
- 验证
- 检查点保存/加载

**src/evaluator.py**：
- SREvaluator（评估器）
- PSNR 计算
- SSIM 计算
- 图像超分辨率

**src/utils.py**：
- 随机种子设置
- 指标计算
- 可视化工具
- 文件操作

## 3. 开发流程

### 3.1 代码风格

**PEP 8 规范**：
- 使用 4 空格缩进
- 行长度限制 79 字符
- 使用空行分隔函数和类
- 使用小写字母和下划线命名

**类型注解**：
```python
def train(
    self,
    train_dir: str,
    val_dir: Optional[str] = None,
    epochs: int = 100,
    batch_size: int = 16
) -> Dict:
    """训练模型"""
    pass
```

**文档字符串**：
```python
def calculate_psnr(
    sr_image: torch.Tensor,
    hr_image: torch.Tensor,
    max_pixel: float = 1.0
) -> float:
    """
    计算 PSNR（峰值信噪比）

    Args:
        sr_image (torch.Tensor): 超分辨率图像
        hr_image (torch.Tensor): 高分辨率图像
        max_pixel (float): 最大像素值

    Returns:
        float: PSNR 值
    """
    pass
```

### 3.2 版本控制

**Git 工作流**：
1. 创建功能分支
2. 开发功能
3. 编写测试
4. 提交代码
5. 创建 Pull Request
6. 代码审查
7. 合并到主分支

**提交信息格式**：
```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

### 3.3 测试驱动开发

**流程**：
1. 编写测试
2. 运行测试（失败）
3. 编写代码
4. 运行测试（通过）
5. 重构代码
6. 运行测试（通过）

**示例**：
```python
# 1. 编写测试
def test_srcnn_forward():
    model = SRCNN()
    x = torch.randn(1, 3, 32, 32)
    output = model(x)
    assert output.shape == (1, 3, 32, 32)

# 2. 运行测试（失败）
# pytest tests/test_models.py::test_srcnn_forward

# 3. 编写代码
class SRCNN(nn.Module):
    def forward(self, x):
        # 实现前向传播
        pass

# 4. 运行测试（通过）
# pytest tests/test_models.py::test_srcnn_forward
```

## 4. 开发任务

### 4.1 模型开发

**任务 1：实现 SRCNN**

步骤：
1. 定义模型类
2. 实现特征提取层
3. 实现非线性映射层
4. 实现重建层
5. 编写测试
6. 验证功能

**任务 2：实现 ESPCN**

步骤：
1. 定义模型类
2. 实现特征提取层
3. 实现特征映射层
4. 实现亚像素卷积层
5. 实现 PixelShuffle
6. 编写测试
7. 验证功能

**任务 3：实现 EDSR**

步骤：
1. 定义残差块
2. 定义模型类
3. 实现浅层特征提取
4. 实现深层特征提取
5. 实现上采样模块
6. 实现重建层
7. 编写测试
8. 验证功能

### 4.2 数据集开发

**任务 1：实现 SRDataset**

步骤：
1. 定义数据集类
2. 实现图像加载
3. 实现随机裁剪
4. 实现数据增强
5. 实现降采样
6. 编写测试
7. 验证功能

**任务 2：实现 SRTestDataset**

步骤：
1. 定义数据集类
2. 实现图像加载
3. 实现尺寸调整
4. 实现降采样
5. 编写测试
6. 验证功能

### 4.3 训练器开发

**任务 1：实现 SRTrainer**

步骤：
1. 定义训练器类
2. 实现模型初始化
3. 实现数据加载
4. 实现训练循环
5. 实现验证
6. 实现检查点保存/加载
7. 编写测试
8. 验证功能

### 4.4 评估器开发

**任务 1：实现 SREvaluator**

步骤：
1. 定义评估器类
2. 实现模型加载
3. 实现 PSNR 计算
4. 实现 SSIM 计算
5. 实现图像超分辨率
6. 编写测试
7. 验证功能

### 4.5 脚本开发

**任务 1：实现训练脚本**

步骤：
1. 解析命令行参数
2. 创建训练器
3. 训练模型
4. 保存结果

**任务 2：实现评估脚本**

步骤：
1. 解析命令行参数
2. 创建评估器
3. 加载检查点
4. 评估模型
5. 保存结果

**任务 3：实现演示脚本**

步骤：
1. 演示模型创建
2. 演示前向传播
3. 演示图像超分辨率
4. 演示模型对比

## 5. 调试技巧

### 5.1 模型调试

**检查模型参数**：
```python
model = SRCNN()
print(model)
print(f"Total parameters: {sum(p.numel() for p in model.parameters()):,}")
```

**检查前向传播**：
```python
x = torch.randn(1, 3, 32, 32)
output = model(x)
print(f"Input shape: {x.shape}")
print(f"Output shape: {output.shape}")
```

**检查梯度流动**：
```python
x = torch.randn(1, 3, 32, 32, requires_grad=True)
output = model(x)
loss = output.mean()
loss.backward()
print(f"Input gradient: {x.grad is not None}")
for name, param in model.named_parameters():
    print(f"{name} gradient: {param.grad is not None}")
```

### 5.2 数据调试

**检查数据集**：
```python
dataset = SRDataset(hr_dir='data/train', scale_factor=2)
print(f"Dataset size: {len(dataset)}")

lr, hr = dataset[0]
print(f"LR shape: {lr.shape}")
print(f"HR shape: {hr.shape}")
```

**可视化数据**：
```python
import matplotlib.pyplot as plt

lr, hr = dataset[0]
fig, axes = plt.subplots(1, 2)
axes[0].imshow(lr.permute(1, 2, 0).numpy())
axes[0].set_title('Low Resolution')
axes[1].imshow(hr.permute(1, 2, 0).numpy())
axes[1].set_title('High Resolution')
plt.show()
```

### 5.3 训练调试

**检查训练过程**：
```python
trainer = SRTrainer(model_name='srcnn')
history = trainer.train(train_dir='data/train', epochs=10)

# 绘制损失曲线
plt.plot(history['train_loss'])
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training Loss')
plt.show()
```

**检查梯度**：
```python
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad_mean={param.grad.mean():.6f}, grad_std={param.grad.std():.6f}")
```

## 6. 常见问题

### 6.1 模型不收敛

**可能原因**：
- 学习率过大或过小
- 数据预处理不当
- 模型架构问题

**解决方法**：
- 调整学习率
- 检查数据预处理
- 简化模型架构

### 6.2 内存不足

**可能原因**：
- 批次大小过大
- 图像尺寸过大
- 模型过大

**解决方法**：
- 减小批次大小
- 减小图像尺寸
- 使用梯度累积

### 6.3 训练速度慢

**可能原因**：
- 数据加载瓶颈
- 模型计算复杂
- GPU 利用率低

**解决方法**：
- 使用多线程数据加载
- 优化模型架构
- 使用混合精度训练

### 6.4 测试失败

**可能原因**：
- 代码逻辑错误
- 测试数据问题
- 环境问题

**解决方法**：
- 检查代码逻辑
- 检查测试数据
- 检查环境配置

## 7. 最佳实践

### 7.1 代码组织

- 模块化设计
- 单一职责原则
- 依赖注入

### 7.2 错误处理

- 使用异常处理
- 提供清晰的错误消息
- 记录错误日志

### 7.3 性能优化

- 使用向量化操作
- 避免不必要的循环
- 使用缓存

### 7.4 文档编写

- 编写清晰的文档
- 提供使用示例
- 更新文档

## 8. 发布流程

### 8.1 版本管理

**版本号格式**：`MAJOR.MINOR.PATCH`

- MAJOR：不兼容的 API 变更
- MINOR：向后兼容的功能添加
- PATCH：向后兼容的 bug 修复

### 8.2 发布检查

**检查列表**：
- [ ] 所有测试通过
- [ ] 代码覆盖率达标
- [ ] 文档更新
- [ ] 版本号更新
- [ ] 更新日志更新

### 8.3 发布步骤

1. 更新版本号
2. 更新更新日志
3. 运行测试
4. 构建包
5. 发布到 PyPI（可选）
6. 创建 Git 标签
7. 推送到远程仓库

## 9. 贡献指南

### 9.1 如何贡献

1. Fork 项目
2. 创建功能分支
3. 开发功能
4. 编写测试
5. 提交代码
6. 创建 Pull Request

### 9.2 代码审查

**审查要点**：
- 代码风格
- 测试覆盖
- 文档完整
- 性能影响

### 9.3 问题报告

**报告内容**：
- 问题描述
- 复现步骤
- 期望行为
- 实际行为
- 环境信息

## 10. 资源链接

### 10.1 官方文档

- [PyTorch 文档](https://pytorch.org/docs/)
- [torchvision 文档](https://pytorch.org/vision/stable/)
- [NumPy 文档](https://numpy.org/doc/)

### 10.2 学习资源

- [PyTorch 教程](https://pytorch.org/tutorials/)
- [深度学习课程](https://www.deeplearning.ai/)
- [论文阅读](https://arxiv.org/)

### 10.3 工具

- [GitHub](https://github.com/)
- [VS Code](https://code.visualstudio.com/)
- [PyCharm](https://www.jetbrains.com/pycharm/)
