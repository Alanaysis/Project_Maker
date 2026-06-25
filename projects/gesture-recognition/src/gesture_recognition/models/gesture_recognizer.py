"""
Gesture Recognizer - 端到端手势识别系统

核心流程：
    图像输入 → 手部检测 → 关键点提取 → 手势分类 → 输出

学习要点：
- 理解端到端系统的组件集成
- 掌握管道(pipeline)设计模式
- 学会错误处理和状态管理
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

from gesture_recognition.models.hand_detector import HandDetector
from gesture_recognition.models.keypoint_extractor import KeypointExtractor
from gesture_recognition.models.gesture_classifier import GestureClassifier


@dataclass
class RecognitionResult:
    """
    识别结果数据结构

    包含单个手的完整识别信息
    """
    hand_id: int
    bbox: Tuple[int, int, int, int]
    center: Tuple[int, int]
    keypoints: np.ndarray
    keypoints_pixel: np.ndarray
    gesture: str
    gesture_zh: str
    confidence: float
    probabilities: Optional[Dict[str, float]] = None

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "hand_id": self.hand_id,
            "bbox": self.bbox,
            "center": self.center,
            "gesture": self.gesture,
            "gesture_zh": self.gesture_zh,
            "confidence": self.confidence,
        }


class GestureRecognizer:
    """
    手势识别器 - 端到端手势识别系统

    整合了三个核心组件：
    1. HandDetector - 手部检测
    2. KeypointExtractor - 关键点提取
    3. GestureClassifier - 手势分类

    使用示例：
        recognizer = GestureRecognizer()
        results = recognizer.recognize(image)
        for result in results:
            print(f"Hand {result.hand_id}: {result.gesture_zh}")
    """

    def __init__(
        self,
        use_neural_classifier: bool = False,
        device: str = "cpu",
    ):
        """
        初始化手势识别器

        Args:
            use_neural_classifier: 是否使用神经网络分类器（否则用规则方法）
            device: 推理设备
        """
        self.hand_detector = HandDetector()
        self.keypoint_extractor = KeypointExtractor(device=device)
        self.gesture_classifier = GestureClassifier(device=device)
        self.use_neural_classifier = use_neural_classifier

        # 手部颜色映射（用于可视化）
        self.hand_colors = [
            (0, 255, 0),    # 绿色 - 手1
            (255, 0, 0),    # 蓝色 - 手2
            (0, 0, 255),    # 红色 - 手3
            (255, 255, 0),  # 青色 - 手4
        ]

    def recognize(self, image: np.ndarray) -> List[RecognitionResult]:
        """
        识别图像中的手势

        Args:
            image: BGR格式的输入图像

        Returns:
            List[RecognitionResult]: 识别结果列表
        """
        results = []

        # 第1步：手部检测
        hands = self.hand_detector.detect(image)

        for i, hand in enumerate(hands):
            bbox = hand["bbox"]

            # 第2步：关键点提取
            keypoints_result = self.keypoint_extractor.extract(image, bbox)

            # 第3步：手势分类
            if self.use_neural_classifier:
                gesture_result = self.gesture_classifier.classify(
                    keypoints_result["keypoints"]
                )
            else:
                gesture_result = self.gesture_classifier.classify_rule_based(
                    keypoints_result["keypoints"]
                )

            # 组装结果
            result = RecognitionResult(
                hand_id=i,
                bbox=bbox,
                center=hand["center"],
                keypoints=keypoints_result["keypoints"],
                keypoints_pixel=keypoints_result["keypoints_pixel"],
                gesture=gesture_result["gesture"],
                gesture_zh=gesture_result["gesture_zh"],
                confidence=gesture_result["confidence"],
                probabilities=gesture_result.get("probabilities"),
            )

            results.append(result)

        return results

    def recognize_with_visualization(self, image: np.ndarray) -> Tuple[np.ndarray, List[RecognitionResult]]:
        """
        识别并返回带可视化的图像

        Args:
            image: BGR格式的输入图像

        Returns:
            Tuple[np.ndarray, List[RecognitionResult]]: (可视化图像, 识别结果)
        """
        results = self.recognize(image)
        vis_image = self._visualize(image, results)

        return vis_image, results

    def _visualize(self, image: np.ndarray, results: List[RecognitionResult]) -> np.ndarray:
        """
        在图像上绘制识别结果

        绘制内容：
        1. 手部边界框
        2. 关键点和骨架
        3. 手势标签和置信度
        """
        vis = image.copy()

        for i, result in enumerate(results):
            color = self.hand_colors[i % len(self.hand_colors)]

            # 绘制边界框
            x, y, w, h = result.bbox
            cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)

            # 绘制关键点
            for kp in result.keypoints_pixel:
                cv2.circle(vis, (int(kp[0]), int(kp[1])), 4, color, -1)

            # 绘制骨架连接
            for start_idx, end_idx in self.keypoint_extractor.CONNECTIONS:
                start = tuple(result.keypoints_pixel[start_idx].astype(int))
                end = tuple(result.keypoints_pixel[end_idx].astype(int))
                cv2.line(vis, start, end, color, 2)

            # 绘制手势标签
            label = f"{result.gesture_zh} ({result.confidence:.2f})"
            label_pos = (x, y - 10)
            cv2.putText(
                vis, label, label_pos,
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
            )

        return vis

    def process_video(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        show: bool = False,
    ) -> List[List[RecognitionResult]]:
        """
        处理视频流

        Args:
            video_path: 输入视频路径
            output_path: 输出视频路径（可选）
            show: 是否实时显示

        Returns:
            List[List[RecognitionResult]]: 每帧的识别结果
        """
        cap = cv2.VideoCapture(video_path)
        all_results = []

        # 获取视频属性
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # 创建视频写入器
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 识别
            vis_frame, results = self.recognize_with_visualization(frame)
            all_results.append(results)

            # 写入输出视频
            if writer:
                writer.write(vis_frame)

            # 实时显示
            if show:
                cv2.imshow("Gesture Recognition", vis_frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        cap.release()
        if writer:
            writer.release()
        if show:
            cv2.destroyAllWindows()

        return all_results

    def process_camera(
        self,
        camera_id: int = 0,
        output_path: Optional[str] = None,
    ):
        """
        处理摄像头实时流

        Args:
            camera_id: 摄像头ID
            output_path: 输出视频路径（可选）
        """
        cap = cv2.VideoCapture(camera_id)

        if not cap.isOpened():
            print("无法打开摄像头")
            return

        writer = None
        if output_path:
            fps = 30
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        print("按 'q' 退出实时识别")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 识别
            vis_frame, results = self.recognize_with_visualization(frame)

            # 显示结果信息
            for result in results:
                print(f"Hand {result.hand_id}: {result.gesture_zh} ({result.confidence:.2f})")

            # 写入视频
            if writer:
                writer.write(vis_frame)

            # 显示
            cv2.imshow("Gesture Recognition", vis_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
