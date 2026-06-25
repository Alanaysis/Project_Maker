# Point Cloud Processing - 点云处理

实现 3D 点云处理，支持分类和分割，基于 PointNet 架构。

## 学习目标

- 理解点云数据结构
- 掌握 PointNet 架构
- 学会 3D 特征提取

## 核心循环

```
点云输入 → 特征提取 → 对称函数 → 分类/分割
```

## 项目结构

```
point-cloud/
├── src/
│   ├── __init__.py          # 包初始化
│   ├── pointnet.py          # PointNet 模型
│   ├── dataset.py           # 数据集加载
│   ├── trainer.py           # 模型训练器
│   ├── visualization.py     # 3D 可视化
│   └── utils.py             # 工具函数
├── tests/
│   ├── test_pointnet.py     # 模型测试
│   ├── test_dataset.py      # 数据集测试
│   └── test_utils.py        # 工具函数测试
├── docs/
│   ├── 01-RESEARCH.md       # 研究文档
│   ├── 02-DESIGN.md         # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md        # 测试文档
│   └── 05-DEVELOPMENT.md    # 开发文档
├── examples/
│   ├── classification_demo.py  # 分类演示
│   └── segmentation_demo.py    # 分割演示
├── train.py                 # 训练脚本
├── requirements.txt         # 依赖包
├── README.md                # 项目说明
└── LEARNING_NOTES.md        # 学习笔记
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行演示

```bash
# 分类演示
python examples/classification_demo.py

# 分割演示
python examples/segmentation_demo.py
```

### 训练模型

```bash
# 分类任务
python train.py --task classification --num_classes 10 --epochs 50

# 分割任务
python train.py --task segmentation --num_classes 4 --epochs 50

# 使用数据增强
python train.py --task classification --augment
```

### 运行测试

```bash
pytest tests/ -v
```

## 模型架构

### PointNet

PointNet 是一种直接处理点云的深度学习架构，核心创新点：

1. **对称函数保证排列不变性**
   - 使用最大池化作为对称函数
   - 无论点的输入顺序如何，输出相同

2. **空间变换网络 (TNet)**
   - 学习输入点云的对齐变换
   - 保证模型对刚性变换的不变性

3. **逐点特征提取**
   - 共享 MLP 对每个点独立处理
   - 提取局部特征

### 架构图

```
输入点云 (B, N, 3)
     ↓
[输入变换 TNet] → 3x3 变换矩阵
     ↓
[共享 MLP: 3→64→64]
     ↓
[特征变换 TNet] → 64x64 变换矩阵
     ↓
[共享 MLP: 64→128→1024]
     ↓
[全局最大池化] → 1024 维全局特征
     ↓
┌─────────────────┬─────────────────┐
│     分类任务     │     分割任务     │
├─────────────────┼─────────────────┤
│ [FC: 1024→512]  │ [拼接全局+局部]  │
│ [FC: 512→256]   │ [共享 MLP]      │
│ [FC: 256→C]     │ [逐点分类]      │
└─────────────────┴─────────────────┘
```

## 技术细节

### 点云数据特点

- **无序性**: 点的排列顺序不影响几何形状
- **稀疏性**: 3D 空间中的稀疏采样
- **不规则性**: 非结构化数据，无法用网格表示

### 关键技术

1. **对称函数**
   - 最大池化: `max(p1, p2, ..., pn)`
   - 保证排列不变性

2. **TNet (空间变换网络)**
   - 学习 3x3 或 64x64 变换矩阵
   - 对齐输入点云或特征

3. **共享 MLP**
   - 对每个点应用相同的卷积核
   - 参数共享，减少计算量

## 参考资料

- [PointNet 论文](https://arxiv.org/abs/1612.00593)
- [PointNet++ 论文](https://arxiv.org/abs/1706.02413)
- [Open3D 文档](http://www.open3d.org/docs/)
