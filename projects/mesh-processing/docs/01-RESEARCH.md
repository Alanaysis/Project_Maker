# 研究背景

## 网格处理概述

三角网格是 3D 计算机图形学中最常用的表面表示方法。网格处理算法在游戏、动画、CAD/CAM、3D 打印等领域有广泛应用。

## 核心算法

### 1. 网格简化

网格简化的目的是在保持整体形状的前提下减少三角形数量。

**二次误差度量 (QEM)**
- 由 Garland 和 Heckbert 于 1997 年提出
- 通过边折叠操作逐步简化网格
- 使用 4x4 对称矩阵累积误差
- 误差定义为顶点到相关平面的距离平方和

**算法流程**：
1. 为每个顶点初始化二次矩阵
2. 为每个面累加二次矩阵
3. 计算每条边的折叠代价
4. 选择代价最小的边进行折叠
5. 重复直到达到目标面数

### 2. 网格细分

细分曲面通过递归细化网格来生成光滑曲面。

**Loop 细分**
- 由 Charles Loop 于 1987 年提出
- 适用于三角形网格
- 每个三角形细分为 4 个子三角形
- 使用特定的权重模板调整顶点位置

**权重计算**：
- 旧顶点：`new_pos = (1 - n*beta) * old_pos + beta * sum(neighbors)`
- 边上新顶点：`new_pos = 3/8 * (v0 + v1) + 1/8 * (opp0 + opp1)`

### 3. 网格平滑

网格平滑用于减少噪声、改善顶点分布。

**拉普拉斯平滑**
- 将顶点向相邻顶点平均位置移动
- 简单高效，但会导致网格收缩

**Taubin 平滑**
- 交替使用正向和负向平滑
- lambda > 0 收缩，mu < 0 膨胀
- 更好地保持体积

**加权拉普拉斯平滑**
- 均匀权重：所有相邻顶点权重相同
- 面积权重：根据相邻三角形面积加权
- 余切权重：根据角度的余切值加权

## 参考文献

1. Garland, M., & Heckbert, P. S. (1997). Surface simplification using quadric error metrics.
2. Loop, C. (1987). Smooth subdivision surfaces based on triangles.
3. Taubin, G. (1995). A signal processing approach to fair surface design.
