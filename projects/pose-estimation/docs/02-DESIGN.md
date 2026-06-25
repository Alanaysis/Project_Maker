# 架构设计 - 人体姿态估计

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    人体姿态估计系统                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐ │
│  │  数据集   │───→│  骨干网络 │───→│ 热力图头 │───→│ 关键点 │ │
│  │ Dataset  │    │ Backbone │    │  Head    │    │ 解码   │ │
│  └──────────┘    └──────────┘    └──────────┘    └────────┘ │
│       │               │               │               │     │
│       ▼               ▼               ▼               ▼     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐ │
│  │ 数据增强 │    │ 特征提取 │    │ 损失计算 │    │ 可视化 │ │
│  │Augment   │    │ Features │    │  Loss    │    │  Viz   │ │
│  └──────────┘    └──────────┘    └──────────┘    └────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 模块设计

### 1. 模型模块 (`model.py`)

```
PoseEstimationNet
├── LightweightBackbone
│   ├── stem (Conv + BN + ReLU + MaxPool)
│   ├── layer1 (Conv + ResidualBlock)
│   ├── layer2 (Conv + ResidualBlock)
│   └── layer3 (Conv + ResidualBlock)
└── HeatmapHead
    ├── deconv1 (ConvTranspose + BN + ReLU)
    ├── deconv2 (ConvTranspose + BN + ReLU)
    └── final (Conv 1x1)
```

**类设计**:

```python
class ConvBlock(nn.Module):
    """卷积 + BN + ReLU"""
    
class ResidualBlock(nn.Module):
    """残差块"""
    
class LightweightBackbone(nn.Module):
    """轻量级骨干网络"""
    
class HeatmapHead(nn.Module):
    """热力图预测头"""
    
class PoseEstimationNet(nn.Module):
    """完整的姿态估计网络"""
```

### 2. 热力图模块 (`heatmap.py`)

```
heatmap.py
├── generate_heatmaps()      # 生成高斯热力图
├── heatmaps_to_keypoints()  # argmax 提取关键点
├── soft_argmax()            # 可微的关键点提取
├── decode_heatmap_batch()   # 批量解码
└── resize_heatmaps()        # 调整热力图尺寸
```

### 3. 损失函数模块 (`loss.py`)

```
loss.py
├── KeypointMSELoss       # MSE 损失
├── KeypointOHKMLoss      # OHKM 损失
└── CombinedPoseLoss      # 组合损失
```

### 4. 关键点模块 (`keypoints.py`)

```
keypoints.py
├── KEYPOINT_NAMES         # 关键点名称
├── SKELETON_CONNECTIONS   # 骨骼连接
├── extract_keypoints()    # 关键点提取
├── decode_predictions()   # 预测解码
└── compute_pck()          # PCK 评估
```

### 5. 数据集模块 (`dataset.py`)

```
dataset.py
├── SyntheticPoseDataset   # 合成数据集
└── create_dataloader()    # 创建数据加载器
```

### 6. 工具模块 (`utils.py`)

```
utils.py
├── draw_skeleton()        # 绘制骨骼
├── visualize_pose()       # 姿态可视化
├── normalize_keypoints()  # 归一化
├── denormalize_keypoints() # 反归一化
└── compute_oks()          # OKS 计算
```

## 数据流

### 训练流程

```
输入图像 (B, 3, H, W)
    │
    ▼
骨干网络 (LightweightBackbone)
    │
    ▼
特征图 (B, 256, H/4, W/4)
    │
    ▼
热力图头 (HeatmapHead)
    │
    ▼
预测热力图 (B, K, H', W')
    │
    ▼
损失计算 (KeypointMSELoss)
    │
    ▼
反向传播
```

### 推理流程

```
输入图像 (B, 3, H, W)
    │
    ▼
骨干网络
    │
    ▼
热力图头
    │
    ▼
预测热力图 (B, K, H', W')
    │
    ▼
关键点提取 (argmax / soft-argmax)
    │
    ▼
关键点坐标 (B, K, 2)
    │
    ▼
可视化
```

## 接口设计

### 模型接口

```python
class PoseEstimationNet(nn.Module):
    def forward(self, x: Tensor) -> Tensor:
        """前向传播，返回热力图"""
        
    def predict_keypoints(self, x: Tensor, threshold: float) -> Tuple[Tensor, Tensor]:
        """预测关键点坐标"""
```

### 损失函数接口

```python
class KeypointMSELoss(nn.Module):
    def forward(
        self,
        pred_heatmaps: Tensor,
        target_heatmaps: Tensor,
        target_weights: Optional[Tensor] = None,
    ) -> Dict[str, Tensor]:
        """计算损失，返回损失字典"""
```

### 数据集接口

```python
class SyntheticPoseDataset(Dataset):
    def __getitem__(self, idx: int) -> Dict[str, Tensor]:
        """
        返回:
            - image: (3, H, W) 图像
            - keypoints: (K, 2) 关键点
            - weights: (K,) 权重
            - heatmaps: (K, H', W') 热力图
        """
```

## 设计决策

### 1. 使用热力图回归而非直接回归

**原因**:
- 精度更高
- 可以表达不确定性
- 是目前主流方法

### 2. 使用轻量级骨干网络

**原因**:
- 学习项目，不需要过重的模型
- 便于理解和调试
- 训练速度快

### 3. 使用 MSE 损失

**原因**:
- 简单有效
- 是热力图回归的标准损失
- 易于理解和实现

### 4. 支持多种关键点提取方法

**原因**:
- argmax 简单快速
- soft-argmax 可微，适合端到端训练
- 亚像素精度更高
