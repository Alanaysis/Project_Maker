"""
多分类 SVM 模块
==============

实现两种经典的多分类策略:
- One-vs-Rest (OvR): 为每个类别训练一个二分类器，该类 vs 其余所有类
- One-vs-One (OvO): 为每对类别训练一个二分类器，使用投票决定最终类别

SVM 本身是二分类器，通过组合多个二分类器实现多分类。
"""

import numpy as np
from typing import Optional, Literal, List, Tuple
from .svm import SVM


class OneVsRestSVM:
    """
    One-vs-Rest (OvR) 多分类 SVM

    为每个类别训练一个二分类 SVM:
    - 类别 k 的正类: 标签为 k 的样本
    - 类别 k 的负类: 标签不为 k 的所有样本

    预测时，选择决策函数值最大的类别。

    属性:
        classes: 所有类别
        classifiers: 每个类别对应的二分类 SVM
    """

    def __init__(
        self,
        kernel: Literal["linear", "rbf", "polynomial", "sigmoid"] = "rbf",
        C: float = 1.0,
        gamma: float = 1.0,
        degree: int = 3,
        coef0: float = 1.0,
        tol: float = 1e-3,
        max_passes: int = 10,
    ):
        """
        初始化 One-vs-Rest 多分类 SVM

        参数:
            kernel: 核函数类型
            C: 正则化参数
            gamma: RBF/Sigmoid 核参数
            degree: 多项式核阶数
            coef0: 多项式/Sigmoid 核系数
            tol: 容差
            max_passes: 最大迭代次数
        """
        self.kernel = kernel
        self.C = C
        self.gamma = gamma
        self.degree = degree
        self.coef0 = coef0
        self.tol = tol
        self.max_passes = max_passes

        self.classes: Optional[np.ndarray] = None
        self.classifiers: List[SVM] = []

    def fit(self, X: np.ndarray, y: np.ndarray) -> "OneVsRestSVM":
        """
        训练 One-vs-Rest 多分类 SVM

        参数:
            X: 训练数据，形状 (n_samples, n_features)
            y: 标签，形状 (n_samples,)

        返回:
            self
        """
        self.classes = np.unique(y)
        self.classifiers = []

        for cls in self.classes:
            # 创建二分类标签: 当前类为 +1，其余为 -1
            binary_y = np.where(y == cls, 1, -1)

            svm = SVM(
                kernel=self.kernel,
                C=self.C,
                gamma=self.gamma,
                degree=self.degree,
                coef0=self.coef0,
                tol=self.tol,
                max_passes=self.max_passes,
            )
            svm.fit(X, binary_y)
            self.classifiers.append(svm)

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测新数据的类别

        选择决策函数值最大的类别。

        参数:
            X: 待预测数据，形状 (n_samples, n_features)

        返回:
            predictions: 预测类别，形状 (n_samples,)
        """
        if self.classes is None:
            raise RuntimeError("模型尚未训练，请先调用 fit() 方法")

        n_samples = X.shape[0]
        n_classes = len(self.classes)
        decision_values = np.zeros((n_samples, n_classes))

        for idx, svm in enumerate(self.classifiers):
            decision_values[:, idx] = svm.decision_function(X)

        # 选择决策值最大的类别
        predicted_indices = np.argmax(decision_values, axis=1)
        return self.classes[predicted_indices]

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        计算分类准确率

        参数:
            X: 测试数据
            y: 真实标签

        返回:
            accuracy: 准确率
        """
        predictions = self.predict(X)
        return np.mean(predictions == y)

    def __repr__(self) -> str:
        return (
            f"OneVsRestSVM(kernel='{self.kernel}', C={self.C}, "
            f"n_classes={len(self.classes) if self.classes is not None else '?'})"
        )


class OneVsOneSVM:
    """
    One-vs-One (OvO) 多分类 SVM

    为每对类别 (i, j) 训练一个二分类 SVM。
    预测时，每个分类器投票，选择得票最多的类别。

    总共需要训练 C(n_classes, 2) = n_classes * (n_classes - 1) / 2 个分类器。

    属性:
        classes: 所有类别
        classifiers: 每对类别对应的二分类 SVM
        class_pairs: 每个分类器对应的类别对
    """

    def __init__(
        self,
        kernel: Literal["linear", "rbf", "polynomial", "sigmoid"] = "rbf",
        C: float = 1.0,
        gamma: float = 1.0,
        degree: int = 3,
        coef0: float = 1.0,
        tol: float = 1e-3,
        max_passes: int = 10,
    ):
        """
        初始化 One-vs-One 多分类 SVM

        参数:
            kernel: 核函数类型
            C: 正则化参数
            gamma: RBF/Sigmoid 核参数
            degree: 多项式核阶数
            coef0: 多项式/Sigmoid 核系数
            tol: 容差
            max_passes: 最大迭代次数
        """
        self.kernel = kernel
        self.C = C
        self.gamma = gamma
        self.degree = degree
        self.coef0 = coef0
        self.tol = tol
        self.max_passes = max_passes

        self.classes: Optional[np.ndarray] = None
        self.classifiers: List[SVM] = []
        self.class_pairs: List[Tuple] = []

    def fit(self, X: np.ndarray, y: np.ndarray) -> "OneVsOneSVM":
        """
        训练 One-vs-One 多分类 SVM

        为每对类别训练一个二分类 SVM。

        参数:
            X: 训练数据，形状 (n_samples, n_features)
            y: 标签，形状 (n_samples,)

        返回:
            self
        """
        self.classes = np.unique(y)
        self.classifiers = []
        self.class_pairs = []

        n_classes = len(self.classes)

        for i in range(n_classes):
            for j in range(i + 1, n_classes):
                cls_i = self.classes[i]
                cls_j = self.classes[j]

                # 只选择类别 i 和 j 的样本
                mask = (y == cls_i) | (y == cls_j)
                X_pair = X[mask]
                y_pair = y[mask]

                # 转换为 +1 / -1 标签
                binary_y = np.where(y_pair == cls_i, 1, -1)

                svm = SVM(
                    kernel=self.kernel,
                    C=self.C,
                    gamma=self.gamma,
                    degree=self.degree,
                    coef0=self.coef0,
                    tol=self.tol,
                    max_passes=self.max_passes,
                )
                svm.fit(X_pair, binary_y)
                self.classifiers.append(svm)
                self.class_pairs.append((cls_i, cls_j))

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测新数据的类别

        每个分类器投票，选择得票最多的类别。

        参数:
            X: 待预测数据，形状 (n_samples, n_features)

        返回:
            predictions: 预测类别，形状 (n_samples,)
        """
        if self.classes is None:
            raise RuntimeError("模型尚未训练，请先调用 fit() 方法")

        n_samples = X.shape[0]
        n_classes = len(self.classes)

        # 投票矩阵
        votes = np.zeros((n_samples, n_classes), dtype=int)

        for idx, svm in enumerate(self.classifiers):
            predictions = svm.predict(X)
            cls_i, cls_j = self.class_pairs[idx]

            # 找到类别在 classes 数组中的索引
            idx_i = np.where(self.classes == cls_i)[0][0]
            idx_j = np.where(self.classes == cls_j)[0][0]

            # 投票: +1 投给 cls_i，-1 投给 cls_j
            for k in range(n_samples):
                if predictions[k] == 1:
                    votes[k, idx_i] += 1
                else:
                    votes[k, idx_j] += 1

        # 选择得票最多的类别
        predicted_indices = np.argmax(votes, axis=1)
        return self.classes[predicted_indices]

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        计算分类准确率

        参数:
            X: 测试数据
            y: 真实标签

        返回:
            accuracy: 准确率
        """
        predictions = self.predict(X)
        return np.mean(predictions == y)

    def __repr__(self) -> str:
        n_cls = len(self.classes) if self.classes is not None else 0
        n_svm = len(self.classifiers)
        return (
            f"OneVsOneSVM(kernel='{self.kernel}', C={self.C}, "
            f"n_classes={n_cls}, n_classifiers={n_svm})"
        )
