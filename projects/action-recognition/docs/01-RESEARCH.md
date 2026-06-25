# 01 - 动作识别研究调研

## 1. 问题定义

动作识别（Action Recognition）是计算机视觉的核心任务之一，目标是从视频中自动识别和分类人体动作。

### 1.1 任务分类

| 任务 | 描述 | 输入 | 输出 |
|------|------|------|------|
| 动作分类 | 对整个视频片段分类 | 视频片段 | 动作类别 |
| 时序动作检测 | 定位动作的时间区间 | 长视频 | (起始, 结束, 类别) |
| 空间-时序检测 | 定位并跟踪动作执行者 | 视频帧序列 | 边界框 + 动作 |
| 动作预测 | 预测未来动作 | 部分视频 | 未来动作类别 |

### 1.2 典型数据集

| 数据集 | 类别数 | 视频数 | 特点 |
|--------|--------|--------|------|
| UCF-101 | 101 | 13,320 | 最常用基准 |
| HMDB-51 | 51 | 6,766 | 电影片段 |
| Kinetics-400 | 400 | ~300,000 | 大规模，YouTube视频 |
| Kinetics-700 | 700 | ~650,000 | Kinetics扩展 |
| Something-Something V2 | 174 | ~220,000 | 以物体交互为主 |
| ActivityNet | 200 | ~20,000 | 长视频，时序标注 |

## 2. 核心算法

### 2.1 双流网络（Two-Stream Networks）

**核心思想**：分别处理空间信息（单帧RGB）和时间信息（光流），然后融合。

**架构**：
```
RGB帧 ──→ 空间流CNN ──→ 空间特征 ─┐
                                    ├──→ 融合 ──→ 分类
光流帧 ──→ 时间流CNN ──→ 时间特征 ─┘
```

**优点**：
- 空间流捕捉外观信息
- 时间流捕捉运动信息
- 两流互补，效果好

**缺点**：
- 需要计算光流（计算量大）
- 两流独立训练，无法端到端优化

**关键论文**：
- Simonyan & Zisserman, "Two-Stream Convolutional Networks for Action Recognition in Videos", NIPS 2014

### 2.2 3D卷积网络（C3D / I3D）

**核心思想**：使用3D卷积核直接在时空维度上提取特征。

**C3D架构**：
```
输入: (3, 16, 112, 112)  # (C, T, H, W)
  → Conv3D(64) → MaxPool3D
  → Conv3D(128) → MaxPool3D
  → Conv3D(256) × 2 → MaxPool3D
  → Conv3D(512) × 2 → MaxPool3D
  → Conv3D(512) × 2 → MaxPool3D
  → FC(4096) → FC(4096) → FC(num_classes)
```

**I3D（Inflated 3D）**：
- 将2D预训练权重"膨胀"到3D
- 结合双流思想（RGB + 光流）
- Kinetics数据集上效果显著

**关键公式**：
3D卷积操作：
$$y_{t,i,j} = \sum_{t'} \sum_{i'} \sum_{j'} w_{t',i',j'} \cdot x_{t+t', i+i', j+j'}$$

**关键论文**：
- Tran et al., "Learning Spatiotemporal Features with 3D Convolutional Networks", ICCV 2015
- Carreira & Zisserman, "Quo Vadis, Action Recognition? A New Model and the Kinetics Dataset", CVPR 2017

### 2.3 时序分段网络（TSN）

**核心思想**：从视频中均匀采样多个片段，分别提取特征后聚合。

**架构**：
```
视频 ──→ 均匀采样K个片段 ──→ 每个片段通过CNN ──→ 特征聚合 ──→ 分类
```

**关键创新**：
- 稀疏采样策略，覆盖整个视频
- 跨片段共识（consensus）机制
- 支持多种模态（RGB, 光流, RGB diff）

**聚合函数**：
$$G = g(F_1, F_2, ..., F_K)$$

常用聚合方式：
- 平均池化：$G = \frac{1}{K} \sum_{k=1}^{K} F_k$
- 最大池化：$G = \max_{k} F_k$
- 注意力加权：$G = \sum_{k=1}^{K} \alpha_k F_k$

**关键论文**：
- Wang et al., "Temporal Segment Networks: Towards Good Practices for Deep Action Recognition", ECCV 2016

### 2.4 SlowFast网络

**核心思想**：使用两条路径分别捕捉慢速（外观）和快速（运动）特征。

**架构**：
```
输入帧 ──→ Slow路径(低帧率, 大通道数) ──→ 外观特征 ──┐
                                                       ├──→ 融合 ──→ 分类
输入帧 ──→ Fast路径(高帧率, 小通道数) ──→ 运动特征 ──┘
```

**关键设计**：
- Slow路径：帧率τ=16，通道数大（捕捉静态外观）
- Fast路径：帧率τ=2，通道数小（捕捉快速运动）
- 横向连接（lateral connections）融合两路径

**关键论文**：
- Feichtenhofer et al., "SlowFast Networks for Video Recognition", ICCV 2019

### 2.5 Video Transformer

**核心思想**：将Transformer应用于视频理解，利用自注意力机制建模长距离时空依赖。

**TimeSformer架构**：
- 将视频帧分割为时空patch
- 使用不同的注意力策略：
  - Joint space-time attention
  - Divided space-time attention
  - Sparse attention

**ViViT（Video Vision Transformer）**：
- 四种时空注意力分解策略
- 更高效的计算方式

**关键论文**：
- Bertasius et al., "Is Space-Time Attention All You Need for Video Understanding?", ICML 2021
- Arnab et al., "ViViT: A Video Vision Transformer", ICCV 2021

## 3. 本项目采用的方案

### 3.1 设计选择

本项目采用 **CNN + RNN** 的经典方案：

```
视频帧 ──→ CNN(ResNet) ──→ 空间特征序列 ──→ RNN(LSTM/GRU) ──→ 时序特征 ──→ 分类器
```

**选择理由**：
1. **简单易懂**：适合学习动作识别的基本原理
2. **模块化**：空间和时序模块可独立理解和调试
3. **灵活**：可轻松替换CNN骨干或RNN类型
4. **可扩展**：可逐步添加更复杂的模块

### 3.2 与其他方案的对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| CNN+RNN（本项目） | 简单、可解释、模块化 | 难以捕捉长期依赖 | 学习、中小规模数据 |
| 3D CNN | 端到端、时空特征联合学习 | 计算量大、需要大量数据 | 大规模数据集 |
| Two-Stream | 效果好、理论清晰 | 需要光流、两流独立 | 追求精度 |
| Transformer | 长距离依赖、并行计算 | 需要大量数据和计算 | 大规模、长视频 |

## 4. 参考资源

### 4.1 关键论文
- Simonyan & Zisserman, "Two-Stream Convolutional Networks", NIPS 2014
- Tran et al., "C3D", ICCV 2015
- Wang et al., "Temporal Segment Networks", ECCV 2016
- Carreira & Zisserman, "I3D", CVPR 2017
- Feichtenhofer et al., "SlowFast", ICCV 2019
- Bertasius et al., "TimeSformer", ICML 2021

### 4.2 开源实现
- [MMAction2](https://github.com/open-mmlab/mmaction2) - OpenMMLab视频理解工具箱
- [PySlowFast](https://github.com/facebookresearch/SlowFast) - Facebook的SlowFast实现
- [VideoBERT](https://github.com/google-research/google-research/tree/master/videobert)

### 4.3 教程与课程
- [CS231N](http://cs231n.stanford.edu/) - Stanford计算机视觉课程
- [DeepMind UCL深度学习课程](https://www.deepmind.com/learning-resources)
