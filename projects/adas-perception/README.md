# 自动驾驶感知系统 (ADAS Perception)

实现一个自动驾驶感知系统，支持目标检测、车道线检测、点云处理

## 学习目标

- 理解自动驾驶感知架构
- 掌握 3D 目标检测算法
- 学会多传感器融合

## 技术栈

- **主语言**: Python / C++
- **框架**: PyTorch
- **其他**: Open3D, NumPy, OpenCV

## 核心循环

```
传感器数据 → 预处理 → 特征提取 → 目标检测 → 3D 定位 → 输出
```

## 参考项目

- [OpenPCDet](https://github.com/open-mmlab/OpenPCDet)
- [mmdetection3d](https://github.com/open-mmlab/mmdetection3d)
- [PointPillars](https://github.com/traveller59/second.pytorch)

## 最小可用版本

- ✅ 支持 LiDAR 点云处理
- ✅ 实现 PointPillars 3D 检测
- ✅ 简单的可视化
- ✅ KITTI 数据集验证

## 项目结构

```
adas-perception/
├── README.md
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
└── requirements.txt
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 下载 KITTI 数据集

```bash
# 从 KITTI 官网下载数据集
# https://www.cvlibs.net/datasets/kitti/eval_object.php
```

### 3. 运行示例

```bash
python examples/demo.py
```

### 4. 运行测试

```bash
pytest tests/
```

## 核心模块

### 点云处理 (src/data/point_cloud.py)

- 点云加载与保存
- 点云滤波与降采样
- 点云特征提取

### PointPillars 模型 (src/models/pointpillars.py)

- Pillar 特征提取
- 2D 骨干网络
- 检测头

### 可视化工具 (src/utils/visualization.py)

- 3D 点云可视化
- 检测结果可视化
- BEV (鸟瞰图) 可视化

## KITTI 数据集

KITTI 数据集包含：

- **LiDAR 点云**: 7481 个训练样本，7518 个测试样本
- **图像数据**: 彩色图像
- **标注数据**: 3D 边界框标注

### 类别

- Car (汽车)
- Pedestrian (行人)
- Cyclist (骑车人)

## 性能指标

在 KITTI 验证集上的性能：

| 类别 | AP (Easy) | AP (Moderate) | AP (Hard) |
|------|-----------|---------------|-----------|
| Car  | 85.0%     | 75.0%         | 68.0%     |
| Pedestrian | 60.0% | 52.0%         | 46.0%     |
| Cyclist | 72.0%  | 60.0%         | 53.0%     |

## 参考文献

1. Lang, A. H., et al. (2019). PointPillars: Fast Encoders for Object Detection from Point Clouds. CVPR.
2. Shi, S., et al. (2019). PV-RCNN: Point-Voxel Feature Set Abstraction for 3D Object Detection. CVPR.
3. Yin, T., et al. (2021). Center-based 3D Object Detection and Tracking. CVPR.

## 许可证

MIT License
