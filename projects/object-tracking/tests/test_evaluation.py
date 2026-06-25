"""
跟踪评估测试

测试内容:
- IoU计算
- 中心误差计算
- 精度图计算
- 成功率计算
- 评估器功能
"""

import pytest
import numpy as np
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.evaluation import (
    compute_iou,
    compute_center_error,
    compute_precision,
    compute_success_rate,
    compute_average_precision,
    compute_area_under_curve,
    compute_fps,
    TrackingEvaluator,
    OPEBenchmark
)


class TestIoU:
    """IoU测试类"""

    def test_perfect_overlap(self):
        """测试完全重叠"""
        bbox = (100, 100, 50, 50)
        iou = compute_iou(bbox, bbox)
        assert abs(iou - 1.0) < 1e-6

    def test_no_overlap(self):
        """测试无重叠"""
        bbox1 = (100, 100, 50, 50)
        bbox2 = (300, 300, 50, 50)
        iou = compute_iou(bbox1, bbox2)
        assert iou == 0.0

    def test_partial_overlap(self):
        """测试部分重叠"""
        bbox1 = (100, 100, 50, 50)
        bbox2 = (120, 120, 50, 50)
        iou = compute_iou(bbox1, bbox2)

        # 计算期望IoU
        # 交集: (120,120)-(150,150) = 30x30 = 900
        # 并集: 2500 + 2500 - 900 = 4100
        expected = 900 / 4100
        assert abs(iou - expected) < 1e-6

    def test_containment(self):
        """测试包含关系"""
        bbox1 = (100, 100, 100, 100)
        bbox2 = (125, 125, 50, 50)
        iou = compute_iou(bbox1, bbox2)

        # bbox2完全在bbox1内
        expected = 2500 / (10000 + 2500 - 2500)
        assert abs(iou - expected) < 1e-6


class TestCenterError:
    """中心误差测试类"""

    def test_same_center(self):
        """测试相同中心"""
        bbox = (100, 100, 50, 50)
        error = compute_center_error(bbox, bbox)
        assert error == 0.0

    def test_known_distance(self):
        """测试已知距离"""
        bbox1 = (100, 100, 50, 50)  # 中心: (125, 125)
        bbox2 = (130, 140, 50, 50)  # 中心: (155, 165)

        error = compute_center_error(bbox1, bbox2)
        expected = np.sqrt(30**2 + 40**2)
        assert abs(error - expected) < 1e-6


class TestPrecision:
    """精度测试类"""

    def test_perfect_tracking(self):
        """测试完美跟踪"""
        errors = [0.0] * 100
        thresholds, precisions = compute_precision(errors)

        # 所有阈值下精度都应该接近1
        for p in precisions:
            assert p == 1.0

    def test_zero_tracking(self):
        """测试零跟踪"""
        errors = [100.0] * 100
        thresholds, precisions = compute_precision(errors, thresholds=[0, 50])

        # 阈值0时精度为0
        assert precisions[0] == 0.0
        # 阈值50时精度为0
        assert precisions[1] == 0.0

    def test_mixed_tracking(self):
        """测试混合跟踪"""
        # 50个好跟踪，50个差跟踪
        errors = [1.0] * 50 + [100.0] * 50
        thresholds, precisions = compute_precision(errors, thresholds=[0, 5, 50])

        assert precisions[0] == 0.0  # 阈值0
        assert precisions[1] == 0.5  # 阈值5
        assert precisions[2] == 0.5  # 阈值50


class TestSuccessRate:
    """成功率测试类"""

    def test_perfect_tracking(self):
        """测试完美跟踪"""
        ious = [1.0] * 100
        thresholds, rates = compute_success_rate(ious)

        # 所有阈值下成功率都应该接近1
        for r in rates:
            assert r == 1.0

    def test_zero_tracking(self):
        """测试零跟踪"""
        ious = [0.0] * 100
        thresholds, rates = compute_success_rate(ious, thresholds=[0, 0.5])

        # IoU=0时成功率
        assert rates[0] == 1.0  # 阈值0: 所有都>=0
        assert rates[1] == 0.0  # 阈值0.5: 没有>=0.5


class TestTrackingEvaluator:
    """跟踪评估器测试类"""

    def test_add_frame(self):
        """测试添加帧"""
        evaluator = TrackingEvaluator()

        evaluator.add_frame("tracker1", (100, 100, 50, 50), (105, 105, 50, 50))
        evaluator.add_frame("tracker1", (110, 110, 50, 50), (115, 115, 50, 50))

        assert "tracker1" in evaluator.results
        assert evaluator.results["tracker1"].num_frames == 2

    def test_evaluate(self):
        """测试评估"""
        evaluator = TrackingEvaluator()

        # 添加一些帧
        for i in range(20):
            gt = (100 + 5*i, 100 + 3*i, 50, 50)
            pred = (100 + 5*i, 100 + 3*i, 50, 50)  # 完美跟踪
            evaluator.add_frame("perfect", pred, gt)

        result = evaluator.evaluate("perfect")

        assert "average_precision" in result
        assert "success_auc" in result
        assert result["average_iou"] > 0.99

    def test_compare(self):
        """测试比较"""
        evaluator = TrackingEvaluator()

        # 添加两个跟踪器的结果
        for i in range(20):
            gt = (100, 100, 50, 50)

            # 好的跟踪器
            evaluator.add_frame("good", gt, gt)

            # 差的跟踪器
            bad = (200, 200, 50, 50)
            evaluator.add_frame("bad", bad, gt)

        comparison = evaluator.compare("average_iou")
        assert len(comparison) == 2
        assert comparison[0][0] == "good"  # 好的应该排第一

    def test_multiple_trackers(self):
        """测试多个跟踪器"""
        evaluator = TrackingEvaluator()

        # 添加三个跟踪器
        for i in range(10):
            gt = (100, 100, 50, 50)
            evaluator.add_frame("tracker1", gt, gt)
            evaluator.add_frame("tracker2", (110, 110, 50, 50), gt)
            evaluator.add_frame("tracker3", (200, 200, 50, 50), gt)

        all_results = evaluator.evaluate_all()
        assert len(all_results) == 3

    def test_print_summary(self, capsys):
        """测试打印摘要"""
        evaluator = TrackingEvaluator()

        for i in range(10):
            evaluator.add_frame("test", (100, 100, 50, 50), (100, 100, 50, 50))

        evaluator.print_summary()
        captured = capsys.readouterr()
        assert "跟踪评估结果摘要" in captured.out


class TestOPEBenchmark:
    """OPE基准测试类"""

    def test_run(self):
        """测试运行"""
        # 创建简单的跟踪器
        class SimpleTracker:
            def __init__(self):
                self.bbox = None

            def init(self, frame, bbox):
                self.bbox = bbox
                return True

            def update(self, frame):
                # 返回相同的边界框
                return TrackingResult(
                    bbox=self.bbox,
                    confidence=1.0,
                    center=(self.bbox[0] + self.bbox[2]/2,
                           self.bbox[1] + self.bbox[3]/2)
                )

        from src.correlation_filter import TrackingResult

        benchmark = OPEBenchmark()

        # 创建序列
        sequence = [np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(10)]
        ground_truth = [(10, 10, 20, 20)] * 10

        tracker = SimpleTracker()
        result = benchmark.run(tracker, sequence, ground_truth, "simple")

        assert "average_iou" in result
        assert result["average_iou"] > 0.99


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
