"""
点云处理工具函数

包含点云预处理、采样、距离计算等常用函数。
"""

import torch
import numpy as np


def normalize_pointcloud(points):
    """
    归一化点云到单位球

    Args:
        points: (N, 3) 或 (B, N, 3) 点云坐标

    Returns:
        normalized_points: 归一化后的点云
    """
    if isinstance(points, np.ndarray):
        centroid = np.mean(points, axis=-2, keepdims=True)
        points = points - centroid
        max_dist = np.max(np.sqrt(np.sum(points ** 2, axis=-1, keepdims=True)), axis=-2, keepdims=True)
        points = points / max_dist
    else:
        centroid = torch.mean(points, dim=-2, keepdim=True)
        points = points - centroid
        max_dist = torch.max(torch.sqrt(torch.sum(points ** 2, dim=-1, keepdim=True)), dim=-2, keepdim=True)[0]
        points = points / max_dist

    return points


def farthest_point_sample(points, num_samples):
    """
    最远点采样 (Farthest Point Sampling, FPS)

    迭代选择距离已选点集最远的点，保证采样点的均匀分布。

    Args:
        points: (B, N, 3) 点云坐标
        num_samples: 采样点数

    Returns:
        indices: (B, num_samples) 采样点索引
    """
    batch_size, num_points, _ = points.shape
    device = points.device

    # 初始化
    indices = torch.zeros(batch_size, num_samples, dtype=torch.long, device=device)
    distances = torch.full((batch_size, num_points), float('inf'), device=device)

    # 随机选择第一个点
    farthest = torch.randint(0, num_points, (batch_size,), device=device)

    for i in range(num_samples):
        indices[:, i] = farthest

        # 获取当前点
        current_point = points[torch.arange(batch_size), farthest].unsqueeze(1)

        # 计算距离
        dist = torch.sum((points - current_point) ** 2, dim=-1)

        # 更新最小距离
        distances = torch.min(distances, dist)

        # 选择最远点
        farthest = torch.argmax(distances, dim=-1)

    return indices


def compute_normals(points, k=20):
    """
    计算点云法向量

    使用 k 近邻的主成分分析 (PCA) 估计法向量。

    Args:
        points: (N, 3) 点云坐标
        k: 近邻数

    Returns:
        normals: (N, 3) 法向量
    """
    if isinstance(points, torch.Tensor):
        points = points.cpu().numpy()

    from scipy.spatial import KDTree

    n = points.shape[0]
    normals = np.zeros_like(points)

    tree = KDTree(points)

    for i in range(n):
        # 查询 k 近邻
        _, nn_indices = tree.query(points[i], k=k)
        neighbors = points[nn_indices]

        # 计算协方差矩阵
        centroid = np.mean(neighbors, axis=0)
        cov = np.cov((neighbors - centroid).T)

        # 特征分解
        eigenvalues, eigenvectors = np.linalg.eigh(cov)

        # 最小特征值对应的特征向量即为法向量
        normals[i] = eigenvectors[:, 0]

    return normals


def random_sample_points(points, num_samples):
    """
    随机采样点云

    Args:
        points: (N, 3) 点云坐标
        num_samples: 采样点数

    Returns:
        sampled_points: (num_samples, 3) 采样后的点云
    """
    n = points.shape[0]

    if n >= num_samples:
        indices = np.random.choice(n, num_samples, replace=False)
    else:
        indices = np.random.choice(n, num_samples, replace=True)

    return points[indices]


def compute_point_cloud_distance(source, target):
    """
    计算点云之间的距离 (Chamfer Distance)

    Args:
        source: (N, 3) 源点云
        target: (M, 3) 目标点云

    Returns:
        dist: Chamfer 距离
    """
    if isinstance(source, np.ndarray):
        source = torch.FloatTensor(source)
        target = torch.FloatTensor(target)

    # 计算所有点对之间的距离
    diff = source.unsqueeze(1) - target.unsqueeze(0)  # (N, M, 3)
    dist_matrix = torch.sum(diff ** 2, dim=-1)  # (N, M)

    # Chamfer 距离
    dist_s2t = torch.min(dist_matrix, dim=1)[0]  # source 到 target
    dist_t2s = torch.min(dist_matrix, dim=0)[0]  # target 到 source

    chamfer_dist = torch.mean(dist_s2t) + torch.mean(dist_t2s)

    return chamfer_dist.item()


def voxel_downsample(points, voxel_size=0.05):
    """
    体素下采样

    Args:
        points: (N, 3) 点云坐标
        voxel_size: 体素大小

    Returns:
        downsampled_points: 下采样后的点云
    """
    if isinstance(points, torch.Tensor):
        points = points.cpu().numpy()

    # 计算体素索引
    voxel_indices = np.floor(points / voxel_size).astype(int)

    # 使用字典去重
    voxel_dict = {}
    for i, idx in enumerate(voxel_indices):
        key = tuple(idx)
        if key not in voxel_dict:
            voxel_dict[key] = i

    # 提取去重后的点
    selected_indices = list(voxel_dict.values())
    downsampled_points = points[selected_indices]

    return downsampled_points
