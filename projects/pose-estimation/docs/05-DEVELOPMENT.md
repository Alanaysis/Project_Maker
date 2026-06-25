# 开发指南 - 人体姿态估计

## 开发环境

### 依赖安装

```bash
pip install torch torchvision numpy opencv-python matplotlib pytest
```

### 项目结构

```
pose-estimation/
├── src/           # 源代码
├── tests/         # 测试
├── examples/      # 示例
├── docs/          # 文档
└── README.md      # 说明
```

## 开发流程

### 1. 热力图生成

**目标**: 从关键点坐标生成高斯热力图

**步骤**:
1. 创建坐标网格
2. 计算高斯分布
3. 应用可见性权重

**关键代码**:
```python
# 坐标网格
y_grid, x_grid = torch.meshgrid(y_coords, x_coords, indexing="ij")

# 高斯热力图
heatmaps = torch.exp(
    -((x_grid - kx) ** 2 + (y_grid - ky) ** 2) / (2 * sigma ** 2)
)
```

**踩坑记录**:
- `torch.meshgrid` 的 `indexing` 参数需要指定为 "ij"
- 关键点坐标需要从 [0, 1] 转换到热力图空间

### 2. 骨干网络

**目标**: 实现轻量级特征提取网络

**步骤**:
1. 设计 ConvBlock (Conv + BN + ReLU)
2. 设计 ResidualBlock
3. 组合为骨干网络

**关键代码**:
```python
class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1):
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
```

**踩坑记录**:
- `bias=False` 因为 BatchNorm 有自己的偏置
- 使用 `inplace=True` 节省内存

### 3. 热力图预测头

**目标**: 从特征图生成热力图

**步骤**:
1. 反卷积上采样
2. 最终卷积生成热力图

**关键代码**:
```python
class HeatmapHead(nn.Module):
    def __init__(self, in_channels, num_keypoints):
        self.deconv = nn.ConvTranspose2d(in_channels, 256, 4, 2, 1)
        self.final = nn.Conv2d(256, num_keypoints, 1)
```

**踩坑记录**:
- 反卷积的 kernel_size=4, stride=2, padding=1 实现 2x 上采样
- 最终使用 1x1 卷积生成 K 个热力图

### 4. 损失函数

**目标**: 实现 MSE 和 OHKM 损失

**步骤**:
1. 实现基础 MSE 损失
2. 添加权重支持
3. 实现 OHKM 损失

**关键代码**:
```python
# MSE 损失
mse_per_kp = ((pred - target) ** 2).mean(dim=2)
weighted_mse = mse_per_kp * weights
loss = weighted_mse.sum() / weights.sum().clamp(min=1.0)

# OHKM 损失
topk_loss, _ = torch.topk(mse_per_kp, topk, dim=1)
loss = topk_loss.mean()
```

**踩坑记录**:
- 需要处理 `weights.sum() = 0` 的情况
- OHKM 的 topk 不能超过关键点数量

### 5. 关键点提取

**目标**: 从热力图提取关键点坐标

**步骤**:
1. argmax 找峰值
2. 转换为 2D 坐标
3. 归一化到 [0, 1]

**关键代码**:
```python
# argmax
confidence, max_idx = torch.max(heatmaps_flat, dim=2)

# 转换为 2D
y_coords = max_idx / w
x_coords = max_idx % w

# 归一化
x_norm = x_coords / (w - 1)
y_norm = y_coords / (h - 1)
```

**踩坑记录**:
- `max_idx / w` 得到行坐标，`max_idx % w` 得到列坐标
- 归一化时除以 `(w - 1)` 而非 `w`

### 6. 可视化

**目标**: 在图像上绘制骨骼

**步骤**:
1. 绘制关键点
2. 绘制连线
3. 处理 OpenCV 不可用的情况

**关键代码**:
```python
def draw_skeleton(image, keypoints, confidence, ...):
    # 绘制连线
    for (i, j) in connections:
        cv2.line(img, (x1, y1), (x2, y2), color, thickness)
    
    # 绘制关键点
    for k in range(num_kp):
        cv2.circle(img, (x, y), radius, color, -1)
```

**踩坑记录**:
- OpenCV 使用 BGR 格式，需要转换
- 需要处理 OpenCV 不可用的情况（使用纯 numpy 绘制）

## 测试策略

### 单元测试

每个模块都有对应的测试文件：

```bash
pytest tests/test_model.py -v
pytest tests/test_heatmap.py -v
pytest tests/test_loss.py -v
pytest tests/test_keypoints.py -v
pytest tests/test_dataset.py -v
pytest tests/test_utils.py -v
```

### 集成测试

通过 demo.py 进行集成测试：

```bash
python examples/demo.py
```

### 数值测试

验证数学计算的正确性：

```python
def test_roundtrip():
    """测试生成热力图后提取关键点的精度"""
    original_kp = torch.tensor([[[0.3, 0.6]]])
    heatmaps = generate_heatmaps(original_kp, torch.ones(1, 1), (128, 128))
    extracted_kp, _ = heatmaps_to_keypoints(heatmaps)
    error = (original_kp - extracted_kp).abs().max()
    assert error < 0.05
```

## 性能优化

### 1. 使用 GPU

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
```

### 2. 混合精度训练

```python
scaler = torch.cuda.amp.GradScaler()
with torch.cuda.amp.autocast():
    pred = model(images)
    loss = criterion(pred, target)
scaler.scale(loss).backward()
```

### 3. 数据加载优化

```python
loader = DataLoader(
    dataset,
    batch_size=16,
    num_workers=4,
    pin_memory=True,
)
```

## 常见问题

### Q1: 热力图全为零

**原因**: 关键点坐标超出 [0, 1] 范围

**解决**: 检查数据预处理，确保坐标在 [0, 1] 范围内

### Q2: 训练不收敛

**原因**: 学习率过大

**解决**: 使用更小的学习率 (1e-4)，添加学习率调度

### Q3: 关键点精度低

**原因**: sigma 值不合适

**解决**: 调整 sigma 值 (通常 2-3 像素)

### Q4: 内存不足

**原因**: 图像或热力图尺寸过大

**解决**: 减小 batch_size 或图像尺寸

### Q5: 测试失败

**原因**: 数值精度问题

**解决**: 使用 `torch.allclose` 而非 `==` 比较浮点数

## 扩展方向

### 1. 使用真实数据集

```python
from torchvision.datasets import CocoDetection
dataset = CocoDetection(root="data/coco/train2017", annFile="...")
```

### 2. 更强的骨干网络

```python
import torchvision.models as models
backbone = models.resnet50(pretrained=True)
```

### 3. 高级技术

- 自顶向下方法
- 自底向上方法
- Transformer
- 3D 姿态估计
