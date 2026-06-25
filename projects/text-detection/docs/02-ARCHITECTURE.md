# 02 - 架构设计

## 1. 系统架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Text Detection System                    │
├─────────────────────────────────────────────────────────────┤
│  Input Layer                                                │
│  ├── Image Preprocessing (Resize, Normalize)                │
│  └── Data Augmentation (Rotate, Crop, ColorJitter)          │
├─────────────────────────────────────────────────────────────┤
│  Model Layer                                                │
│  ├── Backbone (VGG / Light)                                │
│  │   └── Multi-scale Feature Extraction (1/2, 1/4, ..., 1/32)│
│  ├── Neck (U-Net / FPN)                                    │
│  │   └── Feature Fusion with Lateral Connections            │
│  └── Head (EAST / DB)                                      │
│      ├── Score Branch (Text Probability)                    │
│      └── Geometry Branch (Bounding Box)                     │
├─────────────────────────────────────────────────────────────┤
│  Post-processing Layer                                      │
│  ├── Score Thresholding                                     │
│  ├── Box Decoding                                           │
│  └── NMS / LANMS                                           │
├─────────────────────────────────────────────────────────────┤
│  Output Layer                                               │
│  └── Bounding Boxes + Confidence Scores                     │
└─────────────────────────────────────────────────────────────┘
```

## 2. 模块设计

### 2.1 Backbone Module

**职责**：从输入图像提取多尺度特征

```python
class VGGBackbone(nn.Module):
    """
    VGG-like backbone for feature extraction.

    Produces multi-scale feature maps at different stages:
    - Stage 1 (1/2):  64 channels
    - Stage 2 (1/4):  128 channels
    - Stage 3 (1/8):  256 channels
    - Stage 4 (1/16): 512 channels
    - Stage 5 (1/32): 512 channels
    """
```

**设计考虑**：
- 渐进式下采样：1/2 -> 1/4 -> 1/8 -> 1/16 -> 1/32
- 通道数递增：64 -> 128 -> 256 -> 512 -> 512
- BatchNorm + ReLU 激活

### 2.2 Neck Module

**职责**：融合多尺度特征

```python
class UNetNeck(nn.Module):
    """
    U-Net style feature merging neck.

    Progressively merges multi-scale features from backbone
    using upsampling and lateral connections.
    """
```

**设计考虑**：
- 自顶向下路径：从低分辨率到高分辨率
- 横向连接：保留高分辨率细节
- 特征加法融合：简单高效

### 2.3 Head Module

**职责**：预测文字区域和几何信息

```python
class EASTHead(nn.Module):
    """
    EAST detection head.

    Outputs:
        - Score map: text/non-text classification
        - Geometry map: RBOX or QUAD
    """
```

**设计考虑**：
- 共享特征层：减少计算量
- 分支预测：分数和几何独立预测
- Sigmoid 激活：输出概率

## 3. 数据流设计

### 3.1 训练数据流

```
原始图像 (H x W x 3)
    ↓
数据增强 (Rotate, Crop, ColorJitter)
    ↓
预处理 (Resize, Normalize)
    ↓
Score Map 生成 (H/4 x W/4)
    ↓
Geometry Map 生成 (5 x H/4 x W/4)
    ↓
Mask 生成
    ↓
DataLoader 批处理
    ↓
模型前向传播
    ↓
损失计算
    ↓
反向传播
```

### 3.2 推理数据流

```
输入图像
    ↓
预处理 (Resize, Normalize)
    ↓
模型前向传播
    ↓
Score Map + Geometry Map
    ↓
分数阈值过滤
    ↓
边界框解码
    ↓
NMS 去重
    ↓
输出边界框
```

## 4. 损失函数设计

### 4.1 EAST Loss

```python
class EASTLoss(nn.Module):
    """
    Loss function for EAST text detector.

    Combines:
    - Score loss: Binary Cross-Entropy
    - Geometry loss: IoU loss + Smooth L1 for angle
    """
```

**组成部分**：

1. **Score Loss** (L_score)
   ```
   L_score = BCE(pred_score, gt_score)
   ```

2. **Geometry Loss** (L_geo)
   ```
   L_geo = L_iou + L_angle
   L_iou = 1 - IoU(pred_box, gt_box)
   L_angle = SmoothL1(pred_angle, gt_angle)
   ```

3. **Total Loss**
   ```
   L_total = λ_score * L_score + λ_geo * L_geo
   ```

### 4.2 DB Loss

```python
class DBLoss(nn.Module):
    """
    Loss function for DBNet text detector.

    Combines:
    - Probability map loss: BCE + Dice
    - Threshold map loss: L1
    - Binary map loss: BCE + Dice
    """
```

## 5. 后处理设计

### 5.1 NMS (Non-Maximum Suppression)

```python
def nms(boxes, scores, threshold):
    """
    Standard NMS for axis-aligned bounding boxes.
    """
```

**算法流程**：
1. 按分数排序
2. 选择最高分的框
3. 删除 IoU > threshold 的框
4. 重复直到所有框处理完毕

### 5.2 LANMS (Locality-Aware NMS)

```python
def lanms(boxes, scores, threshold):
    """
    Locality-Aware NMS used in EAST.
    Merges overlapping boxes by averaging coordinates.
    """
```

**改进点**：
- 合并重叠框而非删除
- 平均坐标和分数
- 更适合文字检测场景

## 6. 类设计图

```
┌─────────────────┐     ┌─────────────────┐
│  VGGBackbone    │     │  LightBackbone  │
│  (backbone.py)  │     │  (backbone.py)  │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
┌────────┴────────┐     ┌────────┴────────┐
│    UNetNeck     │     │     FPNNeck     │
│    (neck.py)    │     │    (neck.py)    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
┌────────┴────────┐     ┌────────┴────────┐
│    EASTHead     │     │     DBHead      │
│    (head.py)    │     │    (head.py)    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
┌────────┴────────┐     ┌────────┴────────┐
│    EASTNet      │     │  TextDetector   │
│  (east_net.py)  │     │  (east_net.py)  │
└─────────────────┘     └─────────────────┘
```

## 7. 接口设计

### 7.1 模型接口

```python
class EASTNet(nn.Module):
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Args:
            x: Input image [B, C, H, W]
        Returns:
            {'score': [B, 1, H/4, W/4], 'geo': [B, 5, H/4, W/4]}
        """
```

### 7.2 检测器接口

```python
class TextDetector:
    def detect(self, images: torch.Tensor) -> List[Dict]:
        """
        Args:
            images: [B, C, H, W] normalized images
        Returns:
            List of {'boxes': [N, 4], 'scores': [N]}
        """
```

### 7.3 数据集接口

```python
class TextDetectionDataset(Dataset):
    def __getitem__(self, idx) -> Tuple[Tensor, Tensor, Tensor, Tensor]:
        """
        Returns:
            (image, score_map, geo_map, mask)
        """
```

## 8. 扩展性设计

### 8.1 新增 Backbone

只需继承 `nn.Module` 并实现多尺度输出接口。

### 8.2 新增检测头

只需继承 `nn.Module` 并实现 `forward` 方法。

### 8.3 新增后处理算法

在 `postprocess/` 目录下添加新模块即可。

## 9. 性能考虑

### 9.1 模型大小

| 模型 | 参数量 | 推理速度 |
|------|--------|----------|
| VGG Backbone | ~15M | 中等 |
| Light Backbone | ~2M | 快 |
| EASTNet (VGG) | ~16M | 中等 |
| EASTNet (Light) | ~3M | 快 |

### 9.2 显存占用

- 输入 512x512: ~500MB (VGG), ~200MB (Light)
- 输入 1024x1024: ~2GB (VGG), ~800MB (Light)

### 9.3 优化建议

1. 使用轻量级 backbone 减少计算量
2. 使用混合精度训练减少显存
3. 使用模型量化加速推理
