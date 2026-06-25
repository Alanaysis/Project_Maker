# 05 - 开发指南

## 1. 开发环境搭建

### 1.1 系统要求

- Python 3.8+
- CUDA 11.0+ (可选，用于 GPU 加速)
- 8GB+ RAM
- 2GB+ 显存 (使用 GPU 时)

### 1.2 依赖安装

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

| 工具 | 用途 | 安装 |
|------|------|------|
| pytest | 测试框架 | `pip install pytest` |
| black | 代码格式化 | `pip install black` |
| flake8 | 代码检查 | `pip install flake8` |
| mypy | 类型检查 | `pip install mypy` |
| pytest-cov | 覆盖率 | `pip install pytest-cov` |

## 2. 项目结构

```
text-detection/
├── src/                    # 源代码
│   ├── model/             # 模型定义
│   │   ├── backbone.py    # 骨干网络
│   │   ├── neck.py        # 特征融合
│   │   ├── head.py        # 检测头
│   │   └── east_net.py    # 完整网络
│   ├── loss/              # 损失函数
│   │   └── east_loss.py
│   ├── postprocess/       # 后处理
│   │   └── nms.py
│   ├── data/              # 数据处理
│   │   ├── dataset.py
│   │   └── transforms.py
│   └── utils/             # 工具函数
│       └── visualizer.py
├── tests/                 # 测试文件
├── examples/              # 示例脚本
├── docs/                  # 文档
├── checkpoints/           # 模型权重
└── outputs/               # 输出结果
```

## 3. 编码规范

### 3.1 Python 风格

```python
# 使用 snake_case 命名函数和变量
def compute_iou(box1, box2):
    ...

# 使用 PascalCase 命名类
class EASTNet(nn.Module):
    ...

# 使用 UPPER_CASE 命名常量
MAX_IMAGE_SIZE = 1024
```

### 3.2 类型注解

```python
from typing import List, Tuple, Dict, Optional

def detect(self, images: torch.Tensor) -> List[Dict[str, np.ndarray]]:
    """
    Args:
        images: [B, C, H, W] normalized images

    Returns:
        List of detection results
    """
```

### 3.3 文档字符串

```python
class EASTNet(nn.Module):
    """
    EAST: Efficient and Accurate Scene Text Detector

    Architecture:
    1. Backbone: VGG-like feature extractor
    2. Neck: U-Net feature merging
    3. Head: Score + Geometry prediction

    Args:
        backbone_type: 'vgg' or 'light'
        neck_type: 'unet' or 'fpn'
        geo_type: 'rbox' or 'quad'
        in_channels: Input image channels

    Example:
        >>> model = EASTNet(backbone_type='vgg')
        >>> x = torch.randn(1, 3, 512, 512)
        >>> output = model(x)
        >>> output['score'].shape
        torch.Size([1, 1, 128, 128])
    """
```

## 4. 开发流程

### 4.1 新增功能

1. **创建分支**
   ```bash
   git checkout -b feature/new-backbone
   ```

2. **实现功能**
   ```bash
   # 编写代码
   vim src/model/backbone.py

   # 编写测试
   vim tests/test_model.py
   ```

3. **运行测试**
   ```bash
   pytest tests/ -v
   ```

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add new backbone"
   ```

### 4.2 Bug 修复

1. **重现问题**
   ```bash
   pytest tests/test_model.py::TestVGGBackbone::test_output_shapes -v
   ```

2. **定位问题**
   ```python
   # 添加调试信息
   print(f"Input shape: {x.shape}")
   print(f"Output shape: {output.shape}")
   ```

3. **修复并测试**
   ```bash
   pytest tests/ -v
   ```

## 5. 模型开发

### 5.1 新增 Backbone

```python
class NewBackbone(nn.Module):
    """
    新的骨干网络实现

    Args:
        in_channels: 输入通道数
    """

    def __init__(self, in_channels=3):
        super().__init__()
        # 定义网络层
        self.layer1 = ...
        self.layer2 = ...

    def forward(self, x):
        """
        返回多尺度特征

        Args:
            x: [B, C, H, W]

        Returns:
            (f1, f2, f3, f4, f5)
        """
        f1 = self.layer1(x)
        f2 = self.layer2(f1)
        ...
        return f1, f2, f3, f4, f5
```

### 5.2 新增检测头

```python
class NewHead(nn.Module):
    """新的检测头实现"""

    def __init__(self, in_channels):
        super().__init__()
        self.score_branch = nn.Sequential(
            nn.Conv2d(in_channels, 1, 1),
            nn.Sigmoid()
        )
        self.geo_branch = nn.Conv2d(in_channels, 5, 1)

    def forward(self, x):
        score = self.score_branch(x)
        geo = self.geo_branch(x)
        return score, geo
```

### 5.3 新增损失函数

```python
class NewLoss(nn.Module):
    """新的损失函数实现"""

    def forward(self, pred, target, mask):
        """
        计算损失

        Args:
            pred: 预测值
            target: 真实值
            mask: 掩码

        Returns:
            loss: 标量损失
        """
        loss = F.l1_loss(pred * mask, target * mask)
        return loss
```

## 6. 数据开发

### 6.1 新增数据集

```python
class NewDataset(Dataset):
    """新的数据集实现"""

    def __init__(self, data_dir, transform=None):
        self.data_dir = data_dir
        self.transform = transform
        self.samples = self._load_samples()

    def _load_samples(self):
        """加载数据样本列表"""
        samples = []
        for img_path in glob(f"{self.data_dir}/*.jpg"):
            label_path = img_path.replace('.jpg', '.txt')
            samples.append((img_path, label_path))
        return samples

    def __getitem__(self, idx):
        img_path, label_path = self.samples[idx]
        image = cv2.imread(img_path)
        boxes = self._load_boxes(label_path)

        if self.transform:
            image, boxes = self.transform(image, boxes)

        return image, boxes

    def _load_boxes(self, label_path):
        """加载边界框"""
        boxes = []
        with open(label_path) as f:
            for line in f:
                x1, y1, x2, y2 = map(float, line.strip().split())
                boxes.append([x1, y1, x2, y2])
        return np.array(boxes)
```

### 6.2 新增数据增强

```python
class NewTransform:
    """新的数据增强实现"""

    def __init__(self, params):
        self.params = params

    def __call__(self, image, boxes):
        """
        应用数据增强

        Args:
            image: [H, W, 3] 图像
            boxes: [N, 4] 边界框

        Returns:
            augmented_image, augmented_boxes
        """
        # 实现增强逻辑
        ...
        return image, boxes
```

## 7. 调试技巧

### 7.1 形状调试

```python
def debug_shapes(model, x):
    """打印各层输出形状"""
    print(f"Input: {x.shape}")

    features = model.backbone(x)
    for i, f in enumerate(features):
        print(f"Backbone stage {i+1}: {f.shape}")

    merged = model.neck(features)
    print(f"Neck output: {merged.shape}")

    score, geo = model.head(merged)
    print(f"Score: {score.shape}")
    print(f"Geo: {geo.shape}")
```

### 7.2 梯度调试

```python
def debug_gradients(model):
    """检查梯度流"""
    for name, param in model.named_parameters():
        if param.grad is not None:
            print(f"{name}: grad_mean={param.grad.mean():.6f}")
        else:
            print(f"{name}: NO GRADIENT")
```

### 7.3 损失调试

```python
def debug_loss(loss_fn, pred, target, mask):
    """调试损失计算"""
    total, score_loss, geo_loss = loss_fn(pred, target, mask)

    print(f"Total loss: {total.item():.4f}")
    print(f"Score loss: {score_loss.item():.4f}")
    print(f"Geo loss: {geo_loss.item():.4f}")

    if torch.isnan(total):
        print("WARNING: NaN detected!")
        print(f"Pred range: [{pred.min():.4f}, {pred.max():.4f}]")
        print(f"Target range: [{target.min():.4f}, {target.max():.4f}]")
```

## 8. 性能优化

### 8.1 模型优化

```python
# 使用轻量级 backbone
model = EASTNet(backbone_type='light')

# 使用混合精度训练
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()

with autocast():
    output = model(images)
    loss = criterion(output, targets)

scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

### 8.2 数据加载优化

```python
# 增加 DataLoader workers
dataloader = DataLoader(
    dataset,
    batch_size=32,
    num_workers=4,
    pin_memory=True,
    prefetch_factor=2
)
```

### 8.3 推理优化

```python
# 模型量化
quantized_model = torch.quantization.quantize_dynamic(
    model, {nn.Linear, nn.Conv2d}, dtype=torch.qint8
)

# ONNX 导出
torch.onnx.export(model, dummy_input, "model.onnx", opset_version=11)
```

## 9. 常见问题

### 9.1 CUDA 内存不足

```python
# 减小 batch size
batch_size = 4  # 从 16 减到 4

# 使用梯度累积
optimizer.zero_grad()
for i, (images, targets) in enumerate(dataloader):
    loss = criterion(model(images), targets)
    loss = loss / accumulation_steps
    loss.backward()

    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

### 9.2 模型不收敛

```python
# 检查学习率
print(f"Learning rate: {optimizer.param_groups[0]['lr']}")

# 检查数据
print(f"Image range: [{images.min():.4f}, {images.max():.4f}]")
print(f"Target range: [{targets.min():.4f}, {targets.max():.4f}]")

# 使用学习率预热
scheduler = WarmupLR(optimizer, warmup_epochs=5)
```

### 9.3 测试失败

```bash
# 查看详细错误
pytest tests/test_model.py -v --tb=long

# 只运行失败的测试
pytest tests/test_model.py -x

# 进入调试模式
pytest tests/test_model.py --pdb
```

## 10. 部署指南

### 10.1 模型导出

```python
# PyTorch 保存
torch.save(model.state_dict(), 'model.pth')

# ONNX 导出
torch.onnx.export(
    model,
    dummy_input,
    'model.onnx',
    opset_version=11,
    input_names=['input'],
    output_names=['score', 'geometry'],
    dynamic_axes={'input': {0: 'batch'}}
)
```

### 10.2 TensorRT 优化

```python
import tensorrt as trt

# 构建 TensorRT 引擎
logger = trt.Logger(trt.Logger.WARNING)
builder = trt.Builder(logger)
network = builder.create_network()
parser = trt.OnnxParser(network, logger)

with open('model.onnx', 'rb') as f:
    parser.parse(f.read())

engine = builder.build_cuda_engine(network)
```

### 10.3 服务部署

```python
from flask import Flask, request, jsonify
import torch

app = Flask(__name__)
model = EASTNet()
model.load_state_dict(torch.load('model.pth'))
model.eval()

@app.route('/detect', methods=['POST'])
def detect():
    image = preprocess(request.files['image'])
    results = detector.detect(image)
    return jsonify(results)
```
