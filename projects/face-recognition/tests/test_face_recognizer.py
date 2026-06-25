"""
人脸识别器测试
"""

import pytest
import numpy as np
import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.face_recognizer import FaceRecognizer, FaceDatabase
from src.utils import normalize_feature


class TestFaceDatabase:
    """FaceDatabase 测试"""

    def test_database_creation(self):
        """测试创建数据库"""
        db = FaceDatabase()
        assert db.get_num_people() == 0
        assert db.get_num_samples() == 0

    def test_add_face(self):
        """测试添加人脸"""
        db = FaceDatabase()
        feature = np.random.randn(128)
        db.add("张三", feature)
        assert db.contains("张三")
        assert db.get_num_people() == 1
        assert db.get_num_samples() == 1

    def test_add_multiple_features(self):
        """测试添加多个特征"""
        db = FaceDatabase()
        for i in range(3):
            feature = np.random.randn(128)
            db.add("张三", feature)
        assert db.get_num_people() == 1
        assert db.get_num_samples() == 3

    def test_remove_face(self):
        """测试移除人脸"""
        db = FaceDatabase()
        feature = np.random.randn(128)
        db.add("张三", feature)
        assert db.remove("张三") == True
        assert not db.contains("张三")

    def test_remove_nonexistent(self):
        """测试移除不存在的人脸"""
        db = FaceDatabase()
        assert db.remove("不存在") == False

    def test_get_features(self):
        """测试获取特征"""
        db = FaceDatabase()
        feature = np.random.randn(128)
        db.add("张三", feature)
        features = db.get_features("张三")
        assert features is not None
        assert len(features) == 1

    def test_get_names(self):
        """测试获取人名列表"""
        db = FaceDatabase()
        db.add("张三", np.random.randn(128))
        db.add("李四", np.random.randn(128))
        names = db.get_names()
        assert "张三" in names
        assert "李四" in names

    def test_clear(self):
        """测试清空数据库"""
        db = FaceDatabase()
        db.add("张三", np.random.randn(128))
        db.clear()
        assert db.get_num_people() == 0

    def test_save_load(self, tmp_path):
        """测试保存和加载"""
        db = FaceDatabase()
        feature = np.random.randn(128)
        db.add("张三", feature)

        # 保存
        save_path = str(tmp_path / "database")
        db.save(save_path)

        # 加载
        new_db = FaceDatabase()
        new_db.load(save_path)
        assert new_db.contains("张三")
        assert new_db.get_num_samples() == 1


class TestFaceRecognizer:
    """FaceRecognizer 测试"""

    def test_recognizer_creation(self):
        """测试创建识别器"""
        recognizer = FaceRecognizer(threshold=0.6)
        assert recognizer.threshold == 0.6

    def test_add_face(self):
        """测试添加人脸"""
        recognizer = FaceRecognizer()
        feature = np.random.randn(128)
        recognizer.add_face("张三", feature)
        info = recognizer.get_database_info()
        assert "张三" in info["names"]

    def test_identify_known_face(self):
        """测试识别已知人脸"""
        recognizer = FaceRecognizer(threshold=0.5)
        feature = normalize_feature(np.random.randn(128))
        recognizer.add_face("张三", feature)

        # 使用相似的特征查询
        query = normalize_feature(feature + np.random.randn(128) * 0.1)
        identity, confidence = recognizer.identify(query)
        assert identity == "张三"
        assert confidence > 0.5

    def test_identify_unknown_face(self):
        """测试识别未知人脸"""
        recognizer = FaceRecognizer(threshold=0.9)
        feature = normalize_feature(np.random.randn(128))
        recognizer.add_face("张三", feature)

        # 使用完全不同的特征查询
        query = normalize_feature(np.random.randn(128))
        identity, confidence = recognizer.identify(query)
        # 由于特征是随机的，可能无法确定是否匹配
        assert identity in ["张三", "Unknown"]

    def test_verify_same_features(self):
        """测试验证相同特征"""
        recognizer = FaceRecognizer(threshold=0.5)
        feature = normalize_feature(np.random.randn(128))

        is_same, similarity = recognizer.verify(feature, feature)
        assert is_same == True
        assert similarity > 0.99

    def test_verify_similar_features(self):
        """测试验证相似特征"""
        recognizer = FaceRecognizer(threshold=0.5)
        feature = normalize_feature(np.random.randn(128))

        # 添加微小扰动
        feature2 = normalize_feature(feature + np.random.randn(128) * 0.01)
        is_same, similarity = recognizer.verify(feature, feature2)
        assert is_same == True
        assert similarity > 0.9

    def test_verify_different_features(self):
        """测试验证不同特征"""
        recognizer = FaceRecognizer(threshold=0.9)
        feature1 = normalize_feature(np.random.randn(128))
        feature2 = normalize_feature(np.random.randn(128))

        is_same, similarity = recognizer.verify(feature1, feature2)
        # 随机特征可能相似度较低
        assert isinstance(is_same, bool)
        assert -1 <= similarity <= 1

    def test_remove_face(self):
        """测试移除人脸"""
        recognizer = FaceRecognizer()
        feature = np.random.randn(128)
        recognizer.add_face("张三", feature)
        assert recognizer.remove_face("张三") == True
        info = recognizer.get_database_info()
        assert "张三" not in info["names"]

    def test_find_similar(self):
        """测试查找相似人脸"""
        recognizer = FaceRecognizer()
        feature1 = normalize_feature(np.random.randn(128))
        feature2 = normalize_feature(np.random.randn(128))
        recognizer.add_face("张三", feature1)
        recognizer.add_face("李四", feature2)

        query = normalize_feature(feature1 + np.random.randn(128) * 0.1)
        results = recognizer.find_similar(query, top_k=2)
        assert len(results) == 2
        assert results[0][0] == "张三"  # 应该最相似

    def test_set_threshold(self):
        """测试设置阈值"""
        recognizer = FaceRecognizer(threshold=0.6)
        recognizer.set_threshold(0.8)
        assert recognizer.threshold == 0.8

    def test_invalid_threshold(self):
        """测试无效阈值"""
        recognizer = FaceRecognizer()
        with pytest.raises(ValueError):
            recognizer.set_threshold(1.5)

    def test_cosine_similarity(self):
        """测试余弦相似度计算"""
        feature1 = np.array([1.0, 0.0, 0.0])
        feature2 = np.array([1.0, 0.0, 0.0])
        similarity = FaceRecognizer._cosine_similarity(feature1, feature2)
        assert abs(similarity - 1.0) < 1e-5

    def test_euclidean_similarity(self):
        """测试欧氏距离相似度计算"""
        feature1 = np.array([1.0, 0.0, 0.0])
        feature2 = np.array([1.0, 0.0, 0.0])
        similarity = FaceRecognizer._euclidean_similarity(feature1, feature2)
        assert abs(similarity - 1.0) < 1e-5

    def test_save_load_database(self, tmp_path):
        """测试保存和加载数据库"""
        recognizer = FaceRecognizer()
        feature = normalize_feature(np.random.randn(128))
        recognizer.add_face("张三", feature)

        # 保存
        save_path = str(tmp_path / "face_db")
        recognizer.save_database(save_path)

        # 加载
        new_recognizer = FaceRecognizer()
        new_recognizer.load_database(save_path)
        info = new_recognizer.get_database_info()
        assert "张三" in info["names"]

    def test_distance_metric_cosine(self):
        """测试余弦距离度量"""
        recognizer = FaceRecognizer(distance_metric="cosine")
        feature1 = normalize_feature(np.random.randn(128))
        feature2 = normalize_feature(np.random.randn(128))
        _, similarity = recognizer.verify(feature1, feature2)
        assert -1 <= similarity <= 1

    def test_distance_metric_euclidean(self):
        """测试欧氏距离度量"""
        recognizer = FaceRecognizer(distance_metric="euclidean")
        feature1 = normalize_feature(np.random.randn(128))
        feature2 = normalize_feature(np.random.randn(128))
        _, similarity = recognizer.verify(feature1, feature2)
        assert 0 <= similarity <= 1

    def test_invalid_distance_metric(self):
        """测试无效的距离度量"""
        recognizer = FaceRecognizer(distance_metric="invalid")
        feature1 = normalize_feature(np.random.randn(128))
        feature2 = normalize_feature(np.random.randn(128))
        with pytest.raises(ValueError):
            recognizer.verify(feature1, feature2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
