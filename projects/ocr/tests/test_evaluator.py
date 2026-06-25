"""测试评估器"""

import pytest
import numpy as np
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.evaluator import OCREvaluator, DetectionEvaluator


class TestOCREvaluator:
    """测试评估器"""

    @pytest.fixture
    def evaluator(self):
        return OCREvaluator()

    def test_add_result(self, evaluator):
        """添加结果"""
        evaluator.add_result("hello", "hello")
        assert len(evaluator.results) == 1

    def test_reset(self, evaluator):
        """重置"""
        evaluator.add_result("test", "test")
        evaluator.reset()
        assert len(evaluator.results) == 0

    def test_char_accuracy_perfect(self, evaluator):
        """完美字符准确率"""
        evaluator.add_result("hello", "hello")
        assert evaluator.compute_char_accuracy() == 1.0

    def test_char_accuracy_partial(self, evaluator):
        """部分字符准确率"""
        evaluator.add_result("helo", "hello")
        accuracy = evaluator.compute_char_accuracy()
        assert 0 < accuracy < 1

    def test_word_accuracy_perfect(self, evaluator):
        """完美词准确率"""
        evaluator.add_result("hello", "hello")
        evaluator.add_result("world", "world")
        assert evaluator.compute_word_accuracy() == 1.0

    def test_word_accuracy_partial(self, evaluator):
        """部分词准确率"""
        evaluator.add_result("hello", "hello")
        evaluator.add_result("helo", "hello")
        assert evaluator.compute_word_accuracy() == 0.5

    def test_edit_distance_same(self, evaluator):
        """相同字符串编辑距离"""
        assert evaluator.compute_edit_distance("hello", "hello") == 0

    def test_edit_distance_one_edit(self, evaluator):
        """一次编辑"""
        assert evaluator.compute_edit_distance("hello", "helo") == 1

    def test_edit_distance_different(self, evaluator):
        """完全不同"""
        assert evaluator.compute_edit_distance("abc", "xyz") == 3

    def test_edit_distance_empty(self, evaluator):
        """空字符串"""
        assert evaluator.compute_edit_distance("", "hello") == 5
        assert evaluator.compute_edit_distance("hello", "") == 5

    def test_normalized_edit_distance(self, evaluator):
        """归一化编辑距离"""
        evaluator.add_result("hello", "hello")
        evaluator.add_result("helo", "hello")
        ned = evaluator.compute_normalized_edit_distance()
        assert 0 <= ned <= 1

    def test_summary(self, evaluator):
        """评估摘要"""
        evaluator.add_result("test", "test")
        summary = evaluator.summary()

        assert "char_accuracy" in summary
        assert "word_accuracy" in summary
        assert "normalized_edit_distance" in summary
        assert "num_samples" in summary

    def test_summary_empty(self, evaluator):
        """空结果摘要"""
        summary = evaluator.summary()
        assert summary["num_samples"] == 0

    def test_print_summary(self, evaluator, capsys):
        """打印摘要"""
        evaluator.add_result("test", "test")
        evaluator.print_summary()
        captured = capsys.readouterr()
        assert "评估报告" in captured.out


class TestDetectionEvaluator:
    """测试检测评估器"""

    @pytest.fixture
    def evaluator(self):
        return DetectionEvaluator()

    def test_add_result(self, evaluator):
        """添加结果"""
        pred_boxes = [np.array([[0, 0], [10, 0], [10, 10], [0, 10]])]
        gt_boxes = [np.array([[0, 0], [10, 0], [10, 10], [0, 10]])]
        evaluator.add_result(pred_boxes, gt_boxes)
        assert len(evaluator.results) == 1

    def test_compute_metrics_perfect(self, evaluator):
        """完美检测"""
        pred_boxes = [np.array([[0, 0], [10, 0], [10, 10], [0, 10]])]
        gt_boxes = [np.array([[0, 0], [10, 0], [10, 10], [0, 10]])]
        evaluator.add_result(pred_boxes, gt_boxes)

        metrics = evaluator.compute_metrics(iou_threshold=0.5)
        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0
        assert metrics["f1"] == 1.0

    def test_compute_metrics_no_match(self, evaluator):
        """无匹配"""
        pred_boxes = [np.array([[0, 0], [10, 0], [10, 10], [0, 10]])]
        gt_boxes = [np.array([[100, 100], [110, 100], [110, 110], [100, 110]])]
        evaluator.add_result(pred_boxes, gt_boxes)

        metrics = evaluator.compute_metrics(iou_threshold=0.5)
        assert metrics["precision"] == 0.0
        assert metrics["recall"] == 0.0

    def test_compute_metrics_empty(self, evaluator):
        """空结果"""
        metrics = evaluator.compute_metrics()
        assert metrics["precision"] == 0.0
        assert metrics["recall"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])