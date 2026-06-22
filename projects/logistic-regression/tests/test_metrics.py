"""
评估指标测试
"""

import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.metrics import (
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)


class TestMetrics:
    """评估指标测试类"""

    def test_confusion_matrix(self):
        """测试混淆矩阵计算"""
        y_true = np.array([1, 1, 0, 0, 1, 0])
        y_pred = np.array([1, 0, 0, 1, 1, 0])

        tn, fp, fn, tp = confusion_matrix(y_true, y_pred)

        assert tp == 2  # 预测为1且实际为1
        assert tn == 2  # 预测为0且实际为0
        assert fp == 1  # 预测为1但实际为0
        assert fn == 1  # 预测为0但实际为1

    def test_perfect_prediction(self):
        """测试完美预测"""
        y_true = np.array([1, 1, 0, 0])
        y_pred = np.array([1, 1, 0, 0])

        assert accuracy_score(y_true, y_pred) == 1.0
        assert precision_score(y_true, y_pred) == 1.0
        assert recall_score(y_true, y_pred) == 1.0
        assert f1_score(y_true, y_pred) == 1.0

    def test_worst_prediction(self):
        """测试最差预测"""
        y_true = np.array([1, 1, 0, 0])
        y_pred = np.array([0, 0, 1, 1])

        assert accuracy_score(y_true, y_pred) == 0.0
        assert precision_score(y_true, y_pred) == 0.0
        assert recall_score(y_true, y_pred) == 0.0

    def test_accuracy(self):
        """测试准确率计算"""
        y_true = np.array([1, 1, 0, 0, 1])
        y_pred = np.array([1, 0, 0, 0, 1])

        acc = accuracy_score(y_true, y_pred)
        assert acc == 0.8  # 4/5

    def test_precision(self):
        """测试精确率计算"""
        y_true = np.array([1, 1, 0, 0, 1])
        y_pred = np.array([1, 1, 1, 0, 0])

        prec = precision_score(y_true, y_pred)
        # TP=2, FP=1, Precision = 2/3
        assert abs(prec - 2/3) < 1e-10

    def test_recall(self):
        """测试召回率计算"""
        y_true = np.array([1, 1, 0, 0, 1])
        y_pred = np.array([1, 0, 0, 0, 1])

        rec = recall_score(y_true, y_pred)
        # TP=2, FN=1, Recall = 2/3
        assert abs(rec - 2/3) < 1e-10

    def test_f1_score(self):
        """测试F1分数计算"""
        y_true = np.array([1, 1, 0, 0, 1])
        y_pred = np.array([1, 1, 0, 0, 0])

        f1 = f1_score(y_true, y_pred)
        # Precision = 2/2 = 1, Recall = 2/3
        # F1 = 2 * (1 * 2/3) / (1 + 2/3) = 4/5 = 0.8
        assert abs(f1 - 0.8) < 1e-10

    def test_edge_case_all_positive(self):
        """测试全正类情况"""
        y_true = np.array([1, 1, 1])
        y_pred = np.array([1, 1, 1])

        assert accuracy_score(y_true, y_pred) == 1.0
        assert precision_score(y_true, y_pred) == 1.0
        assert recall_score(y_true, y_pred) == 1.0

    def test_edge_case_all_negative(self):
        """测试全负类情况"""
        y_true = np.array([0, 0, 0])
        y_pred = np.array([0, 0, 0])

        assert accuracy_score(y_true, y_pred) == 1.0
        # 精确率和召回率为0（分母为0）
        assert precision_score(y_true, y_pred) == 0.0
        assert recall_score(y_true, y_pred) == 0.0

    def test_classification_report(self):
        """测试分类报告生成"""
        y_true = np.array([1, 1, 0, 0, 1, 0])
        y_pred = np.array([1, 0, 0, 1, 1, 0])

        report = classification_report(y_true, y_pred)

        assert '准确率' in report
        assert '精确率' in report
        assert '召回率' in report
        assert 'F1分数' in report
        assert '混淆矩阵' in report


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
