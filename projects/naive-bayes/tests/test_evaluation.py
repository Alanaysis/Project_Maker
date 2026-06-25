"""模型评估模块测试"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.evaluation import (
    accuracy,
    confusion_matrix,
    confusion_matrix_to_table,
    precision,
    recall,
    f1_score,
    classification_report,
    print_confusion_matrix,
    evaluate_model,
)


class TestAccuracy:
    """准确率测试"""

    def test_perfect_prediction(self) -> None:
        """测试完美预测"""
        y_true = [0, 1, 2, 0, 1, 2]
        y_pred = [0, 1, 2, 0, 1, 2]
        assert accuracy(y_true, y_pred) == 1.0

    def test_worst_prediction(self) -> None:
        """测试最差预测"""
        y_true = [0, 0, 0, 0]
        y_pred = [1, 1, 1, 1]
        assert accuracy(y_true, y_pred) == 0.0

    def test_partial_prediction(self) -> None:
        """测试部分正确"""
        y_true = [0, 1, 0, 1]
        y_pred = [0, 0, 0, 1]
        assert accuracy(y_true, y_pred) == 0.75

    def test_single_class(self) -> None:
        """测试单类别"""
        y_true = [0, 0, 0]
        y_pred = [0, 0, 0]
        assert accuracy(y_true, y_pred) == 1.0

    def test_mismatched_lengths_raises(self) -> None:
        """测试长度不匹配"""
        with pytest.raises(ValueError, match="长度必须相同"):
            accuracy([0, 1], [0])

    def test_empty_list_raises(self) -> None:
        """测试空列表"""
        with pytest.raises(ValueError, match="不能为空"):
            accuracy([], [])


class TestConfusionMatrix:
    """混淆矩阵测试"""

    def test_binary_classification(self) -> None:
        """测试二分类"""
        y_true = [0, 0, 1, 1]
        y_pred = [0, 1, 0, 1]

        matrix = confusion_matrix(y_true, y_pred)

        assert matrix[(0, 0)] == 1  # TN
        assert matrix[(0, 1)] == 1  # FP
        assert matrix[(1, 0)] == 1  # FN
        assert matrix[(1, 1)] == 1  # TP

    def test_perfect_prediction(self) -> None:
        """测试完美预测"""
        y_true = [0, 1, 2, 0, 1, 2]
        y_pred = [0, 1, 2, 0, 1, 2]

        matrix = confusion_matrix(y_true, y_pred)

        assert matrix[(0, 0)] == 2
        assert matrix[(1, 1)] == 2
        assert matrix[(2, 2)] == 2
        assert matrix[(0, 1)] == 0
        assert matrix[(0, 2)] == 0

    def test_custom_labels(self) -> None:
        """测试自定义标签"""
        y_true = [0, 1]
        y_pred = [0, 1]
        labels = [0, 1, 2]

        matrix = confusion_matrix(y_true, y_pred, labels)

        assert matrix[(2, 2)] == 0
        assert len(matrix) == 9  # 3x3

    def test_to_table(self) -> None:
        """测试转换为表格"""
        y_true = [0, 0, 1, 1]
        y_pred = [0, 1, 0, 1]
        labels = [0, 1]

        matrix = confusion_matrix(y_true, y_pred, labels)
        table = confusion_matrix_to_table(matrix, labels)

        assert table[0][0] == 1
        assert table[0][1] == 1
        assert table[1][0] == 1
        assert table[1][1] == 1

    def test_mismatched_lengths_raises(self) -> None:
        """测试长度不匹配"""
        with pytest.raises(ValueError, match="长度必须相同"):
            confusion_matrix([0], [0, 1])


class TestPrecision:
    """精确率测试"""

    def test_binary_perfect(self) -> None:
        """测试二分类完美预测"""
        y_true = [0, 0, 1, 1]
        y_pred = [0, 0, 1, 1]

        p = precision(y_true, y_pred, average="macro")
        assert p == 1.0

    def test_binary_partial(self) -> None:
        """测试二分类部分正确"""
        # 类别0: TP=2, FP=0 -> precision=2/2=1.0
        # 类别1: TP=1, FP=1 -> precision=1/2=0.5
        y_true = [0, 0, 0, 1]
        y_pred = [0, 0, 1, 1]

        p = precision(y_true, y_pred, average="macro")
        assert abs(p - (1.0 + 0.5) / 2) < 1e-6

    def test_micro_average(self) -> None:
        """测试微平均"""
        y_true = [0, 0, 1, 1]
        y_pred = [0, 1, 0, 1]

        p = precision(y_true, y_pred, average="micro")
        assert p == 0.5

    def test_weighted_average(self) -> None:
        """测试加权平均"""
        y_true = [0, 0, 0, 1]
        y_pred = [0, 0, 1, 1]

        p = precision(y_true, y_pred, average="weighted")
        assert isinstance(p, float)

    def test_per_class(self) -> None:
        """测试每类精确率"""
        y_true = [0, 0, 1, 1]
        y_pred = [0, 1, 0, 1]

        p = precision(y_true, y_pred, average=None)
        assert isinstance(p, dict)
        assert 0 in p
        assert 1 in p

    def test_with_zero_division(self) -> None:
        """测试零除情况"""
        # 类别2被预测但不存在
        y_true = [0, 0, 1, 1]
        y_pred = [0, 1, 2, 2]

        p = precision(y_true, y_pred, average=None)
        assert p[2] == 0.0  # 无法计算精确率


class TestRecall:
    """召回率测试"""

    def test_binary_perfect(self) -> None:
        """测试二分类完美预测"""
        y_true = [0, 0, 1, 1]
        y_pred = [0, 0, 1, 1]

        r = recall(y_true, y_pred, average="macro")
        assert r == 1.0

    def test_binary_partial(self) -> None:
        """测试二分类部分正确"""
        # 类别0: TP=2, FN=0 -> recall=1
        # 类别1: TP=1, FN=1 -> recall=0.5
        y_true = [0, 0, 1, 1]
        y_pred = [0, 0, 0, 1]

        r = recall(y_true, y_pred, average="macro")
        assert abs(r - (1 + 0.5) / 2) < 1e-6

    def test_per_class(self) -> None:
        """测试每类召回率"""
        y_true = [0, 0, 1, 1]
        y_pred = [0, 0, 1, 1]

        r = recall(y_true, y_pred, average=None)
        assert isinstance(r, dict)
        assert r[0] == 1.0
        assert r[1] == 1.0


class TestF1Score:
    """F1分数测试"""

    def test_binary_perfect(self) -> None:
        """测试二分类完美预测"""
        y_true = [0, 0, 1, 1]
        y_pred = [0, 0, 1, 1]

        f1 = f1_score(y_true, y_pred, average="macro")
        assert f1 == 1.0

    def test_binary_partial(self) -> None:
        """测试二分类部分正确"""
        y_true = [0, 0, 1, 1]
        y_pred = [0, 0, 0, 1]

        f1 = f1_score(y_true, y_pred, average="macro")
        assert isinstance(f1, float)
        assert 0 < f1 < 1

    def test_per_class(self) -> None:
        """测试每类F1"""
        y_true = [0, 0, 1, 1]
        y_pred = [0, 0, 1, 1]

        f1 = f1_score(y_true, y_pred, average=None)
        assert isinstance(f1, dict)
        assert f1[0] == 1.0
        assert f1[1] == 1.0

    def test_zero_precision_recall(self) -> None:
        """测试零精确率和召回率"""
        y_true = [0, 1]
        y_pred = [1, 0]

        f1 = f1_score(y_true, y_pred, average="macro")
        assert f1 == 0.0


class TestClassificationReport:
    """分类报告测试"""

    def test_binary_report(self) -> None:
        """测试二分类报告"""
        y_true = [0, 0, 1, 1]
        y_pred = [0, 0, 1, 1]

        report = classification_report(y_true, y_pred)

        assert "precision" in report
        assert "recall" in report
        assert "f1-score" in report
        assert "macro avg" in report
        assert "weighted avg" in report

    def test_multiclass_report(self) -> None:
        """测试多分类报告"""
        y_true = [0, 1, 2, 0, 1, 2]
        y_pred = [0, 1, 2, 0, 1, 2]

        report = classification_report(y_true, y_pred)

        assert "0" in report
        assert "1" in report
        assert "2" in report


class TestPrintConfusionMatrix:
    """打印混淆矩阵测试"""

    def test_binary_output(self) -> None:
        """测试二分类输出"""
        y_true = [0, 0, 1, 1]
        y_pred = [0, 1, 0, 1]

        output = print_confusion_matrix(y_true, y_pred)

        assert "预测标签" in output
        assert "真实标签" in output

    def test_multiclass_output(self) -> None:
        """测试多分类输出"""
        y_true = [0, 1, 2]
        y_pred = [0, 1, 2]

        output = print_confusion_matrix(y_true, y_pred)

        assert "0" in output
        assert "1" in output
        assert "2" in output


class TestEvaluateModel:
    """综合评估测试"""

    def test_evaluate_binary(self) -> None:
        """测试二分类评估"""
        y_true = [0, 0, 1, 1]
        y_pred = [0, 0, 1, 1]

        results = evaluate_model(y_true, y_pred)

        assert results["accuracy"] == 1.0
        assert results["precision_macro"] == 1.0
        assert results["recall_macro"] == 1.0
        assert results["f1_macro"] == 1.0
        assert "confusion_matrix" in results
        assert "report" in results

    def test_evaluate_multiclass(self) -> None:
        """测试多分类评估"""
        y_true = [0, 1, 2, 0, 1, 2]
        y_pred = [0, 1, 1, 0, 2, 2]

        results = evaluate_model(y_true, y_pred)

        assert results["accuracy"] < 1.0
        assert results["precision_macro"] < 1.0
        assert "confusion_matrix" in results

    def test_evaluate_contains_all_metrics(self) -> None:
        """测试包含所有指标"""
        y_true = [0, 1]
        y_pred = [0, 1]

        results = evaluate_model(y_true, y_pred)

        expected_keys = [
            "accuracy",
            "precision_macro",
            "precision_weighted",
            "recall_macro",
            "recall_weighted",
            "f1_macro",
            "f1_weighted",
            "confusion_matrix",
            "report",
        ]
        for key in expected_keys:
            assert key in results
