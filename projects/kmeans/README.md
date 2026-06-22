# K-Means 聚类

从零实现 K-Means 聚类算法，深入理解聚类原理、距离度量和肘部法则。

## 项目概述

本项目是一个学习型项目，旨在通过从零实现 K-Means 聚类算法，深入理解聚类原理和机器学习基础。

### 学习目标

- 理解聚类原理
- 掌握距离度量
- 学会肘部法则
- 实现 K-Means 聚类算法

### 技术栈

- **主语言**：Python
- **框架**：无
- **其他**：NumPy

### 核心循环

```
数据 → 初始化中心 → 分配簇 → 更新中心 → 收敛
```

## 项目结构

```
kmeans/
├── README.md              # 项目说明
├── docs/                  # 文档目录
│   ├── 01-RESEARCH.md     # 调研报告
│   ├── 02-ARCHITECTURE.md # 架构设计
│   ├── 03-IMPLEMENTATION.md # 实现细节
│   ├── 04-TESTING.md      # 测试说明
│   └── 05-DEVELOPMENT.md  # 开发记录
├── src/                   # 源代码
│   ├── __init__.py
│   ├── kmeans.py          # 核心算法
│   ├── distance.py        # 距离度量
│   ├── visualization.py   # 可视化工具
│   └── utils.py           # 工具函数
├── tests/                 # 测试代码
│   ├── __init__.py
│   ├── test_kmeans.py     # 核心算法测试
│   ├── test_distance.py   # 距离度量测试
│   └── test_visualization.py # 可视化测试
└── LEARNING_NOTES.md      # 学习笔记
```

## 功能特性

### 核心功能

- **K-Means 聚类算法**：完整的算法实现
- **多种距离度量**：欧氏距离、曼哈顿距离、余弦距离
- **K-Means++ 初始化**：更智能的初始化方法
- **肘部法则**：自动选择最优 K 值
- **可视化工具**：聚类结果可视化

### 算法特性

- 支持任意维度数据
- 可配置的收敛条件
- 多种初始化方法
- 完整的错误处理

## 安装与使用

### 依赖安装

```bash
pip install numpy matplotlib
```

### 快速开始

```python
from src import KMeans, generate_clustered_data, plot_clusters

# 生成测试数据
X, y = generate_clustered_data(n_samples=300, n_clusters=4, random_state=42)

# 创建 K-Means 模型
kmeans = KMeans(n_clusters=4, random_state=42)

# 训练模型
kmeans.fit(X)

# 获取结果
labels = kmeans.labels_
centroids = kmeans.cluster_centers_

# 可视化
plot_clusters(X, labels, centroids)
```

### 使用肘部法则

```python
from src.utils import find_optimal_k_elbow

# 寻找最优 K
optimal_k, k_range, wcss_list = find_optimal_k_elbow(X, max_k=10)
print(f"最优 K 值: {optimal_k}")

# 绘制肘部法则图
from src.visualization import plot_elbow
plot_elbow(wcss_list, k_range)
```

### 使用不同的距离度量

```python
# 欧氏距离
kmeans_euclidean = KMeans(n_clusters=4, distance='euclidean')

# 曼哈顿距离
kmeans_manhattan = KMeans(n_clusters=4, distance='manhattan')

# 余弦距离
kmeans_cosine = KMeans(n_clusters=4, distance='cosine')
```

### 使用 K-Means++ 初始化

```python
kmeans_pp = KMeans(n_clusters=4, init='kmeans++', random_state=42)
kmeans_pp.fit(X)
```

## 测试

### 运行所有测试

```bash
cd projects/kmeans
python -m pytest tests/ -v
```

### 运行特定测试

```bash
python -m pytest tests/test_kmeans.py -v
python -m pytest tests/test_distance.py -v
python -m pytest tests/test_visualization.py -v
```

## 文档

- [调研报告](docs/01-RESEARCH.md)：K-Means 算法调研
- [架构设计](docs/02-ARCHITECTURE.md)：项目架构设计
- [实现细节](docs/03-IMPLEMENTATION.md)：算法实现细节
- [测试说明](docs/04-TESTING.md)：测试用例和策略
- [开发记录](docs/05-DEVELOPMENT.md)：开发过程和心得
- [学习笔记](LEARNING_NOTES.md)：学习总结和笔记

## 学习资源

### 理论资源

- Scikit-learn 文档：K-Means 聚类
- 《机器学习》周志华 - 第 9 章
- 《Pattern Recognition and Machine Learning》

### 实践资源

- Kaggle 数据集：Iris、Wine 等
- UCI 机器学习库

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 致谢

感谢以下资源对本项目的帮助：
- Scikit-learn 文档
- NumPy 官方文档
- Matplotlib 官方文档
- 《机器学习》周志华