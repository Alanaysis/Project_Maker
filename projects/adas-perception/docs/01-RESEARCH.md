# 01 - 市场调研报告

## 自动驾驶感知系统概述

### 行业背景

自动驾驶感知系统是自动驾驶技术的核心组成部分，负责理解车辆周围的环境。随着自动驾驶技术从 L2 级向 L4/L5 级发展，对感知系统的要求越来越高。

### 市场规模

- 2025年全球自动驾驶市场规模预计达到 420 亿美元
- 2030年预计达到 2 万亿美元
- 感知系统占自动驾驶系统成本的 30-40%

## 主要技术路线

### 1. 纯视觉方案 (Vision-only)

**代表企业**: Tesla

**优势**:
- 成本低，仅需摄像头
- 信息丰富，可识别颜色和纹理
- 覆盖范围广，360度视野

**劣势**:
- 缺乏深度信息
- 受光照和天气影响大
- 计算量大

### 2. LiDAR + 相机融合方案

**代表企业**: Waymo, Cruise, 百度 Apollo

**优势**:
- 精确的 3D 测距
- 不受光照影响
- 信息冗余，安全性高

**劣势**:
- LiDAR 成本高
- 点云稀疏，远距离检测困难
- 多传感器标定复杂

### 3. 4D 毫米波雷达 + 相机方案

**代表企业**: 华为, Mobileye

**优势**:
- 成本适中
- 可测速
- 不受天气影响

**劣势**:
- 角分辨率低
- 点云稀疏
- 技术成熟度较低

## 主流 3D 检测算法

### 1. PointPillars (2019)

**特点**:
- 将点云组织成柱状 (Pillars)
- 使用 2D CNN 处理伪图像
- 推理速度快

**性能**:
- KITTI Car 3D AP (Moderate): 74.31%
- 推理速度: 62 FPS

**适用场景**:
- 实时性要求高的场景
- 资源受限的嵌入式平台

### 2. SECOND (2018)

**特点**:
- 使用稀疏卷积处理 3D 体素
- 中间特征提取器
- Anchor-based 检测头

**性能**:
- KITTI Car 3D AP (Moderate): 76.48%
- 推理速度: 20 FPS

**适用场景**:
- 需要高精度的场景
- 服务器端部署

### 3. PointRCNN (2019)

**特点**:
- 两阶段检测器
- 第一阶段: 前景点分割和边界框生成
- 第二阶段: 边界框精炼

**性能**:
- KITTI Car 3D AP (Moderate): 78.70%
- 推理速度: 10 FPS

**适用场景**:
- 高精度要求的场景
- 研究用途

### 4. PV-RCNN (2020)

**特点**:
- 结合体素和点的特征
- 关键点集合抽象
- 两阶段精炼

**性能**:
- KITTI Car 3D AP (Moderate): 83.90%
- 推理速度: 8 FPS

**适用场景**:
- 最高精度要求
- 学术研究

### 5. CenterPoint (2021)

**特点**:
- 基于中心点的检测
- 无需 Anchor
- 可扩展到跟踪任务

**性能**:
- Waymo 3D AP (Moderate): 72.1%
- 推理速度: 15 FPS

**适用场景**:
- 多任务学习
- 目标跟踪

## 数据集对比

### 1. KITTI

**规模**:
- 训练集: 7481 帧
- 验证集: 7518 帧
- 测试集: 7518 帧

**类别**:
- Car, Pedestrian, Cyclist
- Van, Truck, Tram
- Misc, DontCare

**特点**:
- 最早的自动驾驶数据集
- 评测标准广泛使用
- 数据量较小

### 2. nuScenes

**规模**:
- 1000 个场景
- 1.4M 帧图像
- 400K 帧点云

**类别**:
- 23 个类别
- 更细粒度的标注

**特点**:
- 数据量大
- 包含雷达数据
- 360度视野

### 3. Waymo Open Dataset

**规模**:
- 1150 个场景
- 230K 帧点云
- 12M 3D 标注

**类别**:
- Vehicle, Pedestrian, Cyclist, Sign

**特点**:
- 数据量最大
- 高质量标注
- 多传感器数据

### 4. Argoverse

**规模**:
- 113 个场景
- 330K 帧点云

**类别**:
- 15 个类别

**特点**:
- 包含高精地图
- 支持运动预测
- 众包采集

## 关键技术挑战

### 1. 点云稀疏性

**问题**:
- 远距离点云稀疏
- 小目标检测困难
- 特征提取困难

**解决方案**:
- 稀疏卷积 (Sparse Convolution)
- 点云增强 (Point Cloud Augmentation)
- 多帧融合 (Multi-frame Fusion)

### 2. 实时性要求

**问题**:
- 自动驾驶需要实时处理
- 计算资源受限
- 延迟敏感

**解决方案**:
- 轻量化模型设计
- 模型压缩和量化
- 硬件加速 (GPU, NPU)

### 3. 多传感器融合

**问题**:
- 传感器标定误差
- 时间同步困难
- 数据格式不一致

**解决方案**:
- 在线标定算法
- 时间戳对齐
- 特征级融合

### 4. 长尾分布

**问题**:
- 罕见类别样本少
- 极端场景覆盖不足
- 泛化能力差

**解决方案**:
- 数据增强
- 迁移学习
- 合成数据

## 未来发展趋势

### 1. 端到端感知

- 从传感器直接到决策
- 减少模块间误差传播
- 端到端学习优化

### 2. 4D 感知

- 时序信息融合
- 动态目标跟踪
- 运动预测

### 3. 自监督学习

- 减少标注需求
- 利用大量无标注数据
- 对比学习

### 4. 神经辐射场 (NeRF)

- 3D 场景重建
- 新视角合成
- 数据增强

## 本项目的技术选型

基于以上调研，本项目选择：

1. **检测算法**: PointPillars
   - 原因: 推理速度快，适合实时应用
   - 优势: 结构简单，易于理解和实现

2. **数据集**: KITTI
   - 原因: 最广泛使用的基准数据集
   - 优势: 评测标准成熟，便于对比

3. **框架**: PyTorch
   - 原因: 灵活性好，社区活跃
   - 优势: 易于调试和扩展

4. **可视化**: Open3D
   - 原因: 功能强大，API 友好
   - 优势: 支持多种 3D 数据格式

## 参考资源

### 学术论文

1. Lang, A. H., et al. (2019). PointPillars: Fast Encoders for Object Detection from Point Clouds. CVPR.
2. Shi, S., et al. (2019). PV-RCNN: Point-Voxel Feature Set Abstraction for 3D Object Detection. CVPR.
3. Yin, T., et al. (2021). Center-based 3D Object Detection and Tracking. CVPR.

### 开源项目

1. OpenPCDet: https://github.com/open-mmlab/OpenPCDet
2. mmdetection3d: https://github.com/open-mmlab/mmdetection3d
3. second.pytorch: https://github.com/traveller59/second.pytorch

### 数据集

1. KITTI: https://www.cvlibs.net/datasets/kitti/
2. nuScenes: https://www.nuscenes.org/
3. Waymo Open Dataset: https://waymo.com/open/
