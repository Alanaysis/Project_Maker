"""
Hand Detector - 检测图像中的手部区域

核心思路：
1. 使用肤色分割 + 轮廓检测的轻量级方法
2. 输出手部边界框 (bounding box)
3. 支持单手和双手检测

学习要点：
- 理解图像预处理流程
- 掌握颜色空间转换 (BGR -> HSV)
- 学会使用形态学操作清理分割结果
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional


class HandDetector:
    """
    手部检测器 - 基于肤色分割的手部区域检测

    为什么选择肤色分割？
    1. 计算量小，适合实时应用
    2. 不需要大规模训练数据
    3. 适合学习图像处理基础

    权衡：
    - 优点：速度快，实现简单
    - 缺点：对光照敏感，可能误检类似肤色的区域
    """

    def __init__(
        self,
        min_hand_area: int = 3000,
        max_hands: int = 2,
        skin_lower: Tuple[int, int, int] = (0, 20, 70),
        skin_upper: Tuple[int, int, int] = (20, 255, 255),
    ):
        """
        初始化手部检测器

        Args:
            min_hand_area: 最小手部面积阈值，过滤噪声
            max_hands: 最大检测手数
            skin_lower: HSV肤色下界
            skin_upper: HSV肤色上界
        """
        self.min_hand_area = min_hand_area
        self.max_hands = max_hands
        self.skin_lower = np.array(skin_lower, dtype=np.uint8)
        self.skin_upper = np.array(skin_upper, dtype=np.uint8)

        # 形态学操作核
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    def detect(self, image: np.ndarray) -> List[dict]:
        """
        检测图像中的手部

        Args:
            image: BGR格式的输入图像

        Returns:
            List[dict]: 检测结果列表，每个包含:
                - bbox: (x, y, w, h) 边界框
                - center: (cx, cy) 中心点
                - area: 手部面积
                - mask: 手部掩码
        """
        # 预处理
        processed = self._preprocess(image)

        # 肤色分割
        skin_mask = self._detect_skin(processed)

        # 形态学操作清理
        cleaned_mask = self._clean_mask(skin_mask)

        # 轮廓检测
        hands = self._find_hands(cleaned_mask)

        # 按面积排序，取前max_hands个
        hands.sort(key=lambda h: h["area"], reverse=True)
        return hands[: self.max_hands]

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理

        关键步骤：
        1. 高斯模糊去噪
        2. 转换到HSV颜色空间

        为什么用HSV？
        - HSV对光照变化更鲁棒
        - 色相(H)通道独立于亮度，便于肤色分割
        """
        # 高斯模糊去噪
        blurred = cv2.GaussianBlur(image, (5, 5), 0)

        # BGR转HSV
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        return hsv

    def _detect_skin(self, hsv_image: np.ndarray) -> np.ndarray:
        """
        肤色分割

        使用HSV颜色空间的阈值分割：
        - H (色相): 0-20 度，覆盖常见肤色范围
        - S (饱和度): 20-255，排除灰白色
        - V (明度): 70-255，排除暗区域
        """
        # 阈值分割
        mask = cv2.inRange(hsv_image, self.skin_lower, self.skin_upper)

        return mask

    def _clean_mask(self, mask: np.ndarray) -> np.ndarray:
        """
        形态学操作清理掩码

        操作顺序：
        1. 开运算：去除小噪声点
        2. 闭运算：填充手部内部空洞
        3. 膨胀：连接断裂区域

        为什么这样组合？
        - 开运算 = 腐蚀 + 膨胀，去除小物体
        - 闭运算 = 膨胀 + 腐蚀，填充小孔
        """
        # 开运算去噪
        cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel, iterations=2)

        # 闭运算填充
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, self.kernel, iterations=2)

        # 膨胀连接
        cleaned = cv2.dilate(cleaned, self.kernel, iterations=1)

        return cleaned

    def _find_hands(self, mask: np.ndarray) -> List[dict]:
        """
        从掩码中提取手部区域

        步骤：
        1. 查找轮廓
        2. 过滤小面积轮廓
        3. 计算边界框和中心点
        """
        # 查找轮廓
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        hands = []
        for contour in contours:
            area = cv2.contourArea(contour)

            # 过滤小面积
            if area < self.min_hand_area:
                continue

            # 计算边界框
            x, y, w, h = cv2.boundingRect(contour)

            # 计算中心点
            cx = x + w // 2
            cy = y + h // 2

            # 创建手部掩码
            hand_mask = np.zeros_like(mask)
            cv2.drawContours(hand_mask, [contour], -1, 255, -1)

            hands.append(
                {
                    "bbox": (x, y, w, h),
                    "center": (cx, cy),
                    "area": area,
                    "mask": hand_mask,
                    "contour": contour,
                }
            )

        return hands

    def detect_from_video(
        self, video_path: str, frame_interval: int = 1
    ) -> List[List[dict]]:
        """
        从视频中检测手部

        Args:
            video_path: 视频路径
            frame_interval: 帧间隔

        Returns:
            List[List[dict]]: 每帧的检测结果
        """
        cap = cv2.VideoCapture(video_path)
        results = []
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                hands = self.detect(frame)
                results.append(hands)

            frame_count += 1

        cap.release()
        return results
