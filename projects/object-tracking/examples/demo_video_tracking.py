"""
视频跟踪综合演示

演示完整的视频目标跟踪流程:
1. 创建合成视频
2. 初始化跟踪器
3. 执行跟踪
4. 评估性能
5. 保存结果
"""

import numpy as np
import cv2
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.video_tracker import VideoTracker, MultiObjectTracker, create_synthetic_video
from src.correlation_filter import MOSSETracker
from src.evaluation import TrackingEvaluator


def demo_single_object_tracking():
    """单目标跟踪演示"""
    print("=" * 60)
    print("单目标跟踪演示")
    print("=" * 60)

    # 1. 创建合成视频
    print("\n1. 创建合成视频...")
    video_path = "test_video.avi"
    trajectory = create_synthetic_video(
        video_path,
        width=640,
        height=480,
        num_frames=150,
        target_size=(50, 50),
        motion_type="circular"
    )
    print(f"   视频已保存: {video_path}")
    print(f"   帧数: {len(trajectory)}")

    # 2. 初始化跟踪器
    print("\n2. 初始化跟踪器...")
    tracker = VideoTracker(
        tracker_type="mosse",
        use_kalman=True,
        show_visualization=False,
        output_path="output_tracking.avi"
    )

    # 3. 处理视频
    print("\n3. 处理视频...")
    cap = cv2.VideoCapture(video_path)

    # 读取第一帧
    ret, frame = cap.read()
    if not ret:
        print("无法读取视频")
        return

    # 初始化跟踪
    init_bbox = trajectory[0]
    tracker.init(frame, init_bbox)
    print(f"   初始目标: {init_bbox}")

    # 评估器
    evaluator = TrackingEvaluator()

    # 跟踪循环
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 更新跟踪
        success, bbox = tracker.update(frame)
        frame_count += 1

        if success and frame_count < len(trajectory):
            gt_bbox = trajectory[frame_count]

            # 记录评估
            evaluator.add_frame("MOSSE+Kalman", bbox, gt_bbox)

            # 可视化
            vis = tracker.draw_visualization(
                frame, bbox,
                confidence=tracker.history[-1]["confidence"]
            )

            # 绘制真实框
            x, y, w, h = gt_bbox
            cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # 显示
            cv2.imshow("Tracking Demo", vis)
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q'):
                break
        else:
            break

    cap.release()
    cv2.destroyAllWindows()

    # 4. 评估结果
    print("\n4. 评估结果...")
    evaluator.print_summary()

    # 5. 保存历史
    print("\n5. 保存跟踪历史...")
    tracker.save_history("tracking_history.json")
    print("   历史已保存: tracking_history.json")

    return evaluator


def demo_multi_object_tracking():
    """多目标跟踪演示"""
    print("\n" + "=" * 60)
    print("多目标跟踪演示")
    print("=" * 60)

    # 1. 创建视频
    print("\n1. 创建视频...")
    video_path = "multi_target_video.avi"
    create_synthetic_video(
        video_path,
        width=640,
        height=480,
        num_frames=100,
        target_size=(30, 30),
        motion_type="linear"
    )

    # 2. 初始化多目标跟踪器
    print("\n2. 初始化多目标跟踪器...")
    multi_tracker = MultiObjectTracker(tracker_type="mosse")

    # 3. 处理视频
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()

    if not ret:
        print("无法读取视频")
        return

    # 添加多个目标
    targets = [
        (100, 100, 30, 30),
        (200, 200, 30, 30),
        (300, 150, 30, 30)
    ]

    for target in targets:
        target_id = multi_tracker.add_target(frame, target)
        print(f"   添加目标 {target_id}: {target}")

    # 跟踪循环
    print("\n3. 开始多目标跟踪...")
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 更新所有跟踪器
        results = multi_tracker.update(frame)
        frame_count += 1

        # 可视化
        vis = multi_tracker.draw_visualization(frame)

        # 显示
        cv2.imshow("Multi-Object Tracking", vis)
        key = cv2.waitKey(30) & 0xFF
        if key == ord('q'):
            break

        if frame_count % 20 == 0:
            for tid, (success, bbox) in results.items():
                print(f"   帧{frame_count} 目标{tid}: success={success}")

    cap.release()
    cv2.destroyAllWindows()

    print("\n多目标跟踪完成!")


def demo_tracking_evaluation():
    """跟踪评估演示"""
    print("\n" + "=" * 60)
    print("跟踪评估演示")
    print("=" * 60)

    # 1. 创建测试序列
    print("\n1. 创建测试序列...")
    video_path = "eval_test.avi"
    trajectory = create_synthetic_video(
        video_path,
        width=400,
        height=400,
        num_frames=80,
        target_size=(40, 40),
        motion_type="circular"
    )

    # 2. 运行不同的跟踪器
    print("\n2. 运行跟踪器...")
    evaluators = {}

    # MOSSE (高学习率)
    print("   运行 MOSSE (高学习率)...")
    tracker1 = MOSSETracker(learning_rate=0.3)
    evaluator1 = TrackingEvaluator()

    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    tracker1.init(frame, trajectory[0])

    for i in range(1, len(trajectory)):
        ret, frame = cap.read()
        if not ret:
            break
        result = tracker1.update(frame)
        evaluator1.add_frame("MOSSE-High", result.bbox, trajectory[i])

    cap.release()
    evaluators["MOSSE-High"] = evaluator1

    # MOSSE (低学习率)
    print("   运行 MOSSE (低学习率)...")
    tracker2 = MOSSETracker(learning_rate=0.1)
    evaluator2 = TrackingEvaluator()

    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    tracker2.init(frame, trajectory[0])

    for i in range(1, len(trajectory)):
        ret, frame = cap.read()
        if not ret:
            break
        result = tracker2.update(frame)
        evaluator2.add_frame("MOSSE-Low", result.bbox, trajectory[i])

    cap.release()
    evaluators["MOSSE-Low"] = evaluator2

    # 3. 比较结果
    print("\n3. 比较结果...")
    for name, evaluator in evaluators.items():
        print(f"\n{name}:")
        result = evaluator.evaluate(name.split('-')[0])
        print(f"   平均IoU: {result['average_iou']:.4f}")
        print(f"   平均中心误差: {result['average_center_error']:.2f} 像素")

    # 4. 打印详细摘要
    print("\n4. 详细评估摘要...")
    for evaluator in evaluators.values():
        evaluator.print_summary()


def demo_real_time_tracking():
    """实时跟踪演示 (使用摄像头)"""
    print("\n" + "=" * 60)
    print("实时跟踪演示")
    print("=" * 60)
    print("\n注意: 此演示需要摄像头")
    print("按 'q' 退出，按 'r' 重新选择目标")

    # 检查摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("\n无法打开摄像头，跳过此演示")
        return

    # 初始化跟踪器
    tracker = VideoTracker(
        tracker_type="mosse",
        use_kalman=True,
        show_visualization=True
    )

    # 读取第一帧
    ret, frame = cap.read()
    if not ret:
        print("无法读取摄像头")
        return

    # 选择目标
    print("\n请用鼠标框选目标...")
    bbox = cv2.selectROI("Select Target", frame, fromCenter=False)
    cv2.destroyWindow("Select Target")

    # 初始化跟踪
    tracker.init(frame, bbox)
    print(f"目标已选择: {bbox}")

    # 跟踪循环
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 更新跟踪
        success, bbox = tracker.update(frame)

        if success:
            # 可视化
            vis = tracker.draw_visualization(
                frame, bbox,
                confidence=tracker.history[-1]["confidence"]
            )

            cv2.imshow("Real-Time Tracking", vis)
        else:
            cv2.imshow("Real-Time Tracking", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            # 重新选择目标
            bbox = cv2.selectROI("Select Target", frame, fromCenter=False)
            cv2.destroyWindow("Select Target")
            tracker.init(frame, bbox)
            print(f"目标已重新选择: {bbox}")

    cap.release()
    cv2.destroyAllWindows()

    print("\n实时跟踪结束!")
    print(f"跟踪帧数: {len(tracker.history)}")


def main():
    """主函数"""
    print("=" * 60)
    print("目标跟踪综合演示")
    print("=" * 60)

    # 1. 单目标跟踪
    demo_single_object_tracking()

    # 2. 多目标跟踪
    demo_multi_object_tracking()

    # 3. 跟踪评估
    demo_tracking_evaluation()

    # 4. 实时跟踪 (可选)
    print("\n是否运行实时摄像头演示? (需要摄像头)")
    response = input("输入 'y' 运行，其他跳过: ")
    if response.lower() == 'y':
        demo_real_time_tracking()

    print("\n" + "=" * 60)
    print("所有演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
