# 开发手册

> Industrial Vision Detection - Development Guide

## 1. 环境搭建

### 1.1 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Linux/macOS/Windows | Ubuntu 20.04+ |
| Python | 3.8 | 3.10 |
| 内存 | 8GB | 16GB+ |
| GPU | 无 (CPU 可运行) | NVIDIA GPU 8GB+ |
| CUDA | 无 | 11.8+ |
| 磁盘空间 | 2GB | 10GB+ |

### 1.2 Python 环境

#### 方式一：venv (推荐)

```bash
# 创建虚拟环境
python -m venv venv

# 激活环境
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

# 升级 pip
pip install --upgrade pip
```

#### 方式二：Conda

```bash
# 创建环境
conda create -n industrial-vision python=3.10

# 激活环境
conda activate industrial-vision
```

### 1.3 依赖安装

```bash
# 安装项目依赖
pip install -r requirements.txt

# 或者开发模式安装
pip install -e .
```

### 1.4 依赖说明

```
requirements.txt:

# 核心依赖
torch>=2.0.0          # PyTorch 深度学习框架
torchvision>=0.15.0   # 视觉工具库

# 数据处理
numpy>=1.24.0         # 数值计算
opencv-python>=4.8.0  # 图像处理
Pillow>=10.0.0        # 图像处理

# 配置管理
pyyaml>=6.0           # YAML 解析

# 可视化
matplotlib>=3.7.0     # 绘图库

# ONNX 部署 (可选)
onnx>=1.14.0          # ONNX 格式支持
onnxruntime>=1.15.0   # ONNX 推理引擎

# 开发工具 (可选)
pytest>=7.4.0         # 测试框架
black>=23.0.0         # 代码格式化
flake8>=6.0.0         # 代码检查
```

### 1.5 GPU 环境配置 (可选)

```bash
# 检查 CUDA 是否可用
python -c "import torch; print(torch.cuda.is_available())"

# 安装 CUDA 版本的 PyTorch
# 访问 https://pytorch.org/get-started/locally/
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## 2. 项目结构详解

### 2.1 目录结构

```
industrial-vision-detection/
│
├── README.md                    # 项目说明文档
├── LEARNING_NOTES.md            # 学习笔记模板
├── requirements.txt             # 依赖列表
├── setup.py                     # 安装配置
├── .gitignore                   # Git 忽略文件
│
├── docs/                        # 文档目录
│   ├── 01-RESEARCH.md           # 市场调研报告
│   ├── 02-REQUIREMENTS.md       # 需求分析文档
│   ├── 03-DESIGN.md             # 技术设计文档
│   ├── 04-PRODUCT.md            # 产品思维文档
│   └── 05-DEVELOPMENT.md        # 开发手册 (本文档)
│
├── src/                         # 源代码目录
│   ├── __init__.py              # 包初始化
│   │
│   ├── models/                  # 模型定义
│   │   ├── __init__.py
│   │   ├── backbone.py          # 骨干网络
│   │   ├── neck.py              # 特征融合网络
│   │   ├── head.py              # 检测头
│   │   ├── yolo.py              # YOLO 完整模型
│   │   └── losses.py            # 损失函数
│   │
│   ├── data/                    # 数据处理
│   │   ├── __init__.py
│   │   ├── dataset.py           # 数据集类
│   │   ├── transforms.py        # 数据变换
│   │   ├── augmentations.py     # 高级数据增强
│   │   └── utils.py             # 数据工具函数
│   │
│   ├── utils/                   # 工具函数
│   │   ├── __init__.py
│   │   ├── metrics.py           # 评估指标
│   │   ├── visualization.py     # 可视化工具
│   │   ├── boxes.py             # 边界框操作
│   │   └── general.py           # 通用工具
│   │
│   └── deployment/              # 部署相关
│       ├── __init__.py
│       ├── onnx_export.py       # ONNX 导出
│       └── onnx_inference.py    # ONNX 推理
│
├── configs/                     # 配置文件
│   ├── default.yaml             # 默认配置
│   └── yolov8_tiny.yaml         # YOLOv8-tiny 配置
│
├── tests/                       # 单元测试
│   ├── __init__.py
│   ├── test_models.py           # 模型测试
│   ├── test_data.py             # 数据处理测试
│   ├── test_losses.py           # 损失函数测试
│   └── test_utils.py            # 工具函数测试
│
├── examples/                    # 使用示例
│   ├── train_example.py         # 训练示例
│   ├── inference_example.py     # 推理示例
│   └── export_example.py        # 导出示例
│
└── scripts/                     # 脚本工具
    ├── train.py                 # 训练脚本
    ├── evaluate.py              # 评估脚本
    └── export.py                # 导出脚本
```

### 2.2 模块职责

| 模块 | 职责 | 主要文件 |
|------|------|----------|
| models | 定义神经网络模型 | backbone.py, neck.py, head.py |
| data | 数据加载和处理 | dataset.py, transforms.py |
| utils | 通用工具函数 | metrics.py, boxes.py |
| deployment | 模型部署工具 | onnx_export.py |
| configs | 配置管理 | YAML 配置文件 |
| tests | 单元测试 | test_*.py |
| examples | 使用示例 | *_example.py |

## 3. 核心模块解析

### 3.1 模型模块 (models/)

#### 3.1.1 backbone.py - 骨干网络

**作用**: 提取图像的多尺度特征

**核心类**:
- `ConvBlock`: 基础卷积块 (Conv + BN + Activation)
- `CSPBlock`: Cross Stage Partial 块
- `SPPF`: 空间金字塔池化
- `CSPDarknet`: 完整骨干网络

**关键代码**:
```python
class ConvBlock(nn.Module):
    """基础卷积块: Conv + BatchNorm + Activation"""

    def __init__(self, in_channels, out_channels, kernel_size=1, stride=1):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size,
                             stride, kernel_size//2, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)
        self.act = nn.SiLU(inplace=True)

    def forward(self, x):
        return self.act(self.bn(self.conv(x)))
```

**⭐ 重点理解**:
- CSP 结构如何减少计算量
- SPPF 如何增强感受野
- 多尺度特征图的生成

#### 3.1.2 neck.py - 特征融合

**作用**: 融合不同尺度的特征，增强多尺度检测能力

**核心类**:
- `C2f`: CSP Bottleneck with 2 convolutions
- `PANet`: 路径聚合网络

**关键设计**:
```
FPN (自顶向下): 高层语义信息 → 低层
PAN (自底向上): 低层细节信息 → 高层
```

**⭐ 重点理解**:
- FPN 如何传递语义信息
- PAN 如何传递位置信息
- 特征融合的 concat 和 add 操作

#### 3.1.3 head.py - 检测头

**作用**: 从特征图生成检测结果

**核心类**:
- `DetectHead`: 解耦检测头

**输出格式**:
```
分类分支: [B, num_classes, H, W]
回归分支: [B, 4 * reg_max, H, W]
目标性分支: [B, 1, H, W]
```

**⭐ 重点理解**:
- 解耦头的优势
- Anchor-free 的预测方式
- DFL (Distribution Focal Loss) 的作用

#### 3.1.4 yolo.py - 完整模型

**作用**: 组装完整的 YOLO 模型

**核心类**:
- `YOLOModel`: 完整 YOLO 模型
- `YOLOv8Tiny`: YOLOv8-tiny 配置

**关键功能**:
```python
class YOLOModel(nn.Module):
    def forward(self, images, targets=None):
        # 训练模式
        if targets is not None:
            return self.compute_loss(predictions, targets)

        # 推理模式
        return self.postprocess(predictions)
```

#### 3.1.5 losses.py - 损失函数

**作用**: 计算训练损失

**核心损失**:
- `BCELoss`: 二元交叉熵损失
- `FocalLoss`: 焦点损失
- `CIoULoss`: 完整 IoU 损失

**⭐ 重点理解**:
- Focal Loss 如何解决样本不平衡
- CIoU Loss 的数学原理
- 多任务损失的组合方式

### 3.2 数据模块 (data/)

#### 3.2.1 dataset.py - 数据集类

**作用**: 加载和管理训练数据

**核心类**:
- `DefectDataset`: 工业缺陷数据集

**支持格式**:
- COCO 格式
- YOLO 格式
- VOC 格式

**关键功能**:
```python
class DefectDataset(Dataset):
    def __getitem__(self, index):
        # 1. 加载图像
        image = self.load_image(index)

        # 2. 加载标注
        target = self.load_target(index)

        # 3. 数据变换
        if self.transforms:
            image, target = self.transforms(image, target)

        return image, target
```

#### 3.2.2 transforms.py - 数据变换

**作用**: 图像和标注的同步变换

**基础变换**:
- `Resize`: 缩放
- `RandomFlip`: 随机翻转
- `RandomRotate`: 随机旋转
- `Normalize`: 归一化

**关键点**: 边界框需要同步变换

```python
def random_flip(image, target, prob=0.5):
    """随机水平翻转"""
    if random.random() < prob:
        image = torch.flip(image, [-1])
        # 翻转边界框
        target['boxes'][:, [0, 2]] = 1 - target['boxes'][:, [2, 0]]
    return image, target
```

#### 3.2.3 augmentations.py - 高级增强

**作用**: 实现高级数据增强策略

**核心增强**:
- `Mosaic`: 马赛克增强
- `MixUp`: 混合增强

**⭐ 重点理解**:
- Mosaic 如何增加上下文信息
- MixUp 如何提升泛化能力

### 3.3 工具模块 (utils/)

#### 3.3.1 boxes.py - 边界框操作

**作用**: 边界框相关的计算

**核心函数**:
```python
def box_iou(box1, box2):
    """计算 IoU (Intersection over Union)"""

def box_nms(boxes, scores, iou_threshold):
    """非极大值抑制"""

def xywh_to_xyxy(boxes):
    """格式转换: (x, y, w, h) → (x1, y1, x2, y2)"""
```

#### 3.3.2 metrics.py - 评估指标

**作用**: 计算检测评估指标

**核心指标**:
- `compute_iou`: 计算 IoU
- `compute_ap`: 计算 Average Precision
- `compute_map`: 计算 mean Average Precision

**⭐ 重点理解**:
- AP 的计算方法 (11-point / 101-point)
- mAP 如何综合评估模型

#### 3.3.3 visualization.py - 可视化

**作用**: 可视化检测结果

**核心功能**:
```python
def plot_detections(image, detections, save_path=None):
    """绘制检测结果"""

def plot_training_curves(history, save_path=None):
    """绘制训练曲线"""
```

### 3.4 部署模块 (deployment/)

#### 3.4.1 onnx_export.py - ONNX 导出

**作用**: 将 PyTorch 模型导出为 ONNX 格式

**核心功能**:
```python
def export_to_onnx(model, output_path, input_shape, opset_version=11):
    """导出 ONNX 模型"""

def validate_onnx(onnx_path, pytorch_model, test_input):
    """验证 ONNX 模型"""
```

#### 3.4.2 onnx_inference.py - ONNX 推理

**作用**: 使用 ONNX Runtime 进行推理

**核心功能**:
```python
class ONNXDetector:
    def __init__(self, onnx_path):
        """加载 ONNX 模型"""

    def predict(self, image):
        """执行推理"""
```

## 4. 开发流程

### 4.1 代码风格

```python
# 使用 Black 格式化
black src/ tests/ examples/

# 使用 Flake8 检查
flake8 src/ tests/ examples/

# 类型提示
def compute_iou(box1: Tensor, box2: Tensor) -> Tensor:
    """计算 IoU"""
    pass
```

### 4.2 提交规范

```
feat: 新功能
fix: 修复 Bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建/工具相关
```

示例:
```bash
git commit -m "feat: 实现 YOLOv8-tiny 模型"
git commit -m "fix: 修复 NMS 边界框越界问题"
git commit -m "docs: 更新 API 文档"
```

### 4.3 测试流程

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_models.py

# 生成覆盖率报告
pytest --cov=src tests/
```

### 4.4 调试技巧

```python
# 1. 使用 pdb 调试
import pdb; pdb.set_trace()

# 2. 打印张量形状
print(f"Tensor shape: {x.shape}, dtype: {x.dtype}")

# 3. 检查梯度
print(f"Requires grad: {x.requires_grad}")
print(f"Grad: {x.grad}")

# 4. 可视化中间结果
import matplotlib.pyplot as plt
plt.imshow(feature_map[0].detach().cpu())
plt.show()
```

## 5. 常见问题

### 5.1 环境问题

**Q: CUDA 不可用?**
```bash
# 检查 CUDA
python -c "import torch; print(torch.cuda.is_available())"

# 解决方案
# 1. 安装正确版本的 PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cu118

# 2. 检查 NVIDIA 驱动
nvidia-smi
```

**Q: 内存不足?**
```python
# 减小 batch_size
config.batch_size = 8

# 使用梯度累积
optimizer.step()
optimizer.zero_grad()

# 使用混合精度训练
from torch.cuda.amp import autocast, GradScaler
```

### 5.2 训练问题

**Q: 损失不下降?**
```
可能原因:
1. 学习率过大/过小
2. 数据标注错误
3. 模型结构问题
4. 数据预处理错误

解决方案:
1. 调整学习率
2. 检查数据
3. 简化模型
4. 可视化数据
```

**Q: 过拟合?**
```
解决方案:
1. 增加数据增强
2. 使用正则化 (Dropout, Weight Decay)
3. 减小模型复杂度
4. 早停 (Early Stopping)
```

### 5.3 推理问题

**Q: 推理速度慢?**
```
解决方案:
1. 使用 GPU
2. 减小输入尺寸
3. 使用 ONNX 导出
4. 使用 TensorRT 优化
```

**Q: 检测效果差?**
```
可能原因:
1. 训练数据不足
2. 类别不平衡
3. 锚框设置不合理
4. 后处理阈值不当

解决方案:
1. 增加数据
2. 使用 Focal Loss
3. 调整锚框
4. 调整置信度阈值
```

## 6. 性能优化

### 6.1 训练优化

```python
# 1. 混合精度训练
scaler = torch.cuda.amp.GradScaler()
with torch.cuda.amp.autocast():
    outputs = model(images)
    loss = criterion(outputs, targets)
scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()

# 2. 数据加载优化
DataLoader(
    dataset,
    batch_size=16,
    num_workers=4,
    pin_memory=True,
    persistent_workers=True
)

# 3. 梯度累积
accumulation_steps = 4
for i, (images, targets) in enumerate(train_loader):
    loss = model(images, targets) / accumulation_steps
    loss.backward()
    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

### 6.2 推理优化

```python
# 1. ONNX 导出
import torch.onnx
torch.onnx.export(
    model,
    dummy_input,
    "model.onnx",
    opset_version=11
)

# 2. ONNX Runtime 优化
import onnxruntime as ort
session = ort.InferenceSession(
    "model.onnx",
    providers=['CUDAExecutionProvider']
)

# 3. TensorRT 优化 (需要 NVIDIA GPU)
# 参考 TensorRT 官方文档
```

### 6.3 内存优化

```python
# 1. 梯度检查点
from torch.utils.checkpoint import checkpoint
output = checkpoint(model.layer, input)

# 2. 释放不需要的张量
del intermediate_tensor
torch.cuda.empty_cache()

# 3. 使用就地操作
x = x.add_(1)  # 就地操作
```

## 7. 扩展开发

### 7.1 添加新模型

```python
# 1. 定义模型配置
YOLO_CONFIGS = {
    'yolov9_tiny': {
        'backbone': [...],
        'neck': [...],
        'head': [...]
    }
}

# 2. 实现模型类
class YOLOv9(nn.Module):
    def __init__(self, config):
        super().__init__()
        # ...

# 3. 注册模型
MODELS = {
    'yolov8_tiny': YOLOv8Tiny,
    'yolov9_tiny': YOLOv9Tiny,
}
```

### 7.2 添加新数据增强

```python
class CustomAugmentation:
    """自定义数据增强"""

    def __init__(self, prob=0.5):
        self.prob = prob

    def __call__(self, image, target):
        if random.random() < self.prob:
            # 执行增强
            image = self.augment_image(image)
            target = self.augment_target(target)
        return image, target

    def augment_image(self, image):
        # 实现图像增强
        pass

    def augment_target(self, target):
        # 实现标注增强
        pass
```

### 7.3 添加新损失函数

```python
class CustomLoss(nn.Module):
    """自定义损失函数"""

    def __init__(self):
        super().__init__()

    def forward(self, predictions, targets):
        # 计算损失
        loss = self.compute_loss(predictions, targets)
        return loss

    def compute_loss(self, predictions, targets):
        # 实现损失计算
        pass
```

## 8. 版本管理

### 8.1 语义化版本

```
版本格式: MAJOR.MINOR.PATCH

MAJOR: 不兼容的 API 修改
MINOR: 向下兼容的功能新增
PATCH: 向下兼容的问题修正

示例:
1.0.0 → 1.1.0 (新增功能)
1.1.0 → 1.1.1 (Bug 修复)
1.1.1 → 2.0.0 (重大更新)
```

### 8.2 分支管理

```
main: 稳定版本
develop: 开发版本
feature/*: 功能分支
hotfix/*: 紧急修复
release/*: 发布分支
```

## 9. 文档编写

### 9.1 代码注释

```python
def compute_iou(box1: Tensor, box2: Tensor) -> Tensor:
    """
    计算两组边界框的 IoU (Intersection over Union)

    Args:
        box1: 第一组边界框 [N, 4], 格式为 (x1, y1, x2, y2)
        box2: 第二组边界框 [M, 4], 格式为 (x1, y1, x2, y2)

    Returns:
        iou: IoU 矩阵 [N, M]

    Example:
        >>> box1 = torch.tensor([[0, 0, 10, 10]])
        >>> box2 = torch.tensor([[5, 5, 15, 15]])
        >>> iou = compute_iou(box1, box2)
        >>> print(iou)
        tensor([[0.1429]])
    """
    pass
```

### 9.2 README 编写

```markdown
# 项目名称

> 一句话描述

## 功能特性
- 特性 1
- 特性 2

## 快速开始
\`\`\`bash
pip install -r requirements.txt
\`\`\`

## 使用示例
\`\`\`python
from src.models import YOLOModel
\`\`\`

## 文档
- [详细文档](docs/)
```

## 10. 发布流程

### 10.1 发布检查清单

```
□ 所有测试通过
□ 文档更新完整
□ 版本号更新
□ CHANGELOG 更新
□ 依赖版本固定
□ 代码格式化
□ 无安全漏洞
```

### 10.2 发布步骤

```bash
# 1. 更新版本号
# setup.py, __init__.py

# 2. 运行测试
pytest tests/

# 3. 格式化代码
black src/ tests/

# 4. 提交代码
git add .
git commit -m "release: v1.0.0"

# 5. 打标签
git tag v1.0.0

# 6. 推送
git push origin main --tags
```

---

**文档版本**: v1.0
**最后更新**: 2024
