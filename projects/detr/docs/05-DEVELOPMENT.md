# DETR 目标检测 - 开发文档

## 1. 开发环境搭建

### 1.1 系统要求

- **操作系统**：Linux / macOS / Windows
- **Python**：3.8 或更高版本
- **CUDA**：11.0 或更高版本（GPU 训练）

### 1.2 依赖安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 1.3 requirements.txt

```
torch>=1.10.0
torchvision>=0.11.0
numpy>=1.19.0
scipy>=1.7.0
pytest>=6.0.0
pytest-cov>=2.0.0
```

## 2. 项目结构

```
detr/
├── src/
│   ├── __init__.py          # 模块初始化
│   ├── backbone.py          # CNN骨干网络
│   ├── transformer.py       # Transformer
│   ├── matcher.py           # 匈牙利匹配
│   ├── loss.py              # 损失函数
│   ├── detr.py              # DETR主模型
│   ├── dataset.py           # 数据集
│   └── utils.py             # 工具函数
├── tests/
│   ├── __init__.py
│   ├── test_backbone.py
│   ├── test_transformer.py
│   ├── test_matcher.py
│   ├── test_loss.py
│   ├── test_detr.py
│   └── test_dataset.py
├── examples/
│   ├── train.py             # 训练示例
│   └── inference.py         # 推理示例
├── docs/
│   ├── 01-RESEARCH.md       # 研究文档
│   ├── 02-DESIGN.md         # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md        # 测试文档
│   └── 05-DEVELOPMENT.md    # 开发文档
├── README.md
├── LEARNING_NOTES.md
└── requirements.txt
```

## 3. 开发流程

### 3.1 功能开发

1. **创建分支**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **编写代码**
   - 遵循 PEP 8 编码规范
   - 添加类型注解
   - 编写文档字符串

3. **编写测试**
   - 为新功能编写单元测试
   - 确保测试覆盖率

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/new-feature
   ```

5. **创建 Pull Request**
   - 描述功能变更
   - 关联相关 Issue

### 3.2 编码规范

#### Python 代码风格

```python
# 使用 4 空格缩进
def my_function(arg1: int, arg2: str) -> bool:
    """
    函数文档字符串
    
    Args:
        arg1: 参数1描述
        arg2: 参数2描述
    
    Returns:
        返回值描述
    
    Raises:
        ValueError: 异常描述
    """
    # 实现
    return True
```

#### 命名规范

- **类名**：PascalCase（如 `TransformerEncoder`）
- **函数名**：snake_case（如 `build_backbone`）
- **变量名**：snake_case（如 `num_classes`）
- **常量**：UPPER_CASE（如 `MAX_OBJECTS`）

#### 类型注解

```python
from typing import List, Dict, Optional, Tuple

def process_data(
    images: torch.Tensor,
    targets: List[Dict[str, torch.Tensor]],
    threshold: float = 0.5
) -> Tuple[torch.Tensor, torch.Tensor]:
    pass
```

### 3.3 文档规范

#### 模块文档

```python
"""
模块名称

模块功能描述
"""
```

#### 类文档

```python
class MyClass:
    """
    类描述
    
    Attributes:
        attr1: 属性1描述
        attr2: 属性2描述
    
    Example:
        >>> obj = MyClass()
        >>> result = obj.method()
    """
```

## 4. 调试技巧

### 4.1 使用 pdb

```python
import pdb; pdb.set_trace()
```

### 4.2 日志记录

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Processing started")
logger.error("An error occurred")
```

### 4.3 性能分析

```python
import cProfile

def my_function():
    pass

cProfile.run('my_function()')
```

### 4.4 内存分析

```python
import torch

# 打印张量形状和数据类型
print(f"Tensor shape: {tensor.shape}")
print(f"Tensor dtype: {tensor.dtype}")
print(f"Tensor device: {tensor.device}")

# 检查梯度
print(f"Requires grad: {tensor.requires_grad}")
print(f"Grad fn: {tensor.grad_fn}")
```

## 5. 常见问题

### 5.1 内存不足

**问题**：`RuntimeError: CUDA out of memory`

**解决方案**：
- 减小批量大小
- 使用梯度检查点
- 减少查询数量
- 使用混合精度训练

```python
# 使用梯度检查点
from torch.utils.checkpoint import checkpoint

def forward_with_checkpoint(self, x):
    return checkpoint(self._forward, x)
```

### 5.2 损失不收敛

**问题**：训练损失不下降

**解决方案**：
- 检查学习率
- 检查数据格式
- 检查匹配质量
- 增加训练轮数

```python
# 打印匹配结果
indices = matcher(outputs, targets)
print(f"Matched predictions: {len(indices[0][0])}")

# 打印损失值
losses = criterion(outputs, targets)
for k, v in losses.items():
    print(f"{k}: {v.item():.4f}")
```

### 5.3 检测效果差

**问题**：模型检测效果不理想

**解决方案**：
- 增加数据增强
- 调整损失权重
- 使用更强的骨干网络
- 增加模型容量

## 6. 扩展开发

### 6.1 添加新的骨干网络

```python
class CustomBackbone(nn.Module):
    def __init__(self):
        super().__init__()
        # 自定义骨干网络
    
    def forward(self, x):
        # 特征提取
        return features
```

### 6.2 添加新的损失函数

```python
class CustomLoss(nn.Module):
    def __init__(self):
        super().__init__()
        # 初始化
    
    def forward(self, outputs, targets):
        # 计算损失
        return losses
```

### 6.3 添加新的匹配策略

```python
class CustomMatcher(nn.Module):
    def __init__(self):
        super().__init__()
        # 初始化
    
    def forward(self, outputs, targets):
        # 执行匹配
        return indices
```

## 7. 部署

### 7.1 模型导出

```python
# 导出为 ONNX
torch.onnx.export(
    model,
    dummy_input,
    "detr.onnx",
    export_params=True,
    opset_version=11,
    input_names=['input'],
    output_names=['output']
)
```

### 7.2 模型量化

```python
# 动态量化
quantized_model = torch.quantization.quantize_dynamic(
    model,
    {torch.nn.Linear},
    dtype=torch.qint8
)
```

### 7.3 模型优化

```python
# 使用 TorchScript
scripted_model = torch.jit.script(model)
scripted_model.save("detr_scripted.pt")
```

## 8. 贡献指南

### 8.1 代码贡献

1. Fork 项目
2. 创建功能分支
3. 编写代码和测试
4. 提交 Pull Request

### 8.2 问题反馈

1. 使用 Issue 模板
2. 提供复现步骤
3. 附上错误日志

### 8.3 文档贡献

1. 修正错别字
2. 补充示例代码
3. 翻译文档

## 9. 版本管理

### 9.1 版本号规范

使用语义化版本号：`MAJOR.MINOR.PATCH`

- **MAJOR**：不兼容的 API 变更
- **MINOR**：向后兼容的功能新增
- **PATCH**：向后兼容的问题修正

### 9.2 变更日志

```markdown
## [1.0.0] - 2024-01-01

### Added
- 初始版本发布
- 实现 DETR 模型
- 实现匈牙利匹配
- 实现集合预测损失

### Changed
- 无

### Fixed
- 无
```

## 10. 学习资源

### 10.1 官方文档

- [PyTorch 文档](https://pytorch.org/docs/)
- [torchvision 文档](https://pytorch.org/vision/stable/)

### 10.2 论文

- [End-to-End Object Detection with Transformers](https://arxiv.org/abs/2005.12872)
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)

### 10.3 教程

- [PyTorch DETR Tutorial](https://pytorch.org/tutorials/intermediate/detr_tutorial.html)
- [DETR 详解](https://github.com/facebookresearch/detr)
