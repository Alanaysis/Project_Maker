# 技术设计文档

> Industrial Vision Detection - Technical Design

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    工业视觉检测系统                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   数据层      │    │   模型层      │    │   部署层      │  │
│  │              │    │              │    │              │  │
│  │  - 数据加载   │    │  - Backbone  │    │  - ONNX 导出  │  │
│  │  - 数据增强   │    │  - Neck      │    │  - 推理引擎   │  │
│  │  - 标注解析   │    │  - Head      │    │  - 后处理     │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │          │
│         └───────────────────┼───────────────────┘          │
│                             │                              │
│                    ┌────────▼────────┐                     │
│                    │    训练引擎      │                     │
│                    │                │                     │
│                    │  - 损失计算     │                     │
│                    │  - 优化器       │                     │
│                    │  - 学习率调度   │                     │
│                    │  - 日志记录     │                     │
│                    └────────────────┘                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
src/
├── models/           # 模型定义
│   ├── backbone.py   # 骨干网络 (CSPDarknet)
│   ├── neck.py       # 特征融合 (PANet)
│   ├── head.py       # 检测头 (Decoupled Head)
│   ├── yolo.py       # YOLO 完整模型
│   └── losses.py     # 损失函数
│
├── data/             # 数据处理
│   ├── dataset.py    # 数据集类
│   ├── transforms.py # 数据变换
│   ├── augmentations.py # 高级增强
│   └── utils.py      # 数据工具
│
├── utils/            # 工具函数
│   ├── metrics.py    # 评估指标
│   ├── visualization.py # 可视化
│   ├── boxes.py      # 边界框操作
│   └── general.py    # 通用工具
│
└── deployment/       # 部署相关
    ├── onnx_export.py # ONNX 导出
    └── onnx_inference.py # ONNX 推理
```

## 2. 核心模块设计

### 2.1 Backbone 设计

#### 2.1.1 CSPDarknet 架构

```
输入图像 [B, 3, 640, 640]
        ↓
┌───────────────────────┐
│ Stem Block            │
│ Conv 3x3, stride=2   │
│ [B, 32, 320, 320]    │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Stage 1               │
│ CSP Block × 1         │
│ [B, 64, 160, 160]    │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Stage 2               │
│ CSP Block × 2         │
│ [B, 128, 80, 80]     │  ← P3 输出
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Stage 3               │
│ CSP Block × 2         │
│ [B, 256, 40, 40]     │  ← P4 输出
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Stage 4               │
│ CSP Block × 1         │
│ [B, 512, 20, 20]     │  ← P5 输出
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ SPPF                  │
│ Spatial Pyramid Pool  │
│ [B, 512, 20, 20]     │
└───────────────────────┘
```

#### 2.1.2 核心组件

**ConvBlock**: 基础卷积块

```python
class ConvBlock(nn.Module):
    """Conv + BN + Activation"""
    def __init__(self, in_channels, out_channels, kernel_size, stride, activation='SiLU'):
        # Conv2d → BatchNorm2d → SiLU
```

**CSPBlock**: Cross Stage Partial Block

```python
class CSPBlock(nn.Module):
    """Cross Stage Partial Block"""
    def __init__(self, in_channels, out_channels, num_bottlenecks):
        # Split → Transform × N → Merge
```

**SPPF**: Spatial Pyramid Pooling - Fast

```python
class SPPF(nn.Module):
    """Fast SPP implementation"""
    def __init__(self, in_channels, out_channels, kernel_size=5):
        # MaxPool2d × 3 → Concat → Conv
```

### 2.2 Neck 设计

#### 2.2.1 PANet 架构

```
P5 (20×20) ─────────────────────────────────────────────┐
    ↓                                                    │
┌───────────────┐                                        │
│ Upsample 2x   │                                        │
│ Conv 1×1      │                                        │
└───────┬───────┘                                        │
        ↓                                                │
P4 (40×40) ──────→ Concat ──→ C2f ──→ Upsample 2x ─────┤
                          ↑                              │
                          │                              │
┌─────────────────────────┘                              │
│                                                        │
P3 (80×80) ──────→ Concat ──→ C2f ──→ [输出 P3] ────────┤
                                                        │
┌─────────────────────────────────────────────────────────┘
│
↓ Downsample 2x ──→ Concat ──→ C2f ──→ [输出 P4]
│
↓ Downsample 2x ──→ Concat ──→ C2f ──→ [输出 P5]
```

#### 2.2.2 核心组件

**C2f**: CSP Bottleneck with 2 convolutions

```python
class C2f(nn.Module):
    """CSP Bottleneck with 2 convolutions"""
    def __init__(self, in_channels, out_channels, num_bottlenecks):
        # Split → Bottleneck × N → Concat → Conv
```

**FPN**: Feature Pyramid Network (自顶向下)

```python
class FPN(nn.Module):
    """Top-down pathway"""
    def forward(self, features):
        # P5 → upsample + add → P4 → upsample + add → P3
```

**PAN**: Path Aggregation Network (自底向上)

```python
class PAN(nn.Module):
    """Bottom-up pathway"""
    def forward(self, features):
        # P3 → downsample + add → P4 → downsample + add → P5
```

### 2.3 Head 设计

#### 2.3.1 解耦头架构

```
特征图 [B, C, H, W]
        ↓
┌───────────────────────────────────────────┐
│              Decoupled Head               │
├───────────────────────────────────────────┤
│                                           │
│  ┌─────────────┐      ┌─────────────┐    │
│  │ 分类分支     │      │ 回归分支     │    │
│  │             │      │             │    │
│  │ Conv 3×3    │      │ Conv 3×3    │    │
│  │ Conv 1×1    │      │ Conv 3×3    │    │
│  │             │      │ Conv 1×1    │    │
│  │ [B, nc, H, W]│    │ [B, 64, H, W]│   │
│  └─────────────┘      └──────┬──────┘    │
│                              │           │
│                              ↓           │
│                    ┌─────────────────┐   │
│                    │ DFL + Conv      │   │
│                    │ [B, 4*reg, H, W]│   │
│                    └─────────────────┘   │
│                                           │
└───────────────────────────────────────────┘
```

#### 2.3.2 输出格式

```python
# 训练模式输出
{
    'cls_pred': Tensor [B, num_anchors, num_classes],  # 分类预测
    'reg_pred': Tensor [B, num_anchors, 4 * reg_max],  # 回归预测
    'obj_pred': Tensor [B, num_anchors, 1],            # 目标性预测
}

# 推理模式输出
{
    'boxes': Tensor [N, 4],      # 边界框 (x1, y1, x2, y2)
    'scores': Tensor [N],        # 置信度
    'labels': Tensor [N],        # 类别标签
}
```

### 2.4 损失函数设计

#### 2.4.1 损失组成

```
Total Loss = λ_cls * L_cls + λ_box * L_box + λ_obj * L_obj

其中:
- L_cls: 分类损失 (BCE Loss / Focal Loss)
- L_box: 边界框回归损失 (CIoU Loss)
- λ: 权重系数
```

#### 2.4.2 CIoU Loss

```python
def ciou_loss(pred_boxes, target_boxes):
    """
    Complete IoU Loss

    CIoU = IoU - (ρ²(b, b^gt) / c²) - αv

    其中:
    - ρ: 欧氏距离
    - b, b^gt: 预测框和目标框中心点
    - c: 最小外接矩形对角线长度
    - v: 长宽比一致性
    - α: 权重系数
    """
```

#### 2.4.3 Focal Loss

```python
def focal_loss(pred, target, alpha=0.25, gamma=2.0):
    """
    Focal Loss for class imbalance

    FL(p_t) = -α_t * (1 - p_t)^γ * log(p_t)

    解决正负样本不平衡问题
    """
```

### 2.5 Anchor 设计

#### 2.5.1 Anchor-free 策略

```
特征图每个位置预测:
- 边界框 (相对于网格的偏移)
- 宽高 (直接预测或 DFL)
- 类别概率
- 目标置信度

与 Anchor-based 的区别:
- 不需要预定义锚框
- 每个位置只预测一个目标
- 简化了匹配策略
```

#### 2.5.2 标签分配

```python
def assign_targets(predictions, targets, strides):
    """
    标签分配策略 (Task-Aligned Assigner)

    1. 计算每个预测与目标的对齐度
    2. 选择 top-k 预测作为正样本
    3. 其余为负样本
    """
```

## 3. 数据结构设计

### 3.1 标注格式

```python
# COCO 格式
{
    "images": [
        {
            "id": int,
            "file_name": str,
            "width": int,
            "height": int
        }
    ],
    "annotations": [
        {
            "id": int,
            "image_id": int,
            "category_id": int,
            "bbox": [x, y, w, h],  # 左上角坐标 + 宽高
            "area": float,
            "iscrowd": 0 or 1
        }
    ],
    "categories": [
        {
            "id": int,
            "name": str,
            "supercategory": str
        }
    ]
}

# YOLO 格式 (每行)
# class_id center_x center_y width height (归一化到 0-1)
0 0.5 0.5 0.3 0.4
```

### 3.2 模型配置

```python
# 模型配置数据类
@dataclass
class ModelConfig:
    # 输入配置
    input_size: int = 640

    # 类别数
    num_classes: int = 80

    # 深度因子 (控制模块重复次数)
    depth_multiple: float = 0.33

    # 宽度因子 (控制通道数)
    width_multiple: float = 0.25

    # Backbone 配置
    backbone: list = None

    # Neck 配置
    neck: list = None

    # Head 配置
    head: list = None
```

### 3.3 训练配置

```python
@dataclass
class TrainingConfig:
    # 优化器
    optimizer: str = 'SGD'
    lr: float = 0.01
    momentum: float = 0.937
    weight_decay: float = 0.0005

    # 学习率调度
    scheduler: str = 'cosine'
    warmup_epochs: int = 3

    # 训练参数
    epochs: int = 100
    batch_size: int = 16

    # 数据增强
    mosaic_prob: float = 1.0
    mixup_prob: float = 0.0
```

### 3.4 检测结果

```python
@dataclass
class Detection:
    """单个检测结果"""
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2
    score: float
    class_id: int
    class_name: str

@dataclass
class DetectionResult:
    """图像检测结果"""
    image_id: str
    detections: List[Detection]
    inference_time: float
```

## 4. 接口设计

### 4.1 数据接口

```python
class DefectDataset(Dataset):
    """工业缺陷数据集"""

    def __init__(
        self,
        data_dir: str,
        annotation_file: str,
        transforms: Optional[Callable] = None,
        image_size: int = 640
    ):
        """
        Args:
            data_dir: 图像目录路径
            annotation_file: 标注文件路径
            transforms: 数据变换函数
            image_size: 输入图像尺寸
        """
        pass

    def __getitem__(self, index: int) -> Tuple[Tensor, Dict]:
        """
        获取单个样本

        Returns:
            image: Tensor [3, H, W]
            target: dict with keys:
                - boxes: Tensor [N, 4]
                - labels: Tensor [N]
                - image_id: int
        """
        pass

    def __len__(self) -> int:
        """数据集大小"""
        pass
```

### 4.2 模型接口

```python
class YOLOModel(nn.Module):
    """YOLO 目标检测模型"""

    def __init__(self, config: ModelConfig):
        """
        Args:
            config: 模型配置
        """
        super().__init__()
        self.backbone = build_backbone(config)
        self.neck = build_neck(config)
        self.head = build_head(config)

    def forward(
        self,
        images: Tensor,
        targets: Optional[List[Dict]] = None
    ) -> Union[Dict, List[Dict]]:
        """
        前向传播

        Args:
            images: 输入图像 [B, 3, H, W]
            targets: 训练目标 (可选)

        Returns:
            训练模式: dict with losses
            推理模式: list of detection results
        """
        pass

    def predict(
        self,
        image: Union[Tensor, np.ndarray],
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45
    ) -> DetectionResult:
        """
        单张图像预测

        Args:
            image: 输入图像
            conf_threshold: 置信度阈值
            iou_threshold: NMS IoU 阈值

        Returns:
            DetectionResult
        """
        pass
```

### 4.3 训练接口

```python
class Trainer:
    """模型训练器"""

    def __init__(
        self,
        model: YOLOModel,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        config: TrainingConfig = None
    ):
        """
        Args:
            model: YOLO 模型
            train_loader: 训练数据加载器
            val_loader: 验证数据加载器
            config: 训练配置
        """
        pass

    def train(self, epochs: int) -> Dict:
        """
        执行训练

        Args:
            epochs: 训练轮数

        Returns:
            训练历史记录
        """
        pass

    def evaluate(self) -> Dict:
        """
        评估模型

        Returns:
            评估指标
        """
        pass

    def save_checkpoint(self, path: str):
        """保存检查点"""
        pass

    def load_checkpoint(self, path: str):
        """加载检查点"""
        pass
```

### 4.4 导出接口

```python
def export_to_onnx(
    model: YOLOModel,
    output_path: str,
    input_shape: Tuple[int, int, int, int] = (1, 3, 640, 640),
    opset_version: int = 11,
    dynamic_axes: Optional[Dict] = None
) -> str:
    """
    导出 ONNX 模型

    Args:
        model: PyTorch 模型
        output_path: 输出路径
        input_shape: 输入形状
        opset_version: ONNX 版本
        dynamic_axes: 动态轴配置

    Returns:
        ONNX 模型路径
    """
    pass

def validate_onnx_model(
    onnx_path: str,
    pytorch_model: YOLOModel,
    test_input: Tensor,
    rtol: float = 1e-3,
    atol: float = 1e-5
) -> bool:
    """
    验证 ONNX 模型

    Args:
        onnx_path: ONNX 模型路径
        pytorch_model: PyTorch 模型
        test_input: 测试输入
        rtol: 相对误差容忍度
        atol: 绝对误差容忍度

    Returns:
        验证是否通过
    """
    pass
```

## 5. 算法设计

### 5.1 NMS 算法

```python
def non_max_suppression(
    predictions: Tensor,
    conf_threshold: float = 0.25,
    iou_threshold: float = 0.45,
    max_det: int = 300
) -> List[Tensor]:
    """
    Non-Maximum Suppression

    步骤:
    1. 过滤低置信度预测
    2. 按置信度排序
    3. 选择最高置信度的框
    4. 删除与其 IoU > 阈值的框
    5. 重复直到没有框剩余
    """
```

### 5.2 IoU 计算

```python
def box_iou(box1: Tensor, box2: Tensor) -> Tensor:
    """
    计算两组边界框的 IoU

    IoU = Intersection / Union

    Args:
        box1: [N, 4] (x1, y1, x2, y2)
        box2: [M, 4] (x1, y1, x2, y2)

    Returns:
        iou: [N, M]
    """
```

### 5.3 mAP 计算

```python
def compute_ap(
    predictions: List[Dict],
    ground_truths: List[Dict],
    iou_threshold: float = 0.5
) -> Dict:
    """
    计算 Average Precision

    步骤:
    1. 按置信度排序预测
    2. 计算 Precision-Recall 曲线
    3. 计算 AP (曲线下面积)
    4. 计算 mAP (所有类别 AP 均值)
    """
```

## 6. 性能优化设计

### 6.1 训练优化

```python
# 混合精度训练
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()
with autocast():
    outputs = model(images)
    loss = criterion(outputs, targets)
scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

### 6.2 数据加载优化

```python
# 多进程数据加载
DataLoader(
    dataset,
    batch_size=16,
    num_workers=4,      # 多进程加载
    pin_memory=True,    # 内存锁定
    persistent_workers=True  # 持久化工作进程
)
```

### 6.3 模型优化

```python
# ONNX 优化
import onnxruntime as ort

session = ort.InferenceSession(
    "model.onnx",
    providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
)
```

## 7. 错误处理设计

### 7.1 异常类型

```python
class VisionDetectionError(Exception):
    """基础异常类"""
    pass

class DataLoadError(VisionDetectionError):
    """数据加载异常"""
    pass

class ModelError(VisionDetectionError):
    """模型异常"""
    pass

class ExportError(VisionDetectionError):
    """导出异常"""
    pass
```

### 7.2 错误处理策略

```python
try:
    dataset = DefectDataset(data_dir, annotation_file)
except FileNotFoundError:
    logger.error(f"数据文件不存在: {annotation_file}")
    raise DataLoadError(f"无法找到标注文件: {annotation_file}")
except json.JSONDecodeError:
    logger.error(f"标注文件格式错误: {annotation_file}")
    raise DataLoadError(f"标注文件 JSON 解析失败")
```

## 8. 配置管理

### 8.1 YAML 配置

```yaml
# configs/default.yaml
model:
  type: yolov8_tiny
  num_classes: 80
  input_size: 640

training:
  epochs: 100
  batch_size: 16
  optimizer: sgd
  lr: 0.01
  weight_decay: 0.0005

data:
  train_dir: data/train
  val_dir: data/val
  annotation_format: coco
```

### 8.2 配置加载

```python
import yaml
from dataclasses import dataclass

def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config
```

## 9. 日志设计

### 9.1 日志格式

```python
import logging

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)
```

### 9.2 训练日志

```python
# 训练过程日志
logger.info(f"Epoch {epoch}/{total_epochs}")
logger.info(f"Train Loss: {train_loss:.4f}")
logger.info(f"Val Loss: {val_loss:.4f}")
logger.info(f"mAP@0.5: {map50:.4f}")
logger.info(f"mAP@0.5:0.95: {map:.4f}")
```

## 10. 扩展性设计

### 10.1 模型扩展

```python
# 支持不同大小的模型
MODEL_CONFIGS = {
    'yolov8_nano': {'depth': 0.33, 'width': 0.25},
    'yolov8_small': {'depth': 0.33, 'width': 0.50},
    'yolov8_medium': {'depth': 0.67, 'width': 0.75},
    'yolov8_large': {'depth': 1.00, 'width': 1.00},
}
```

### 10.2 数据增强扩展

```python
# 可组合的数据增强
class Compose:
    """组合多个变换"""
    def __init__(self, transforms):
        self.transforms = transforms

    def __call__(self, image, target):
        for t in self.transforms:
            image, target = t(image, target)
        return image, target
```

---

**文档版本**: v1.0
**最后更新**: 2024
