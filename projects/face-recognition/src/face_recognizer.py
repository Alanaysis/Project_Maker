"""
人脸识别模块

实现人脸验证和身份识别功能。
"""

import numpy as np
import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class FaceDatabase:
    """
    人脸特征数据库

    存储和管理已知人脸的特征向量。
    """

    def __init__(self):
        """初始化数据库"""
        self.database: Dict[str, List[np.ndarray]] = {}
        self.metadata: Dict[str, dict] = {}

    def add(self, name: str, feature: np.ndarray, metadata: Optional[dict] = None):
        """
        添加人脸特征

        Args:
            name: 人名
            feature: 特征向量
            metadata: 元数据
        """
        if name not in self.database:
            self.database[name] = []
            self.metadata[name] = {
                "added_date": self._get_current_time(),
                "num_samples": 0,
            }

        self.database[name].append(feature)
        self.metadata[name]["num_samples"] = len(self.database[name])

        if metadata:
            self.metadata[name].update(metadata)

    def remove(self, name: str) -> bool:
        """
        移除人脸

        Args:
            name: 人名

        Returns:
            是否成功移除
        """
        if name in self.database:
            del self.database[name]
            del self.metadata[name]
            return True
        return False

    def get_features(self, name: str) -> Optional[List[np.ndarray]]:
        """
        获取指定人的所有特征

        Args:
            name: 人名

        Returns:
            特征列表
        """
        return self.database.get(name)

    def get_names(self) -> List[str]:
        """获取所有人名"""
        return list(self.database.keys())

    def get_num_people(self) -> int:
        """获取人数"""
        return len(self.database)

    def get_num_samples(self) -> int:
        """获取总样本数"""
        return sum(len(features) for features in self.database.values())

    def contains(self, name: str) -> bool:
        """检查是否包含指定人"""
        return name in self.database

    def clear(self):
        """清空数据库"""
        self.database.clear()
        self.metadata.clear()

    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def save(self, path: str):
        """
        保存数据库到文件

        Args:
            path: 保存路径
        """
        save_dir = Path(path)
        save_dir.mkdir(parents=True, exist_ok=True)

        # 保存特征
        for name, features in self.database.items():
            person_dir = save_dir / name
            person_dir.mkdir(exist_ok=True)

            # 保存特征向量
            features_array = np.array(features)
            np.save(str(person_dir / "features.npy"), features_array)

        # 保存元数据
        metadata_path = save_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def load(self, path: str):
        """
        从文件加载数据库

        Args:
            path: 数据库路径
        """
        load_dir = Path(path)

        if not load_dir.exists():
            raise FileNotFoundError(f"数据库路径不存在: {path}")

        # 加载元数据
        metadata_path = load_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

        # 加载特征
        self.database = {}
        for person_dir in load_dir.iterdir():
            if person_dir.is_dir() and person_dir.name != "__pycache__":
                features_path = person_dir / "features.npy"
                if features_path.exists():
                    features_array = np.load(str(features_path))
                    self.database[person_dir.name] = [
                        features_array[i] for i in range(len(features_array))
                    ]


class FaceRecognizer:
    """
    人脸识别器

    支持人脸验证（1:1）和身份识别（1:N）。
    """

    def __init__(self, threshold: float = 0.6, distance_metric: str = "cosine"):
        """
        初始化识别器

        Args:
            threshold: 匹配阈值
            distance_metric: 距离度量 ("cosine" 或 "euclidean")
        """
        self.threshold = threshold
        self.distance_metric = distance_metric
        self.database = FaceDatabase()

    def add_face(self, name: str, feature: np.ndarray, metadata: Optional[dict] = None):
        """
        添加人脸到数据库

        Args:
            name: 人名
            feature: 特征向量
            metadata: 元数据
        """
        # 确保特征已归一化
        feature = self._normalize_feature(feature)
        self.database.add(name, feature, metadata)

    def remove_face(self, name: str) -> bool:
        """
        从数据库移除人脸

        Args:
            name: 人名

        Returns:
            是否成功移除
        """
        return self.database.remove(name)

    def identify(self, feature: np.ndarray) -> Tuple[str, float]:
        """
        识别未知人脸

        Args:
            feature: 特征向量

        Returns:
            (身份, 置信度) 元组
        """
        feature = self._normalize_feature(feature)

        best_match = "Unknown"
        best_similarity = -1.0

        for name, features in self.database.database.items():
            for db_feature in features:
                similarity = self._compute_similarity(feature, db_feature)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = name

        # 检查是否超过阈值
        if best_similarity >= self.threshold:
            return best_match, best_similarity

        return "Unknown", best_similarity

    def verify(self, feature1: np.ndarray, feature2: np.ndarray) -> Tuple[bool, float]:
        """
        验证两张人脸是否为同一人

        Args:
            feature1: 特征向量 1
            feature2: 特征向量 2

        Returns:
            (是否匹配, 相似度) 元组
        """
        feature1 = self._normalize_feature(feature1)
        feature2 = self._normalize_feature(feature2)

        similarity = self._compute_similarity(feature1, feature2)

        return similarity >= self.threshold, similarity

    def find_similar(self, feature: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        查找最相似的人脸

        Args:
            feature: 特征向量
            top_k: 返回前 k 个结果

        Returns:
            [(人名, 相似度)] 列表
        """
        feature = self._normalize_feature(feature)

        similarities = []
        for name, features in self.database.database.items():
            # 计算与该人所有特征的平均相似度
            sims = [self._compute_similarity(feature, f) for f in features]
            avg_sim = np.mean(sims)
            similarities.append((name, avg_sim))

        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def _compute_similarity(self, feature1: np.ndarray, feature2: np.ndarray) -> float:
        """
        计算两个特征的相似度

        Args:
            feature1: 特征向量 1
            feature2: 特征向量 2

        Returns:
            相似度分数
        """
        if self.distance_metric == "cosine":
            return self._cosine_similarity(feature1, feature2)
        elif self.distance_metric == "euclidean":
            return self._euclidean_similarity(feature1, feature2)
        else:
            raise ValueError(f"不支持的距离度量: {self.distance_metric}")

    @staticmethod
    def _cosine_similarity(feature1: np.ndarray, feature2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(feature1, feature2)
        norm1 = np.linalg.norm(feature1)
        norm2 = np.linalg.norm(feature2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    @staticmethod
    def _euclidean_similarity(feature1: np.ndarray, feature2: np.ndarray) -> float:
        """计算欧氏距离相似度（转换为相似度分数）"""
        distance = np.linalg.norm(feature1 - feature2)
        # 将距离转换为相似度 (0, 1]
        return float(1.0 / (1.0 + distance))

    @staticmethod
    def _normalize_feature(feature: np.ndarray) -> np.ndarray:
        """归一化特征向量"""
        norm = np.linalg.norm(feature)
        if norm > 0:
            return feature / norm
        return feature

    def save_database(self, path: str):
        """
        保存数据库

        Args:
            path: 保存路径
        """
        self.database.save(path)

    def load_database(self, path: str):
        """
        加载数据库

        Args:
            path: 数据库路径
        """
        self.database.load(path)

    def get_database_info(self) -> dict:
        """获取数据库信息"""
        return {
            "num_people": self.database.get_num_people(),
            "num_samples": self.database.get_num_samples(),
            "names": self.database.get_names(),
            "threshold": self.threshold,
            "distance_metric": self.distance_metric,
        }

    def set_threshold(self, threshold: float):
        """设置匹配阈值"""
        if not 0 <= threshold <= 1:
            raise ValueError("阈值必须在 0 和 1 之间")
        self.threshold = threshold
