"""
PSO 用于特征选择

使用粒子群优化算法选择最优特征子集，提高机器学习模型性能。

特点：
- 二进制 PSO：粒子位置表示特征选择（0/1）
- 多目标优化：平衡特征数量和模型性能
- 适用于高维数据
"""

import numpy as np
from typing import Callable, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FeatureSelectionConfig:
    """特征选择配置"""

    # 特征选择参数（必须在默认参数之前）
    n_features: int  # 总特征数

    # PSO 参数
    n_particles: int = 30
    max_iterations: int = 100
    w: float = 0.7
    c1: float = 1.5
    c2: float = 1.5

    # 特征选择约束
    min_features: int = 1  # 最少选择的特征数
    max_features: Optional[int] = None  # 最多选择的特征数

    # 适应度权重
    accuracy_weight: float = 0.9  # 准确率权重
    feature_weight: float = 0.1  # 特征数量惩罚权重

    # 其他
    random_seed: Optional[int] = None


class BinaryPSO:
    """
    二进制粒子群优化

    用于离散优化问题，粒子位置通过 sigmoid 函数转换为二进制值。
    """

    def __init__(self, config: FeatureSelectionConfig):
        """初始化二进制 PSO"""
        self.config = config
        self._rng = np.random.default_rng(config.random_seed)

        if config.max_features is None:
            self.config.max_features = config.n_features

        # 初始化粒子（连续值）
        self.positions = self._rng.uniform(-4, 4, size=(config.n_particles, config.n_features))
        self.velocities = self._rng.uniform(-1, 1, size=(config.n_particles, config.n_features))

        # 个体最佳
        self.personal_best_positions = self.positions.copy()
        self.personal_best_fitness = np.full(config.n_particles, float("inf"))

        # 全局最佳
        self.global_best_position: Optional[np.ndarray] = None
        self.global_best_fitness: float = float("inf")

        # 历史记录
        self.convergence_history: list[float] = []

    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid 函数，将连续值转换为概率"""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

    def _to_binary(self, positions: np.ndarray) -> np.ndarray:
        """
        将连续位置转换为二进制选择

        使用 sigmoid 函数将位置值转换为选择概率，然后根据概率随机选择。

        参数:
            positions: 连续位置值

        返回:
            二进制选择矩阵（0 或 1）
        """
        probabilities = self._sigmoid(positions)
        random_values = self._rng.uniform(0, 1, size=positions.shape)
        return (probabilities > random_values).astype(int)

    def _evaluate_particle(
        self,
        binary_position: np.ndarray,
        fitness_function: Callable,
    ) -> float:
        """
        评估单个粒子

        参数:
            binary_position: 二进制特征选择
            fitness_function: 适应度函数

        返回:
            适应度值
        """
        # 检查特征数量约束
        n_selected = np.sum(binary_position)

        if n_selected < self.config.min_features:
            # 特征太少，惩罚
            return float("inf")

        if n_selected > self.config.max_features:
            # 特征太多，惩罚
            return float("inf")

        if n_selected == 0:
            return float("inf")

        # 计算适应度
        return fitness_function(binary_position)

    def optimize(
        self,
        fitness_function: Callable,
        verbose: bool = False,
        callback: Optional[Callable] = None,
    ) -> dict:
        """
        执行二进制 PSO 优化

        参数:
            fitness_function: 适应度函数，接受二进制向量，返回适应度值
            verbose: 是否打印进度
            callback: 回调函数

        返回:
            优化结果字典
        """
        for iteration in range(self.config.max_iterations):
            # 评估所有粒子
            for i in range(self.config.n_particles):
                binary_position = self._to_binary(self.positions[i])
                fitness = self._evaluate_particle(binary_position, fitness_function)

                # 更新个体最佳
                if fitness < self.personal_best_fitness[i]:
                    self.personal_best_fitness[i] = fitness
                    self.personal_best_positions[i] = self.positions[i].copy()

                # 更新全局最佳
                if fitness < self.global_best_fitness:
                    self.global_best_fitness = fitness
                    self.global_best_position = self.positions[i].copy()

            self.convergence_history.append(self.global_best_fitness)

            # 更新速度和位置
            r1 = self._rng.uniform(0, 1, size=(self.config.n_particles, self.config.n_features))
            r2 = self._rng.uniform(0, 1, size=(self.config.n_particles, self.config.n_features))

            self.velocities = (
                self.config.w * self.velocities
                + self.config.c1 * r1 * (self.personal_best_positions - self.positions)
                + self.config.c2 * r2 * (self.global_best_position - self.positions)
            )

            self.positions = self.positions + self.velocities

            # 位置限制
            self.positions = np.clip(self.positions, -4, 4)

            # 回调
            if callback:
                binary_best = self._to_binary(self.global_best_position)
                callback(iteration, self.global_best_fitness, binary_best)

            # 打印进度
            if verbose and (iteration + 1) % 10 == 0:
                binary_best = self._to_binary(self.global_best_position)
                n_selected = np.sum(binary_best)
                print(
                    f"迭代 {iteration + 1}: "
                    f"适应度={self.global_best_fitness:.6f}, "
                    f"选择特征数={n_selected}"
                )

        # 获取最终结果
        best_binary = self._to_binary(self.global_best_position)

        return {
            "best_position": best_binary,
            "best_fitness": self.global_best_fitness,
            "iterations": len(self.convergence_history),
            "convergence_history": self.convergence_history,
            "n_selected_features": int(np.sum(best_binary)),
            "selected_feature_indices": np.where(best_binary == 1)[0].tolist(),
        }


class FeatureSelector:
    """
    特征选择器

    使用 PSO 进行特征选择，支持自定义评估函数。
    """

    def __init__(self, config: FeatureSelectionConfig):
        """
        初始化特征选择器

        参数:
            config: 特征选择配置
        """
        self.config = config
        self._binary_pso = BinaryPSO(config)

    def _create_fitness_function(
        self,
        X: np.ndarray,
        y: np.ndarray,
        evaluator: Callable,
    ) -> Callable:
        """
        创建适应度函数

        参数:
            X: 特征矩阵
            y: 标签
            evaluator: 评估函数，接受 (X_selected, y)，返回准确率

        返回:
            适应度函数
        """
        def fitness_function(binary_mask: np.ndarray) -> float:
            # 选择特征
            selected_indices = np.where(binary_mask == 1)[0]

            if len(selected_indices) == 0:
                return float("inf")

            X_selected = X[:, selected_indices]

            # 评估模型
            accuracy = evaluator(X_selected, y)

            # 计算适应度（最小化）
            n_features = len(selected_indices)
            n_total = self.config.n_features

            # 适应度 = -accuracy + 特征数量惩罚
            fitness = (
                -self.config.accuracy_weight * accuracy
                + self.config.feature_weight * (n_features / n_total)
            )

            return fitness

        return fitness_function

    def select(
        self,
        X: np.ndarray,
        y: np.ndarray,
        evaluator: Callable,
        verbose: bool = False,
    ) -> dict:
        """
        执行特征选择

        参数:
            X: 特征矩阵，形状 (n_samples, n_features)
            y: 标签
            evaluator: 评估函数，接受 (X_selected, y)，返回准确率
            verbose: 是否打印进度

        返回:
            特征选择结果
        """
        # 创建适应度函数
        fitness_function = self._create_fitness_function(X, y, evaluator)

        # 运行优化
        result = self._binary_pso.optimize(fitness_function, verbose=verbose)

        # 计算最终准确率
        selected_indices = result["selected_feature_indices"]
        X_selected = X[:, selected_indices]
        final_accuracy = evaluator(X_selected, y)

        result["final_accuracy"] = final_accuracy
        result["X_selected"] = X_selected

        return result


def simple_cross_validation_accuracy(
    X: np.ndarray,
    y: np.ndarray,
    n_folds: int = 5,
) -> float:
    """
    简单的交叉验证准确率评估

    使用简单的阈值分类器进行评估。

    参数:
        X: 特征矩阵
        y: 标签
        n_folds: 折数

    返回:
        平均准确率
    """
    n_samples = len(X)
    fold_size = n_samples // n_folds
    accuracies = []

    for fold in range(n_folds):
        # 划分训练集和验证集
        val_start = fold * fold_size
        val_end = val_start + fold_size

        X_val = X[val_start:val_end]
        y_val = y[val_start:val_end]

        X_train = np.concatenate([X[:val_start], X[val_end:]])
        y_train = np.concatenate([y[:val_start], y[val_end:]])

        # 简单的阈值分类器
        # 计算每个特征的均值
        mean_0 = np.mean(X_train[y_train.flatten() == 0], axis=0)
        mean_1 = np.mean(X_train[y_train.flatten() == 1], axis=0)

        # 预测
        predictions = []
        for x in X_val:
            dist_0 = np.linalg.norm(x - mean_0)
            dist_1 = np.linalg.norm(x - mean_1)
            predictions.append(0 if dist_0 < dist_1 else 1)

        accuracy = np.mean(np.array(predictions) == y_val.flatten())
        accuracies.append(accuracy)

    return np.mean(accuracies)


def create_sample_dataset(
    n_samples: int = 100,
    n_features: int = 10,
    n_informative: int = 5,
    noise: float = 0.1,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    创建示例数据集

    参数:
        n_samples: 样本数
        n_features: 特征数
        n_informative: 有效特征数
        noise: 噪声水平

    返回:
        (X, y) 元组
    """
    np.random.seed(42)

    # 生成有效特征
    X_informative = np.random.randn(n_samples, n_informative)

    # 生成标签（基于有效特征的线性组合）
    weights = np.random.randn(n_informative)
    y_continuous = X_informative @ weights + np.random.randn(n_samples) * noise
    y = (y_continuous > np.median(y_continuous)).astype(int).reshape(-1, 1)

    # 添加噪声特征
    X_noise = np.random.randn(n_samples, n_features - n_informative)
    X = np.hstack([X_informative, X_noise])

    return X, y
