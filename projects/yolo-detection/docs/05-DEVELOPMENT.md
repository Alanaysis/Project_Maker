# 05 - 开发指南

## 环境搭建

### 依赖安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install torch torchvision numpy matplotlib
pip install pytest pytest-cov  # 测试
```

### 项目结构

```
yolo-detection/
├── src/
│   ├── __init__.py
│   ├── model.py          # YOLO 网络架构
│   ├── loss.py           # 损失函数
│   ├── nms.py            # 非极大值抑制
│   ├── dataset.py        # 数据集处理
│   ├── utils.py          # 工具函数
│   ├── train.py          # 训练脚本
│   └── predict.py        # 推理脚本
├── tests/
│   ├── __init__.py
│   ├── test_model.py
│   ├── test_loss.py
│   ├── test_nms.py
│   ├── test_utils.py
│   └── test_dataset.py
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── README.md
└── LEARNING_NOTES.md
```

## 开发流程

### 1. 功能开发

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 开发和测试
# ...

# 提交
git add .
git commit -m "feat: add new feature"

# 合并
git checkout main
git merge feature/new-feature
```

### 2. 测试驱动开发

```python
# 1. 写测试
def test_new_feature():
    result = new_function(input)
    assert result == expected

# 2. 运行测试（失败）
pytest tests/test_new.py

# 3. 实现功能
def new_function(input):
    return expected

# 4. 运行测试（通过）
pytest tests/test_new.py
```

### 3. 代码审查清单

- [ ] 代码风格一致
- [ ] 有充分的测试覆盖
- [ ] 文档完整
- [ ] 性能可接受
- [ ] 无明显 bug

## 使用指南

### 基本使用

```python
from src.model import TinyYOLOv1
from src.predict import YOLOPredictor

# 创建模型
model = TinyYOLOv1(grid_size=7, num_boxes=2, num_classes=20)

# 创建预测器
predictor = YOLOPredictor(model)

# 运行检测
detections = predictor.detect(image)
```

### 训练模型

```python
from src.train import train_simple

# 快速训练测试
history = train_simple(
    num_epochs=10,
    batch_size=4,
    learning_rate=1e-3,
    num_train_samples=100,
    num_val_samples=20,
)
```

### 自定义训练

```python
from src.model import YOLOv1
from src.train import Trainer
from src.dataset import SimpleDetectionDataset, create_dataloader

# 创建模型
model = YOLOv1(grid_size=7, num_boxes=2, num_classes=20)

# 创建数据集
train_dataset = SimpleDetectionDataset(num_samples=1000)
val_dataset = SimpleDetectionDataset(num_samples=200)

# 创建数据加载器
train_loader = create_dataloader(train_dataset, batch_size=8)
val_loader = create_dataloader(val_dataset, batch_size=8)

# 配置训练
config = {
    "learning_rate": 1e-3,
    "epochs": 50,
    "checkpoint_dir": "checkpoints/my_experiment",
}

# 训练
trainer = Trainer(model, train_loader, val_loader, config)
history = trainer.train()
```

### 使用 NMS

```python
from src.nms import non_max_suppression, batched_nms

# 标准 NMS
keep_boxes, keep_scores = non_max_suppression(
    boxes, scores,
    iou_threshold=0.5,
    score_threshold=0.1
)

# 按类别 NMS
keep_boxes, keep_scores, keep_labels = batched_nms(
    boxes, scores, labels,
    iou_threshold=0.5
)
```

## 调试技巧

### 1. 检查数据

```python
# 可视化数据
import matplotlib.pyplot as plt

image, targets = dataset[0]
plt.imshow(image.permute(1, 2, 0))
plt.show()

# 检查目标张量
print("Target shape:", targets["target"].shape)
print("Target sum:", targets["target"].sum())
```

### 2. 检查模型输出

```python
# 检查输出形状
output = model(images)
print("Output shape:", output.shape)
print("Output range:", output.min(), output.max())

# 检查梯度
loss.backward()
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad norm = {param.grad.norm()}")
```

### 3. 检查损失

```python
# 打印损失组件
loss, loss_dict = criterion(predictions, targets)
for key, value in loss_dict.items():
    print(f"{key}: {value:.4f}")
```

### 4. 可视化检测结果

```python
from src.utils import draw_boxes

# 绘制检测框
result_image = draw_boxes(
    image,
    detections["boxes"].numpy(),
    detections["scores"].numpy(),
    detections["labels"].numpy()
)
plt.imshow(result_image)
plt.show()
```

## 常见问题

### 1. 损失不下降

**可能原因**：
- 学习率过大或过小
- 数据预处理错误
- 损失函数实现错误

**解决方案**：
```python
# 尝试不同学习率
trainer = Trainer(model, train_loader, val_loader, {"learning_rate": 1e-4})

# 检查数据
for images, targets in train_loader:
    print("Image range:", images.min(), images.max())
    print("Target sum:", targets["target"].sum())
    break
```

### 2. 检测结果差

**可能原因**：
- 训练数据不足
- 模型太小
- 没有数据增强

**解决方案**：
```python
# 增加数据
train_dataset = SimpleDetectionDataset(num_samples=5000)

# 使用更大的模型
model = YOLOv1(grid_size=7, num_boxes=2, num_classes=20)

# 添加数据增强
train_dataset = MultiScaleDataset(train_dataset, scales=[320, 384, 448])
```

### 3. 内存不足

**可能原因**：
- 批量太大
- 图像太大
- 模型太大

**解决方案**：
```python
# 减小批量
train_loader = create_dataloader(train_dataset, batch_size=2)

# 使用梯度累积
for i, (images, targets) in enumerate(train_loader):
    loss = criterion(model(images), targets)
    loss = loss / accumulation_steps
    loss.backward()

    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

## 性能优化

### 1. 数据加载优化

```python
# 使用多进程加载
train_loader = create_dataloader(
    train_dataset,
    batch_size=8,
    num_workers=4,
    pin_memory=True
)
```

### 2. 模型优化

```python
# 使用混合精度训练
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()
for images, targets in train_loader:
    with autocast():
        predictions = model(images)
        loss = criterion(predictions, targets)

    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

### 3. 推理优化

```python
# 使用 torch.no_grad()
with torch.no_grad():
    detections = predictor.detect(image)

# 使用 JIT 编译
model = torch.jit.script(model)
```

## 扩展开发

### 1. 添加新数据集

```python
class CustomDataset(Dataset):
    def __init__(self, data_dir):
        # 加载自定义数据
        pass

    def __getitem__(self, idx):
        # 返回图像和目标
        return image, targets
```

### 2. 修改模型架构

```python
class CustomYOLO(YOLOv1):
    def __init__(self):
        super().__init__()
        # 修改骨干网络
        self.backbone = nn.Sequential(...)
```

### 3. 添加新的损失函数

```python
class CustomLoss(nn.Module):
    def forward(self, predictions, targets):
        # 实现自定义损失
        return loss
```

## 部署

### 1. 模型导出

```python
# 导出为 ONNX
torch.onnx.export(
    model,
    dummy_input,
    "model.onnx",
    opset_version=11
)

# 导出为 TorchScript
scripted_model = torch.jit.script(model)
scripted_model.save("model.pt")
```

### 2. 推理服务

```python
# Flask API 示例
from flask import Flask, request, jsonify

app = Flask(__name__)
predictor = YOLOPredictor.from_checkpoint("best_model.pt")

@app.route("/detect", methods=["POST"])
def detect():
    image = load_image(request.files["image"])
    detections = predictor.detect(image)
    return jsonify(format_detections(detections))
```

### 3. 边缘部署

```python
# 使用 TensorRT
import tensorrt as trt

# 转换模型
engine = convert_to_tensorrt(model, input_shape=(1, 3, 448, 448))
```
