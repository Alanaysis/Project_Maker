# 05 - 开发文档

## 开发环境设置

### 1. 系统要求

- **操作系统**: Ubuntu 20.04 / 22.04
- **Python**: 3.8+
- **CUDA**: 11.0+ (如果使用 GPU)
- **GPU**: NVIDIA GPU (推荐 RTX 3060 或更高)

### 2. 依赖安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装 PyTorch (GPU 版本)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 安装 Open3D
pip install open3d

# 安装开发依赖
pip install pytest pytest-cov black flake8 mypy
```

### 3. 代码风格

#### Python 代码风格

- 遵循 PEP 8 规范
- 使用 Black 进行代码格式化
- 使用 Flake8 进行代码检查
- 使用 MyPy 进行类型检查

```bash
# 格式化代码
black src/ tests/

# 检查代码风格
flake8 src/ tests/

# 类型检查
mypy src/
```

#### 代码规范示例

```python
# 好的代码风格
def compute_iou(box1: np.ndarray, box2: np.ndarray) -> float:
    """
    计算两个边界框的 IoU (Intersection over Union).
    
    Args:
        box1: 第一个边界框 [x1, y1, x2, y2]
        box2: 第二个边界框 [x1, y1, x2, y2]
    
    Returns:
        IoU 值，范围 [0, 1]
    
    Raises:
        ValueError: 如果边界框格式不正确
    """
    if box1.shape != (4,) or box2.shape != (4,):
        raise ValueError("边界框必须是 4 维数组")
    
    # 计算交集区域
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    
    # 计算并集区域
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection
    
    # 计算 IoU
    iou = intersection / union if union > 0 else 0.0
    
    return iou
```

## 项目结构

```
adas-perception/
├── README.md
├── requirements.txt
├── setup.py
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── LEARNING_NOTES.md
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── kitti_loader.py
│   │   └── point_cloud.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── pointpillars.py
│   │   └── backbone.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── visualization.py
│   │   └── transforms.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_point_cloud.py
│   ├── test_model.py
│   └── test_visualization.py
├── configs/
│   └── pointpillars_kitti.yaml
├── examples/
│   └── demo.py
└── scripts/
    ├── train.py
    ├── evaluate.py
    └── visualize.py
```

## 开发流程

### 1. Git 工作流

```
main (主分支)
├── develop (开发分支)
│   ├── feature/point-cloud-processing
│   ├── feature/pointpillars-model
│   ├── feature/visualization
│   └── feature/data-augmentation
├── release/v1.0.0
└── hotfix/bug-fix
```

#### 分支命名规范

- `feature/xxx`: 新功能开发
- `bugfix/xxx`: Bug 修复
- `hotfix/xxx`: 紧急修复
- `release/xxx`: 版本发布

#### 提交信息规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type)**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```
feat(point-cloud): 添加点云降采样功能

- 实现体素降采样算法
- 添加降采样测试用例
- 更新文档

Closes #123
```

### 2. 代码审查流程

1. 创建功能分支
2. 完成开发并提交
3. 创建 Pull Request
4. 代码审查
5. 合并到 develop 分支

### 3. 版本发布流程

1. 从 develop 创建 release 分支
2. 进行最后的测试和修复
3. 合并到 main 分支
4. 打标签 (tag)
5. 发布版本

## 开发工具

### 1. IDE 配置

#### VS Code 配置

```json
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "88"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### PyCharm 配置

1. 安装 Python 插件
2. 配置代码风格 (PEP 8)
3. 配置 Black 格式化
4. 配置 Flake8 检查

### 2. 调试工具

#### PyTorch 调试

```python
# 启用异常检测
torch.autograd.set_detect_anomaly(True)

# 打印梯度
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad norm = {param.grad.norm()}")

# 检查 NaN
if torch.isnan(loss):
    print("Loss is NaN!")
    break
```

#### 内存调试

```python
# 打印内存使用
import torch
print(f"Allocated: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
print(f"Cached: {torch.cuda.memory_reserved() / 1024**2:.2f} MB")

# 清空缓存
torch.cuda.empty_cache()
```

### 3. 性能分析

#### PyTorch Profiler

```python
from torch.profiler import profile, record_function, ProfilerActivity

with profile(
    activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
    record_shapes=True,
    profile_memory=True,
    with_stack=True
) as prof:
    with record_function("model_inference"):
        model(input)

print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=10))
```

#### cProfile

```python
import cProfile

def main():
    # 你的代码
    pass

cProfile.run('main()', sort='cumulative')
```

## 常见问题解决

### 1. CUDA 内存不足

**问题**: `RuntimeError: CUDA out of memory`

**解决方案**:
```python
# 1. 减小批量大小
batch_size = 8  # 而不是 32

# 2. 使用梯度累积
accumulation_steps = 4

# 3. 使用混合精度训练
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()

with autocast():
    output = model(input)
    loss = criterion(output, target)

scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()

# 4. 清空缓存
torch.cuda.empty_cache()
```

### 2. 训练 loss 不下降

**问题**: 训练过程中 loss 不下降

**解决方案**:
```python
# 1. 检查学习率
print(f"Learning rate: {optimizer.param_groups[0]['lr']}")

# 2. 检查梯度
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad norm = {param.grad.norm()}")

# 3. 检查数据
print(f"Input shape: {input.shape}")
print(f"Target shape: {target.shape}")
print(f"Input range: [{input.min()}, {input.max()}]")

# 4. 使用梯度裁剪
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
```

### 3. 模型收敛慢

**问题**: 模型需要很长时间才能收敛

**解决方案**:
```python
# 1. 使用学习率调度器
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
    optimizer, T_max=100, eta_min=1e-6
)

# 2. 使用预训练模型
model.load_pretrained('pretrained.pth')

# 3. 使用数据增强
transform = transforms.Compose([
    transforms.RandomFlip(),
    transforms.RandomRotation(),
    transforms.RandomScaling()
])

# 4. 调整损失函数权重
class_weights = torch.tensor([1.0, 2.0, 3.0])
criterion = nn.CrossEntropyLoss(weight=class_weights)
```

### 4. 推理速度慢

**问题**: 模型推理速度太慢

**解决方案**:
```python
# 1. 使用 TensorRT 加速
import torch_tensorrt

trt_model = torch_tensorrt.compile(
    model,
    inputs=[torch_tensorrt.Input((1, 1000, 4))],
    enabled_precisions={torch.float16}
)

# 2. 使用 ONNX Runtime
import onnxruntime as ort

session = ort.InferenceSession("model.onnx")
output = session.run(None, {"input": input.numpy()})

# 3. 模型量化
quantized_model = torch.quantization.quantize_dynamic(
    model, {torch.nn.Linear}, dtype=torch.qint8
)

# 4. 模型剪枝
import torch.nn.utils.prune as prune

for name, module in model.named_modules():
    if isinstance(module, torch.nn.Linear):
        prune.l1_unstructured(module, name='weight', amount=0.3)
```

## 部署指南

### 1. 模型导出

```python
# 导出为 ONNX
dummy_input = torch.randn(1, 1000, 4)
torch.onnx.export(
    model,
    dummy_input,
    "model.onnx",
    export_params=True,
    opset_version=11,
    do_constant_folding=True,
    input_names=['input'],
    output_names=['output'],
    dynamic_axes={
        'input': {0: 'batch_size'},
        'output': {0: 'batch_size'}
    }
)
```

### 2. Docker 部署

```dockerfile
FROM pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "src/main.py"]
```

### 3. 边缘设备部署

```python
# 使用 TensorRT 优化
import tensorrt as trt

# 构建 TensorRT 引擎
logger = trt.Logger(trt.Logger.WARNING)
builder = trt.Builder(logger)
network = builder.create_network(
    1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
)
parser = trt.OnnxParser(network, logger)

with open("model.onnx", "rb") as f:
    parser.parse(f.read())

config = builder.create_builder_config()
config.max_workspace_size = 1 << 30  # 1GB
engine = builder.build_engine(network, config)
```

## 文档编写规范

### 1. 代码文档

```python
def function_name(param1: int, param2: str) -> bool:
    """
    函数功能简述.
    
    详细描述函数的功能、算法和注意事项。
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述
    
    Returns:
        返回值的描述
    
    Raises:
        ValueError: 异常情况的描述
    
    Example:
        >>> result = function_name(1, "test")
        >>> print(result)
        True
    """
    pass
```

### 2. README 文档

- 项目简介
- 安装说明
- 使用方法
- API 文档
- 示例代码
- 贡献指南
- 许可证

### 3. 变更日志

```markdown
# Changelog

## [1.0.0] - 2024-01-01

### Added
- 新增点云处理模块
- 新增 PointPillars 模型
- 新增可视化工具

### Changed
- 优化数据加载速度
- 改进模型性能

### Fixed
- 修复内存泄漏问题
- 修复边界框计算错误
```

## 协作开发

### 1. 代码审查清单

- [ ] 代码风格符合规范
- [ ] 添加了必要的注释
- [ ] 编写了单元测试
- [ ] 测试通过
- [ ] 文档已更新
- [ ] 没有引入新的依赖 (或已说明原因)
- [ ] 性能没有明显下降

### 2. Pull Request 模板

```markdown
## 描述

简要描述这个 PR 的目的。

## 改动

- 改动1
- 改动2
- 改动3

## 测试

- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 性能测试通过

## 截图 (如果适用)

## 相关 Issue

Closes #123
```

## 参考资源

1. PEP 8 代码风格指南: https://peps.python.org/pep-0008/
2. Git 工作流: https://www.atlassian.com/git/tutorials/comparing-workflows
3. PyTorch 最佳实践: https://pytorch.org/docs/stable/notes/faq.html
4. Docker 最佳实践: https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
