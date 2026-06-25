# 设计文档 - 点云处理

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    点云处理系统                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 数据层   │  │ 模型层   │  │ 训练层   │  │ 可视化层 │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

| 模块 | 职责 | 文件 |
|------|------|------|
| 数据层 | 数据加载、预处理、增强 | dataset.py, utils.py |
| 模型层 | PointNet 模型定义 | pointnet.py |
| 训练层 | 训练循环、评估 | trainer.py |
| 可视化层 | 3D 可视化、结果展示 | visualization.py |

## 2. 数据设计

### 2.1 点云数据格式

```python
# 标准格式: (N, 3)
points = np.array([
    [x1, y1, z1],
    [x2, y2, z2],
    ...
])

# 批量格式: (B, N, 3)
batch_points = np.array([points1, points2, ...])

# 模型输入格式: (B, 3, N)
model_input = batch_points.transpose(0, 2, 1)
```

### 2.2 数据集接口

```python
class PointCloudDataset(Dataset):
    def __init__(self, points, labels, task, transform):
        # points: (N, num_points, 3)
        # labels: 分类 (N,) 或分割 (N, num_points)
        pass

    def __getitem__(self, idx):
        # 返回 (points, labels)
        # points: (3, num_points) - 转置后
        pass
```

### 2.3 数据增强

| 增强方法 | 参数范围 | 作用 |
|----------|----------|------|
| 随机旋转 | 0-360° | 增加旋转不变性 |
| 随机缩放 | 0.8-1.2 | 增加尺度不变性 |
| 随机平移 | ±0.1 | 增加平移不变性 |
| 随机抖动 | σ=0.01 | 增加鲁棒性 |

## 3. 模型设计

### 3.1 TNet (空间变换网络)

```
输入: (B, k, N)
  ↓
Conv1d(k, 64) + BN + ReLU
  ↓
Conv1d(64, 128) + BN + ReLU
  ↓
Conv1d(128, 1024) + BN + ReLU
  ↓
MaxPool → (B, 1024)
  ↓
FC(1024, 512) + BN + ReLU
  ↓
FC(512, 256) + BN + ReLU
  ↓
FC(256, k*k)
  ↓
+ I (单位矩阵)
  ↓
输出: (B, k, k)
```

**设计要点**:
- 初始化为单位矩阵，保证初始变换为恒等变换
- 使用 BatchNorm 加速收敛
- 适当的 Dropout 防止过拟合

### 3.2 PointNet 分类器

```
输入: (B, 3, N)
  ↓
[TNet 3x3] → 变换输入
  ↓
[共享 MLP: 3→64→64] → 局部特征
  ↓
[TNet 64x64] → 变换特征
  ↓
[共享 MLP: 64→128→1024]
  ↓
[全局最大池化] → (B, 1024)
  ↓
[FC: 1024→512→256→num_classes]
  ↓
输出: (B, num_classes)
```

### 3.3 PointNet 分割器

```
输入: (B, 3, N)
  ↓
[特征提取器] → 全局特征 (B, 1024) + 局部特征 (B, 64, N)
  ↓
[拼接] → (B, 1024+64, N)
  ↓
[共享 MLP: 1120→512→256→128→num_classes]
  ↓
输出: (B, N, num_classes)
```

## 4. 训练设计

### 4.1 损失函数

```python
# 主损失
loss = CrossEntropyLoss(logits, targets)

# 正则化损失
reg_loss = ||A * A^T - I||_F

# 总损失
total_loss = loss + alpha * reg_loss
```

### 4.2 优化策略

| 策略 | 参数 | 说明 |
|------|------|------|
| 优化器 | Adam | lr=0.001, weight_decay=1e-4 |
| 学习率调度 | StepLR | step_size=20, gamma=0.5 |
| Dropout | 0.3 | 防止过拟合 |
| BatchNorm | - | 加速收敛 |

### 4.3 训练流程

```
for epoch in range(epochs):
    # 训练阶段
    model.train()
    for points, labels in train_loader:
        logits, trans = model(points)
        loss = pointnet_loss(logits, labels, trans)
        loss.backward()
        optimizer.step()

    # 验证阶段
    model.eval()
    with torch.no_grad():
        val_loss, val_acc = evaluate(val_loader)

    # 更新学习率
    scheduler.step()
```

## 5. 可视化设计

### 5.1 可视化功能

| 功能 | 实现 | 说明 |
|------|------|------|
| 点云显示 | Matplotlib 3D | 基本 3D 散点图 |
| 分类结果 | 颜色编码 | 不同类别不同颜色 |
| 分割结果 | 部件着色 | 不同部件不同颜色 |
| 训练曲线 | 折线图 | Loss 和 Accuracy |
| 旋转 GIF | 动画 | 多角度展示 |

### 5.2 输出格式

- PNG 图片: 静态可视化
- GIF 动画: 旋转展示
- Open3D 窗口: 交互式查看

## 6. 接口设计

### 6.1 公共 API

```python
# 模型创建
model = PointNetClassifier(num_classes=10)
model = PointNetSegmentor(num_classes=4)

# 训练器
trainer = PointCloudTrainer(model, task="classification")
trainer.train(train_dataset, val_dataset, epochs=50)
trainer.predict(points)

# 可视化
visualizer = PointCloudVisualizer()
visualizer.visualize_pointcloud(points)
visualizer.visualize_segmentation_result(points, labels)
```

### 6.2 命令行接口

```bash
# 分类训练
python train.py --task classification --num_classes 10

# 分割训练
python train.py --task segmentation --num_classes 4

# 演示
python examples/classification_demo.py
python examples/segmentation_demo.py
```
