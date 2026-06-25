"""
Video Tracking Demo

视频跟踪演示模块，提供完整的视频目标跟踪功能。

功能:
- 从视频文件或摄像头读取帧
- 支持手动选择初始目标
- 实时跟踪显示
- 跟踪结果保存
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List, Dict
from pathlib import Path
import json

from .correlation_filter import MOSSETracker, KCFTracker, TrackingResult
from .kalman_filter import KalmanFilter


class VideoTracker:
    """视频目标跟踪器

    整合相关滤波和卡尔曼滤波的完整跟踪系统。
    """

    def __init__(
        self,
        tracker_type: str = "mosse",
        use_kalman: bool = True,
        show_visualization: bool = True,
        output_path: Optional[str] = None
    ):
        """初始化视频跟踪器

        Args:
            tracker_type: 跟踪器类型 ("mosse" 或 "kcf")
            use_kalman: 是否使用卡尔曼滤波平滑
            show_visualization: 是否显示可视化窗口
            output_path: 输出视频路径
        """
        self.tracker_type = tracker_type
        self.use_kalman = use_kalman
        self.show_visualization = show_visualization
        self.output_path = output_path

        # 初始化跟踪器
        if tracker_type == "mosse":
            self.tracker = MOSSETracker(learning_rate=0.2)
        elif tracker_type == "kcf":
            self.tracker = KCFTracker()
        else:
            raise ValueError(f"不支持的跟踪器类型: {tracker_type}")

        # 卡尔曼滤波器
        self.kalman: Optional[KalmanFilter] = None
        if use_kalman:
            self.kalman = KalmanFilter(dt=1.0, process_noise=1e-2, measurement_noise=1.0)

        # 跟踪状态
        self.initialized = False
        self.bbox: Optional[Tuple[int, int, int, int]] = None
        self.center: Optional[Tuple[float, float]] = None
        self.trajectory: List[Tuple[float, float]] = []

        # 视频写入器
        self.writer: Optional[cv2.VideoWriter] = None

        # 跟踪历史
        self.history: List[Dict] = []

    def select_target(
        self,
        frame: np.ndarray,
        window_name: str = "Select Target"
    ) -> Tuple[int, int, int, int]:
        """手动选择目标

        Args:
            frame: 输入帧
            window_name: 窗口名称

        Returns:
            选择的边界框 (x, y, w, h)
        """
        print("请用鼠标框选目标区域，然后按回车确认")
        bbox = cv2.selectROI(window_name, frame, fromCenter=False, showCrosshair=True)
        cv2.destroyWindow(window_name)
        return bbox

    def init(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> bool:
        """初始化跟踪

        Args:
            frame: 初始帧
            bbox: 初始目标边界框 (x, y, w, h)

        Returns:
            初始化是否成功
        """
        self.bbox = bbox
        x, y, w, h = bbox
        self.center = (x + w / 2, y + h / 2)
        self.trajectory = [self.center]

        # 初始化跟踪器
        success = self.tracker.init(frame, bbox)

        if success and self.kalman:
            # 初始化卡尔曼滤波器
            self.kalman.set_state(self.center[0], self.center[1])

        self.initialized = success
        return success

    def update(
        self,
        frame: np.ndarray
    ) -> Tuple[bool, Tuple[int, int, int, int]]:
        """更新跟踪

        Args:
            frame: 当前帧

        Returns:
            (是否成功, 边界框)
        """
        if not self.initialized:
            return False, (0, 0, 0, 0)

        # 相关滤波跟踪
        result = self.tracker.update(frame)

        # 卡尔曼滤波平滑
        if self.kalman:
            self.kalman.predict()
            self.kalman.update(np.array(result.center))
            smooth_cx, smooth_cy = self.kalman.get_position()

            # 使用平滑后的位置
            w, h = self.bbox[2], self.bbox[3]
            new_x = int(smooth_cx - w / 2)
            new_y = int(smooth_cy - h / 2)
            self.bbox = (new_x, new_y, w, h)
            self.center = (smooth_cx, smooth_cy)
        else:
            self.bbox = result.bbox
            self.center = result.center

        # 记录轨迹
        self.trajectory.append(self.center)

        # 记录历史
        self.history.append({
            "bbox": self.bbox,
            "center": self.center,
            "confidence": result.confidence
        })

        return True, self.bbox

    def draw_visualization(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int],
        confidence: float = 0.0,
        show_trajectory: bool = True
    ) -> np.ndarray:
        """绘制可视化

        Args:
            frame: 输入帧
            bbox: 边界框
            confidence: 置信度
            show_trajectory: 是否显示轨迹

        Returns:
            绘制后的帧
        """
        vis = frame.copy()
        x, y, w, h = bbox

        # 绘制边界框
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # 绘制中心点
        cx, cy = int(x + w / 2), int(y + h / 2)
        cv2.circle(vis, (cx, cy), 3, (0, 0, 255), -1)

        # 显示置信度
        text = f"Conf: {confidence:.2f}"
        cv2.putText(vis, text, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # 绘制轨迹
        if show_trajectory and len(self.trajectory) > 1:
            for i in range(1, len(self.trajectory)):
                pt1 = (int(self.trajectory[i-1][0]), int(self.trajectory[i-1][1]))
                pt2 = (int(self.trajectory[i][0]), int(self.trajectory[i][1]))
                cv2.line(vis, pt1, pt2, (255, 0, 0), 2)

        return vis

    def process_video(
        self,
        video_path: str,
        initial_bbox: Optional[Tuple[int, int, int, int]] = None
    ) -> List[Dict]:
        """处理视频

        Args:
            video_path: 视频路径
            initial_bbox: 初始边界框 (如果为None则手动选择)

        Returns:
            跟踪历史
        """
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")

        # 读取第一帧
        ret, frame = cap.read()
        if not ret:
            raise ValueError("无法读取视频帧")

        # 初始化视频写入器
        if self.output_path:
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            fps = cap.get(cv2.CAP_PROP_FPS)
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.writer = cv2.VideoWriter(
                self.output_path, fourcc, fps, (w, h)
            )

        # 选择初始目标
        if initial_bbox is None:
            bbox = self.select_target(frame)
        else:
            bbox = initial_bbox

        # 初始化跟踪
        self.init(frame, bbox)
        print(f"初始化目标: bbox={bbox}")

        # 跟踪循环
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 更新跟踪
            success, bbox = self.update(frame)
            frame_count += 1

            if success:
                # 绘制可视化
                vis = self.draw_visualization(
                    frame, bbox,
                    confidence=self.history[-1]["confidence"]
                )

                # 显示
                if self.show_visualization:
                    cv2.imshow("Tracking", vis)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break

                # 写入输出
                if self.writer:
                    self.writer.write(vis)

                if frame_count % 30 == 0:
                    print(f"帧 {frame_count}: bbox={bbox}, "
                          f"conf={self.history[-1]['confidence']:.2f}")
            else:
                print(f"帧 {frame_count}: 跟踪失败")
                break

        # 清理
        cap.release()
        if self.writer:
            self.writer.release()
        if self.show_visualization:
            cv2.destroyAllWindows()

        return self.history

    def process_camera(
        self,
        camera_id: int = 0
    ) -> List[Dict]:
        """处理摄像头

        Args:
            camera_id: 摄像头ID

        Returns:
            跟踪历史
        """
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            raise ValueError(f"无法打开摄像头: {camera_id}")

        # 读取第一帧
        ret, frame = cap.read()
        if not ret:
            raise ValueError("无法读取摄像头帧")

        # 选择目标
        bbox = self.select_target(frame)
        self.init(frame, bbox)

        print("开始跟踪，按 'q' 退出，按 'r' 重新选择目标")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 更新跟踪
            success, bbox = self.update(frame)

            if success:
                # 绘制可视化
                vis = self.draw_visualization(
                    frame, bbox,
                    confidence=self.history[-1]["confidence"]
                )

                # 显示
                cv2.imshow("Camera Tracking", vis)
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    break
                elif key == ord('r'):
                    # 重新选择目标
                    bbox = self.select_target(frame)
                    self.init(frame, bbox)
            else:
                print("跟踪失败，按 'r' 重新选择目标")
                cv2.imshow("Camera Tracking", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    bbox = self.select_target(frame)
                    self.init(frame, bbox)

        cap.release()
        cv2.destroyAllWindows()

        return self.history

    def save_history(self, path: str):
        """保存跟踪历史

        Args:
            path: 保存路径
        """
        data = []
        for h in self.history:
            data.append({
                "bbox": list(h["bbox"]),
                "center": list(h["center"]),
                "confidence": h["confidence"]
            })

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_history(self, path: str):
        """加载跟踪历史

        Args:
            path: 历史文件路径
        """
        with open(path, 'r') as f:
            data = json.load(f)

        self.history = []
        for d in data:
            self.history.append({
                "bbox": tuple(d["bbox"]),
                "center": tuple(d["center"]),
                "confidence": d["confidence"]
            })


class MultiObjectTracker:
    """多目标跟踪器

    支持同时跟踪多个目标。
    """

    def __init__(self, tracker_type: str = "mosse"):
        """初始化多目标跟踪器

        Args:
            tracker_type: 跟踪器类型
        """
        self.tracker_type = tracker_type
        self.trackers: Dict[int, VideoTracker] = {}
        self.next_id = 0

    def add_target(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> int:
        """添加跟踪目标

        Args:
            frame: 当前帧
            bbox: 目标边界框

        Returns:
            目标ID
        """
        tracker = VideoTracker(
            tracker_type=self.tracker_type,
            use_kalman=True,
            show_visualization=False
        )
        success = tracker.init(frame, bbox)

        if success:
            target_id = self.next_id
            self.trackers[target_id] = tracker
            self.next_id += 1
            return target_id

        return -1

    def remove_target(self, target_id: int):
        """移除跟踪目标

        Args:
            target_id: 目标ID
        """
        if target_id in self.trackers:
            del self.trackers[target_id]

    def update(
        self,
        frame: np.ndarray
    ) -> Dict[int, Tuple[bool, Tuple[int, int, int, int]]]:
        """更新所有跟踪器

        Args:
            frame: 当前帧

        Returns:
            {目标ID: (是否成功, 边界框)}
        """
        results = {}
        for target_id, tracker in self.trackers.items():
            success, bbox = tracker.update(frame)
            results[target_id] = (success, bbox)
        return results

    def draw_visualization(
        self,
        frame: np.ndarray,
        show_ids: bool = True
    ) -> np.ndarray:
        """绘制所有目标的可视化

        Args:
            frame: 输入帧
            show_ids: 是否显示目标ID

        Returns:
            绘制后的帧
        """
        vis = frame.copy()
        colors = [
            (0, 255, 0), (255, 0, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255)
        ]

        for target_id, tracker in self.trackers.items():
            if tracker.bbox:
                x, y, w, h = tracker.bbox
                color = colors[target_id % len(colors)]

                # 绘制边界框
                cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)

                # 显示ID
                if show_ids:
                    text = f"ID: {target_id}"
                    cv2.putText(vis, text, (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

                # 绘制轨迹
                if len(tracker.trajectory) > 1:
                    for i in range(1, len(tracker.trajectory)):
                        pt1 = (int(tracker.trajectory[i-1][0]),
                               int(tracker.trajectory[i-1][1]))
                        pt2 = (int(tracker.trajectory[i][0]),
                               int(tracker.trajectory[i][1]))
                        cv2.line(vis, pt1, pt2, color, 1)

        return vis


def create_synthetic_video(
    output_path: str,
    width: int = 640,
    height: int = 480,
    num_frames: int = 100,
    target_size: Tuple[int, int] = (40, 40),
    motion_type: str = "linear"
) -> List[Tuple[int, int, int, int]]:
    """创建合成测试视频

    Args:
        output_path: 输出路径
        width: 视频宽度
        height: 视频高度
        num_frames: 帧数
        target_size: 目标大小
        motion_type: 运动类型 ("linear", "circular", "random")

    Returns:
        目标轨迹 [(x, y, w, h), ...]
    """
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    fps = 30
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    w, h = target_size
    cx, cy = width // 2, height // 2
    trajectory = []

    for i in range(num_frames):
        # 创建背景
        frame = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)

        # 更新目标位置
        if motion_type == "linear":
            cx += 3
            cy += 2
            # 边界反弹
            if cx < w or cx > width - w:
                cx = np.clip(cx, w, width - w)
            if cy < h or cy > height - h:
                cy = np.clip(cy, h, height - h)
        elif motion_type == "circular":
            radius = 100
            cx = width // 2 + int(radius * np.cos(2 * np.pi * i / num_frames))
            cy = height // 2 + int(radius * np.sin(2 * np.pi * i / num_frames))
        elif motion_type == "random":
            cx += np.random.randint(-5, 6)
            cy += np.random.randint(-5, 6)
            cx = np.clip(cx, w, width - w)
            cy = np.clip(cy, h, height - h)

        # 绘制目标
        x, y = int(cx - w / 2), int(cy - h / 2)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), -1)

        # 添加噪声
        noise = np.random.randint(0, 30, frame.shape, dtype=np.uint8)
        frame = cv2.add(frame, noise)

        writer.write(frame)
        trajectory.append((x, y, w, h))

    writer.release()
    return trajectory


if __name__ == "__main__":
    # 创建合成视频
    print("创建合成测试视频...")
    video_path = "test_video.avi"
    trajectory = create_synthetic_video(
        video_path,
        width=640,
        height=480,
        num_frames=100,
        motion_type="circular"
    )

    print(f"视频已保存: {video_path}")
    print(f"轨迹点数: {len(trajectory)}")
    print(f"初始位置: {trajectory[0]}")
    print(f"最终位置: {trajectory[-1]}")
