"""
相关滤波跟踪演示

演示MOSSE和KCF相关滤波跟踪器:
1. 创建合成测试序列
2. 初始化跟踪器
3. 执行跟踪
4. 评估和可视化结果
"""

import numpy as np
import cv2
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.correlation_filter import MOSSETracker, KCFTracker
from src.evaluation import TrackingEvaluator, compute_iou, compute_center_error


def create_sequence(
    n_frames: int = 100,
    width: int = 400,
    height: int = 400,
    target_size: tuple = (40, 40),
    motion_type: str = "linear"
) -> tuple:
    """创建测试序列

    Args:
        n_frames: 帧数
        width: 帧宽度
        height: 帧高度
        target_size: 目标大小
        motion_type: 运动类型

    Returns:
        (frames, bboxes) 帧序列和边界框序列
    """
    w, h = target_size
    frames = []
    bboxes = []

    # 初始位置
    cx, cy = width // 4, height // 2

    for i in range(n_frames):
        # 创建背景
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # 更新位置
        if motion_type == "linear":
            cx += 3
            cy += 1
        elif motion_type == "circular":
            radius = 80
            cx = width // 2 + int(radius * np.cos(2 * np.pi * i / n_frames))
            cy = height // 2 + int(radius * np.sin(2 * np.pi * i / n_frames))
        elif motion_type == "random":
            cx += np.random.randint(-5, 6)
            cy += np.random.randint(-5, 6)

        # 边界检查
        cx = np.clip(cx, w, width - w)
        cy = np.clip(cy, h, height - h)

        # 绘制目标
        x = int(cx - w / 2)
        y = int(cy - h / 2)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), -1)

        # 添加噪声
        noise = np.random.randint(0, 20, frame.shape, dtype=np.uint8)
        frame = cv2.add(frame, noise)

        frames.append(frame)
        bboxes.append((x, y, w, h))

    return frames, bboxes


def run_tracker(
    tracker,
    frames: list,
    init_bbox: tuple
) -> list:
    """运行跟踪器

    Args:
        tracker: 跟踪器实例
        frames: 帧序列
        init_bbox: 初始边界框

    Returns:
        跟踪结果列表
    """
    results = []

    # 初始化
    tracker.init(frames[0], init_bbox)

    # 跟踪
    for i in range(1, len(frames)):
        result = tracker.update(frames[i])
        results.append(result)

    return results


def visualize_tracking(
    frames: list,
    results: list,
    ground_truth: list,
    window_name: str = "Tracking",
    delay: int = 30
):
    """可视化跟踪结果

    Args:
        frames: 帧序列
        results: 跟踪结果
        ground_truth: 真实标注
        window_name: 窗口名称
        delay: 帧间延迟 (ms)
    """
    for i, (frame, result, gt) in enumerate(zip(frames[1:], results, ground_truth[1:])):
        vis = frame.copy()

        # 绘制真实边界框 (绿色)
        x, y, w, h = gt
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # 绘制预测边界框 (红色)
        x, y, w, h = result.bbox
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # 显示信息
        iou = compute_iou(result.bbox, gt)
        error = compute_center_error(result.bbox, gt)

        text = f"Frame: {i+1} | IoU: {iou:.2f} | Error: {error:.1f}px"
        cv2.putText(vis, text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow(window_name, vis)
        key = cv2.waitKey(delay) & 0xFF
        if key == ord('q'):
            break

    cv2.destroyAllWindows()


def evaluate_tracker(
    results: list,
    ground_truth: list,
    tracker_name: str
) -> dict:
    """评估跟踪器

    Args:
        results: 跟踪结果
        ground_truth: 真实标注
        tracker_name: 跟踪器名称

    Returns:
        评估指标
    """
    evaluator = TrackingEvaluator()

    for result, gt in zip(results, ground_truth[1:]):
        evaluator.add_frame(
            tracker_name,
            result.bbox,
            gt,
            0.01  # 假设每帧10ms
        )

    return evaluator.evaluate(tracker_name)


def plot_comparison(
    mosse_metrics: dict,
    kcf_metrics: dict
):
    """绘制比较图

    Args:
        mosse_metrics: MOSSE指标
        kcf_metrics: KCF指标
    """
    try:
        import matplotlib.pyplot as plt

        metrics = ['average_iou', 'average_center_error', 'fps']
        labels = ['平均IoU', '平均中心误差', 'FPS']

        fig, axes = plt.subplots(1, 3, figsize=(12, 4))
        fig.suptitle('MOSSE vs KCF 性能比较', fontsize=14)

        for ax, metric, label in zip(axes, metrics, labels):
            values = [mosse_metrics[metric], kcf_metrics[metric]]
            bars = ax.bar(['MOSSE', 'KCF'], values, color=['blue', 'orange'])

            ax.set_ylabel(label)
            ax.set_title(label)

            # 添加数值标签
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'{val:.2f}', ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig('tracker_comparison.png', dpi=150, bbox_inches='tight')
        plt.show()
        print("\n比较图已保存: tracker_comparison.png")

    except ImportError:
        print("\nmatplotlib未安装，跳过绘图")


def main():
    """主函数"""
    print("=" * 60)
    print("相关滤波跟踪演示")
    print("=" * 60)

    # 1. 创建测试序列
    print("\n1. 创建测试序列...")
    motion_types = ["linear", "circular"]

    for motion_type in motion_types:
        print(f"\n--- {motion_type} 运动 ---")

        frames, bboxes = create_sequence(
            n_frames=100,
            width=400,
            height=400,
            motion_type=motion_type
        )

        print(f"  序列长度: {len(frames)} 帧")
        print(f"  初始目标: {bboxes[0]}")
        print(f"  最终目标: {bboxes[-1]}")

        # 2. 运行MOSSE跟踪器
        print("\n  运行MOSSE跟踪器...")
        mosse = MOSSETracker(learning_rate=0.25)
        mosse_results = run_tracker(mosse, frames, bboxes[0])
        mosse_metrics = evaluate_tracker(mosse_results, bboxes, "MOSSE")

        print(f"    平均IoU: {mosse_metrics['average_iou']:.4f}")
        print(f"    平均中心误差: {mosse_metrics['average_center_error']:.2f} 像素")
        print(f"    FPS: {mosse_metrics['fps']:.1f}")

        # 3. 运行KCF跟踪器
        print("\n  运行KCF跟踪器...")
        kcf = KCFTracker()
        kcf_results = run_tracker(kcf, frames, bboxes[0])
        kcf_metrics = evaluate_tracker(kcf_results, bboxes, "KCF")

        print(f"    平均IoU: {kcf_metrics['average_iou']:.4f}")
        print(f"    平均中心误差: {kcf_metrics['average_center_error']:.2f} 像素")
        print(f"    FPS: {kcf_metrics['fps']:.1f}")

        # 4. 可视化
        print("\n  可视化MOSSE跟踪结果 (按q退出)...")
        visualize_tracking(frames, mosse_results, bboxes, "MOSSE Tracking")

        print("\n  可视化KCF跟踪结果 (按q退出)...")
        visualize_tracking(frames, kcf_results, bboxes, "KCF Tracking")

        # 5. 比较
        print("\n  绘制比较图...")
        plot_comparison(mosse_metrics, kcf_metrics)

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
