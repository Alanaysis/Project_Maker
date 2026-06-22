# 02 - 系统架构设计

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    自动驾驶感知系统                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  LiDAR 数据  │    │  相机数据    │    │  雷达数据    │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 数据预处理层                          │   │
│  │  - 点云滤波与降采样                                   │   │
│  │  - 图像预处理                                         │   │
│  │  - 多传感器时间同步                                   │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                        │                                    │
│                        ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 特征提取层                            │   │
│  │  - PointPillars 编码器                               │   │
│  │  - 2D 骨干网络                                       │   │
│  │  - FPN 特征融合                                      │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                        │                                    │
│                        ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 检测头层                              │   │
│  │  - 分类预测                                          │   │
│  │  - 边界框回归                                        │   │
│  │  - 方向预测                                          │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                        │                                    │
│                        ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 后处理层                              │   │
│  │  - NMS (非极大值抑制)                                 │   │
│  │  - 坐标变换                                          │   │
│  │  - 置信度过滤                                        │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                        │                                    │
│                        ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 输出层                                │   │
│  │  - 3D 边界框                                         │   │
│  │  - 类别标签                                          │   │
│  │  - 置信度分数                                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 核心模块设计

### 1. 数据模块 (src/data/)

#### PointCloud 类

```python
class PointCloud:
    """点云数据类，封装点云的基本操作"""
    
    def __init__(self, points: np.ndarray):
        """
        Args:
            points: (N, C) 数组，C 通常是 4 (x, y, z, intensity)
        """
        self.points = points
    
    def filter_by_range(self, x_range, y_range, z_range):
        """按范围过滤点云"""
        pass
    
    def downsample(self, voxel_size):
        """体素降采样"""
        pass
    
    def remove_ground(self):
        """地面点去除"""
        pass
```

#### KITTILoader 类

```python
class KITTILoader:
    """KITTI 数据集加载器"""
    
    def __init__(self, root_dir, split='training'):
        """
        Args:
            root_dir: KITTI 数据集根目录
            split: 'training' 或 'testing'
        """
        self.root_dir = root_dir
        self.split = split
    
    def load_point_cloud(self, idx):
        """加载点云数据"""
        pass
    
    def load_labels(self, idx):
        """加载标注数据"""
        pass
    
    def load_calibration(self, idx):
        """加载标定数据"""
        pass
```

### 2. 模型模块 (src/models/)

#### PointPillars 模型架构

```
输入: (N, C) 点云数据
        │
        ▼
┌─────────────────────────────────┐
│      PointPillars 编码器         │
│  - 将点云组织成 Pillars          │
│  - 学习 Pillar 特征              │
│  - 输出: 伪图像 (D, H, W)      │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│      2D 骨干网络                 │
│  - 多尺度特征提取                │
│  - 下采样和上采样                │
│  - 输出: 多尺度特征图           │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│      检测头                      │
│  - 分类分支                     │
│  - 回归分支                     │
│  - 方向分支                     │
└────────────────┬────────────────┘
                 │
                 ▼
输出: 3D 边界框、类别、置信度
```

#### PointPillars 编码器

```python
class PillarEncoder(nn.Module):
    """PointPillars 编码器"""
    
    def __init__(self, 
                 voxel_size: List[float],
                 point_cloud_range: List[float],
                 max_points_per_pillar: int = 32,
                 max_pillars: int = 12000):
        super().__init__()
        self.voxel_size = voxel_size
        self.point_cloud_range = point_cloud_range
        self.max_points_per_pillar = max_points_per_pillar
        self.max_pillars = max_pillars
    
    def forward(self, points):
        """
        Args:
            points: (B, N, C) 点云数据
        Returns:
            pillars: (B, D, H, W) 伪图像
        """
        pass
```

#### 2D 骨干网络

```python
class Backbone2D(nn.Module):
    """2D 骨干网络"""
    
    def __init__(self, in_channels: int):
        super().__init__()
        self.block1 = self._make_block(in_channels, 64, num_blocks=2)
        self.block2 = self._make_block(64, 128, num_blocks=2)
        self.block3 = self._make_block(128, 256, num_blocks=2)
    
    def _make_block(self, in_channels, out_channels, num_blocks):
        """创建卷积块"""
        pass
    
    def forward(self, x):
        """前向传播"""
        pass
```

#### 检测头

```python
class DetectionHead(nn.Module):
    """检测头"""
    
    def __init__(self, 
                 in_channels: int,
                 num_classes: int,
                 num_anchors: int):
        super().__init__()
        self.num_classes = num_classes
        self.num_anchors = num_anchors
        
        # 分类分支
        self.cls_head = nn.Conv2d(
            in_channels, num_anchors * num_classes, 
            kernel_size=1
        )
        
        # 回归分支
        self.reg_head = nn.Conv2d(
            in_channels, num_anchors * 7,
            kernel_size=1
        )
        
        # 方向分支
        self.dir_head = nn.Conv2d(
            in_channels, num_anchors * 2,
            kernel_size=1
        )
    
    def forward(self, x):
        """
        Args:
            x: (B, C, H, W) 特征图
        Returns:
            cls_score: (B, A*num_classes, H, W) 分类分数
            bbox_pred: (B, A*7, H, W) 边界框预测
            dir_pred: (B, A*2, H, W) 方向预测
        """
        pass
```

### 3. 工具模块 (src/utils/)

#### 可视化工具

```python
class Visualizer:
    """可视化工具类"""
    
    def __init__(self):
        pass
    
    def visualize_point_cloud(self, points, 
                              point_size=2.0,
                              background_color=[0, 0, 0]):
        """可视化点云"""
        pass
    
    def visualize_boxes3d(self, boxes, 
                          color=(0, 1, 0),
                          line_width=2):
        """可视化 3D 边界框"""
        pass
    
    def visualize_bev(self, points, boxes=None,
                      bev_range=(-50, 50, -50, 50),
                      resolution=0.1):
        """可视化鸟瞰图"""
        pass
```

#### 数据变换工具

```python
class PointCloudTransforms:
    """点云数据变换"""
    
    @staticmethod
    def random_flip(points, boxes, prob=0.5):
        """随机翻转"""
        pass
    
    @staticmethod
    def random_rotation(points, boxes, range=(-0.78, 0.78)):
        """随机旋转"""
        pass
    
    @staticmethod
    def random_scaling(points, boxes, range=(0.95, 1.05)):
        """随机缩放"""
        pass
    
    @staticmethod
    def random_translation(points, boxes, std=(0.2, 0.2, 0.2)):
        """随机平移"""
        pass
```

## 数据流设计

### 训练流程

```
1. 数据加载
   ├── 加载点云
   ├── 加载标注
   └── 加载标定参数

2. 数据预处理
   ├── 点云范围过滤
   ├── 地面点去除
   └── 点云增强 (随机翻转、旋转、缩放)

3. 特征提取
   ├── PointPillars 编码
   │   ├── 点云 → Pillars
   │   ├── Pillar 特征学习
   │   └── 伪图像生成
   └── 2D 骨干网络
       ├── 多尺度特征提取
       └── 特征金字塔网络

4. 检测头
   ├── 分类预测
   ├── 边界框回归
   └── 方向预测

5. 损失计算
   ├── 分类损失 (Focal Loss)
   ├── 回归损失 (Smooth L1)
   └── 方向损失 (Cross Entropy)

6. 反向传播
   └── 梯度更新
```

### 推理流程

```
1. 数据输入
   └── 加载点云

2. 数据预处理
   └── 点云范围过滤

3. 特征提取
   ├── PointPillars 编码
   └── 2D 骨干网络

4. 检测头
   └── 预测结果

5. 后处理
   ├── NMS (非极大值抑制)
   ├── 置信度过滤
   └── 坐标变换

6. 输出
   └── 3D 边界框、类别、置信度
```

## 关键设计决策

### 1. 为什么选择 PointPillars？

- **推理速度快**: 62 FPS，满足实时性要求
- **结构简单**: 易于理解和实现
- **资源消耗低**: 适合嵌入式部署

### 2. 为什么选择 KITTI 数据集？

- **基准数据集**: 最广泛使用的评测基准
- **评测标准成熟**: 便于与其他方法对比
- **数据量适中**: 适合快速实验

### 3. 为什么选择 PyTorch？

- **灵活性好**: 易于调试和修改
- **社区活跃**: 丰富的资源和教程
- **生态完善**: 大量预训练模型和工具

### 4. 为什么选择 Open3D？

- **功能强大**: 支持多种 3D 数据格式
- **API 友好**: 易于使用
- **性能优化**: 底层使用 C++ 实现

## 扩展性设计

### 1. 多传感器融合

```
LiDAR 点云 ──┐
              ├──→ 特征融合 ──→ 检测头
相机图像 ────┘
```

### 2. 多任务学习

```
共享特征 ──┬──→ 3D 检测
           ├──→ 语义分割
           └──→ 目标跟踪
```

### 3. 模型集成

```
模型 A ──┐
         ├──→ 结果融合 ──→ 最终输出
模型 B ──┘
```

## 性能优化策略

### 1. 计算优化

- 使用 CUDA 加速
- 模型量化 (INT8)
- 模型剪枝

### 2. 内存优化

- 梯度累积
- 混合精度训练
- 数据流式加载

### 3. 推理优化

- TensorRT 加速
- 批量推理
- 异步处理

## 部署架构

### 嵌入式平台

```
传感器 ──→ 数据采集 ──→ 感知算法 ──→ 决策规划 ──→ 控制执行
           │              │
           └──────────────┘
              (实时反馈)
```

### 云端平台

```
传感器 ──→ 数据上传 ──→ 云端处理 ──→ 结果下发 ──→ 车端执行
           │              │
           └──────────────┘
              (离线优化)
```

## 参考资料

1. Lang, A. H., et al. (2019). PointPillars: Fast Encoders for Object Detection from Point Clouds. CVPR.
2. OpenPCDet: https://github.com/open-mmlab/OpenPCDet
3. mmdetection3d: https://github.com/open-mmlab/mmdetection3d
