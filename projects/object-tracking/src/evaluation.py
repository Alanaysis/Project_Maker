"""
Tracking Evaluation Metrics

跟踪评估指标实现，用于评估目标跟踪算法的性能。

常用指标:
- IoU (Intersection over Union): 边界框重叠度
- Center Error: 中心点距离误差
- Precision: 精度图 (阈值范围内的成功率)
- Success Rate: 成功率 (IoU阈值)
- FPS: 跟踪速度
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class TrackingMetrics:
    """跟踪评估指标"""
    iou_scores: List[float] = field(default_factory=list)
    center_errors: List[float] = field(default_factory=list)
    frame_times: List[float] = field(default_factory=list)
    num_frames: int = 0
    num_lost: int = 0


def compute_iou(
    bbox1: Tuple[int, int, int, int],
    bbox2: Tuple[int, int, int, int]
) -> float:
    """计算两个边界框的IoU (Intersection over Union)

    Args:
        bbox1: 边界框1 (x, y, w, h)
        bbox2: 边界框2 (x, y, w, h)

    Returns:
        IoU值 [0, 1]
    """
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2

    # 转换为 (x1, y1, x2, y2) 格式
    box1 = (x1, y1, x1 + w1, y1 + h1)
    box2 = (x2, y2, x2 + w2, y2 + h2)

    # 计算交集
    x_left = max(box1[0], box2[0])
    y_top = max(box1[1], box2[1])
    x_right = min(box1[2], box2[2])
    y_bottom = min(box1[3], box2[3])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection = (x_right - x_left) * (y_bottom - y_top)

    # 计算并集
    area1 = w1 * h1
    area2 = w2 * h2
    union = area1 + area2 - intersection

    if union <= 0:
        return 0.0

    return intersection / union


def compute_center_error(
    bbox1: Tuple[int, int, int, int],
    bbox2: Tuple[int, int, int, int]
) -> float:
    """计算两个边界框的中心点距离

    Args:
        bbox1: 边界框1 (x, y, w, h)
        bbox2: 边界框2 (x, y, w, h)

    Returns:
        中心点距离 (像素)
    """
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2

    cx1, cy1 = x1 + w1 / 2, y1 + h1 / 2
    cx2, cy2 = x2 + w2 / 2, y2 + h2 / 2

    return np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)


def compute_precision(
    center_errors: List[float],
    thresholds: List[float] = None
) -> Tuple[List[float], List[float]]:
    """计算精度图

    精度 = 中心误差小于阈值的帧比例

    Args:
        center_errors: 中心误差列表
        thresholds: 阈值列表 (默认0-50像素)

    Returns:
        (thresholds, precisions) 阈值和对应的精度
    """
    if thresholds is None:
        thresholds = list(range(0, 51))

    precisions = []
    n = len(center_errors)

    for threshold in thresholds:
        count = sum(1 for e in center_errors if e <= threshold)
        precisions.append(count / n if n > 0 else 0.0)

    return thresholds, precisions


def compute_success_rate(
    iou_scores: List[float],
    thresholds: List[float] = None
) -> Tuple[List[float], List[float]]:
    """计算成功率

    成功率 = IoU大于阈值的帧比例

    Args:
        iou_scores: IoU分数列表
        thresholds: 阈值列表 (默认0-1)

    Returns:
        (thresholds, success_rates) 阈值和对应的成功率
    """
    if thresholds is None:
        thresholds = [i / 100 for i in range(101)]

    success_rates = []
    n = len(iou_scores)

    for threshold in thresholds:
        count = sum(1 for s in iou_scores if s >= threshold)
        success_rates.append(count / n if n > 0 else 0.0)

    return thresholds, success_rates


def compute_average_precision(precisions: List[float]) -> float:
    """计算平均精度 (AP)

    Args:
        precisions: 精度列表

    Returns:
        平均精度
    """
    return np.mean(precisions)


def compute_area_under_curve(
    x: List[float],
    y: List[float]
) -> float:
    """计算曲线下面积 (AUC)

    Args:
        x: x轴值
        y: y轴值

    Returns:
        AUC值
    """
    # NumPy 2.0 compatibility
    if hasattr(np, 'trapezoid'):
        return np.trapezoid(y, x)
    else:
        return np.trapz(y, x)


def compute_fps(frame_times: List[float]) -> float:
    """计算跟踪速度 (FPS)

    Args:
        frame_times: 每帧处理时间列表

    Returns:
        FPS值
    """
    if not frame_times or sum(frame_times) <= 0:
        return 0.0
    return len(frame_times) / sum(frame_times)


class TrackingEvaluator:
    """跟踪评估器

    用于评估跟踪算法的整体性能。
    """

    def __init__(self):
        """初始化评估器"""
        self.results: Dict[str, TrackingMetrics] = {}

    def add_frame(
        self,
        tracker_name: str,
        pred_bbox: Tuple[int, int, int, int],
        gt_bbox: Tuple[int, int, int, int],
        frame_time: float = 0.0
    ):
        """添加一帧的跟踪结果

        Args:
            tracker_name: 跟踪器名称
            pred_bbox: 预测边界框 (x, y, w, h)
            gt_bbox: 真实边界框 (x, y, w, h)
            frame_time: 处理时间 (秒)
        """
        if tracker_name not in self.results:
            self.results[tracker_name] = TrackingMetrics()

        metrics = self.results[tracker_name]

        # 计算IoU
        iou = compute_iou(pred_bbox, gt_bbox)
        metrics.iou_scores.append(iou)

        # 计算中心误差
        error = compute_center_error(pred_bbox, gt_bbox)
        metrics.center_errors.append(error)

        # 记录时间
        metrics.frame_times.append(frame_time)
        metrics.num_frames += 1

        # 检查是否丢失 (IoU < 0.1)
        if iou < 0.1:
            metrics.num_lost += 1

    def evaluate(
        self,
        tracker_name: str
    ) -> Dict[str, float]:
        """评估指定跟踪器

        Args:
            tracker_name: 跟踪器名称

        Returns:
            评估指标字典
        """
        if tracker_name not in self.results:
            return {}

        metrics = self.results[tracker_name]

        # 精度图
        _, precisions = compute_precision(metrics.center_errors)
        avg_precision = compute_average_precision(precisions)

        # 成功率
        _, success_rates = compute_success_rate(metrics.iou_scores)
        auc_success = compute_area_under_curve(
            [i/100 for i in range(101)],
            success_rates
        )

        # 其他指标
        avg_iou = np.mean(metrics.iou_scores) if metrics.iou_scores else 0.0
        avg_center_error = np.mean(metrics.center_errors) if metrics.center_errors else 0.0
        fps = compute_fps(metrics.frame_times)

        return {
            "average_precision": avg_precision,
            "success_auc": auc_success,
            "average_iou": avg_iou,
            "average_center_error": avg_center_error,
            "fps": fps,
            "num_frames": metrics.num_frames,
            "num_lost": metrics.num_lost,
            "lost_rate": metrics.num_lost / metrics.num_frames if metrics.num_frames > 0 else 0.0
        }

    def evaluate_all(self) -> Dict[str, Dict[str, float]]:
        """评估所有跟踪器

        Returns:
            所有跟踪器的评估结果
        """
        results = {}
        for name in self.results:
            results[name] = self.evaluate(name)
        return results

    def compare(
        self,
        metric: str = "average_precision"
    ) -> List[Tuple[str, float]]:
        """比较所有跟踪器

        Args:
            metric: 比较的指标

        Returns:
            排序后的 (名称, 分数) 列表
        """
        scores = []
        for name in self.results:
            eval_result = self.evaluate(name)
            if metric in eval_result:
                scores.append((name, eval_result[metric]))

        # 降序排序
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def print_summary(self):
        """打印评估摘要"""
        print("\n" + "=" * 70)
        print("跟踪评估结果摘要")
        print("=" * 70)

        all_results = self.evaluate_all()

        for name, metrics in all_results.items():
            print(f"\n跟踪器: {name}")
            print("-" * 40)
            print(f"  平均精度 (AP):        {metrics['average_precision']:.4f}")
            print(f"  成功率 AUC:           {metrics['success_auc']:.4f}")
            print(f"  平均 IoU:             {metrics['average_iou']:.4f}")
            print(f"  平均中心误差:         {metrics['average_center_error']:.2f} 像素")
            print(f"  FPS:                  {metrics['fps']:.1f}")
            print(f"  帧数:                 {metrics['num_frames']}")
            print(f"  丢失次数:             {metrics['num_lost']}")
            print(f"  丢失率:               {metrics['lost_rate']:.2%}")


class OPEBenchmark:
    """OPE (One-Pass Evaluation) 基准测试

    标准的跟踪评估协议。
    """

    def __init__(self):
        """初始化OPE基准测试"""
        self.evaluator = TrackingEvaluator()

    def run(
        self,
        tracker,
        sequence: List[np.ndarray],
        ground_truth: List[Tuple[int, int, int, int]],
        name: str = "tracker"
    ) -> Dict[str, float]:
        """运行OPE评估

        Args:
            tracker: 跟踪器实例 (需要 init 和 update 方法)
            sequence: 视频帧序列
            ground_truth: 真实标注序列 [(x, y, w, h), ...]
            name: 跟踪器名称

        Returns:
            评估指标
        """
        import time

        if len(sequence) != len(ground_truth):
            raise ValueError("序列长度和标注长度不匹配")

        # 初始化
        frame = sequence[0]
        bbox = ground_truth[0]
        tracker.init(frame, bbox)

        # 逐帧跟踪
        for i in range(1, len(sequence)):
            frame = sequence[i]
            gt_bbox = ground_truth[i]

            start_time = time.time()
            result = tracker.update(frame)
            frame_time = time.time() - start_time

            self.evaluator.add_frame(
                name,
                result.bbox,
                gt_bbox,
                frame_time
            )

        return self.evaluator.evaluate(name)

    def run_multiple(
        self,
        trackers: Dict[str, object],
        sequence: List[np.ndarray],
        ground_truth: List[Tuple[int, int, int, int]]
    ) -> Dict[str, Dict[str, float]]:
        """运行多个跟踪器的OPE评估

        Args:
            trackers: 跟踪器字典 {名称: 跟踪器实例}
            sequence: 视频帧序列
            ground_truth: 真实标注序列

        Returns:
            所有跟踪器的评估结果
        """
        results = {}
        for name, tracker in trackers.items():
            results[name] = self.run(tracker, sequence, ground_truth, name)
        return results


if __name__ == "__main__":
    # 测试评估函数
    print("跟踪评估指标测试")
    print("=" * 50)

    # 测试IoU计算
    bbox1 = (100, 100, 50, 50)
    bbox2 = (120, 120, 50, 50)
    iou = compute_iou(bbox1, bbox2)
    print(f"IoU测试: {iou:.4f}")

    # 测试中心误差
    error = compute_center_error(bbox1, bbox2)
    print(f"中心误差测试: {error:.2f} 像素")

    # 测试评估器
    evaluator = TrackingEvaluator()

    # 模拟跟踪结果
    for i in range(20):
        gt = (100 + 5*i, 100 + 3*i, 50, 50)
        pred = (100 + 5*i + np.random.randint(-5, 5),
                100 + 3*i + np.random.randint(-5, 5),
                50, 50)
        evaluator.add_frame("MOSSE", pred, gt, 0.01)
        evaluator.add_frame("KCF", pred, gt, 0.015)

    evaluator.print_summary()
