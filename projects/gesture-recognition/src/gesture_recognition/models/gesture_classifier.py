"""
Gesture Classifier - 手势分类器

核心思路：
1. 从关键点坐标提取手势特征
2. 使用全连接网络进行分类
3. 支持多种手势类别

学习要点：
- 理解关键点特征工程
- 掌握分类网络设计
- 学会处理类别不平衡

支持的手势类别：
1. fist (拳头)
2. open_palm (张开手掌)
3. peace (剪刀手/V字)
4. thumbs_up (竖大拇指)
5. pointing (指向)
6. ok (OK手势)
7. none (无手势/其他)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import List, Dict, Optional, Tuple


# 手势类别定义
GESTURE_CLASSES = {
    0: "fist",
    1: "open_palm",
    2: "peace",
    3: "thumbs_up",
    4: "pointing",
    5: "ok",
    6: "none",
}

GESTURE_NAMES_ZH = {
    "fist": "拳头",
    "open_palm": "张开手掌",
    "peace": "剪刀手",
    "thumbs_up": "竖大拇指",
    "pointing": "指向",
    "ok": "OK手势",
    "none": "无手势",
}


class KeypointFeatureExtractor:
    """
    关键点特征提取器

    从21个手部关键点中提取有区分度的特征

    特征设计思路：
    1. 手指伸展状态：判断每根手指是否伸直
    2. 指尖距离：指尖之间的相对距离
    3. 手掌方向：手掌朝向
    4. 手指角度：手指之间的夹角

    为什么这样设计？
    - 手势的区别主要在于手指的弯曲/伸展状态
    - 指尖距离可以区分张开/握拳
    - 角度特征对旋转更鲁棒
    """

    @staticmethod
    def extract_features(keypoints: np.ndarray) -> np.ndarray:
        """
        从关键点提取特征向量

        Args:
            keypoints: (21, 2) 关键点坐标

        Returns:
            np.ndarray: 特征向量
        """
        features = []

        # 1. 手指伸展状态（5个特征）
        finger_states = KeypointFeatureExtractor._get_finger_states(keypoints)
        features.extend(finger_states)

        # 2. 指尖距离特征（10个特征）
        tip_distances = KeypointFeatureExtractor._get_tip_distances(keypoints)
        features.extend(tip_distances)

        # 3. 手指角度特征（4个特征）
        angles = KeypointFeatureExtractor._get_finger_angles(keypoints)
        features.extend(angles)

        # 4. 手掌中心到指尖的距离（5个特征）
        palm_distances = KeypointFeatureExtractor._get_palm_to_tip_distances(
            keypoints
        )
        features.extend(palm_distances)

        # 5. 关键点归一化坐标（42个特征）
        normalized = KeypointFeatureExtractor._normalize_keypoints(keypoints)
        features.extend(normalized.flatten().tolist())

        return np.array(features, dtype=np.float32)

    @staticmethod
    def _get_finger_states(keypoints: np.ndarray) -> List[float]:
        """
        判断每根手指是否伸展

        方法：比较指尖和对应关节的y坐标
        - 指尖y < 关节y → 手指伸展（手指向上）
        - 指尖y > 关节y → 手指弯曲

        关键点索引：
        - 拇指: tip=4, mcp=2
        - 食指: tip=8, mcp=6
        - 中指: tip=12, mcp=10
        - 无名指: tip=16, mcp=14
        - 小指: tip=20, mcp=18
        """
        states = []
        finger_tips = [4, 8, 12, 16, 20]
        finger_mcps = [2, 6, 10, 14, 18]

        for tip, mcp in zip(finger_tips, finger_mcps):
            # 伸展状态：指尖在关节上方
            extended = float(keypoints[tip, 1] < keypoints[mcp, 1])
            states.append(extended)

        return states

    @staticmethod
    def _get_tip_distances(keypoints: np.ndarray) -> List[float]:
        """
        计算指尖之间的相对距离

        选择5个指尖的两两组合中最具区分度的10对
        """
        tips = [4, 8, 12, 16, 20]
        distances = []

        # 归一化：使用手掌宽度作为基准
        palm_width = np.linalg.norm(keypoints[5] - keypoints[17])
        if palm_width < 1e-6:
            palm_width = 1.0

        for i in range(len(tips)):
            for j in range(i + 1, len(tips)):
                dist = np.linalg.norm(keypoints[tips[i]] - keypoints[tips[j]])
                distances.append(dist / palm_width)

        return distances

    @staticmethod
    def _get_finger_angles(keypoints: np.ndarray) -> List[float]:
        """
        计算手指之间的夹角

        使用向量夹角公式
        """
        # 手指方向向量（从根部到指尖）
        finger_vectors = {
            "thumb": keypoints[4] - keypoints[2],
            "index": keypoints[8] - keypoints[5],
            "middle": keypoints[12] - keypoints[9],
            "ring": keypoints[16] - keypoints[13],
        }

        angles = []
        pairs = [("thumb", "index"), ("index", "middle"), ("middle", "ring")]

        for v1_name, v2_name in pairs:
            v1 = finger_vectors[v1_name]
            v2 = finger_vectors[v2_name]

            # 计算夹角
            cos_angle = np.dot(v1, v2) / (
                np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6
            )
            angle = np.arccos(np.clip(cos_angle, -1, 1))
            angles.append(angle)

        # 拇指和小指的夹角
        pinky_vec = keypoints[20] - keypoints[17]
        thumb_vec = finger_vectors["thumb"]
        cos_angle = np.dot(thumb_vec, pinky_vec) / (
            np.linalg.norm(thumb_vec) * np.linalg.norm(pinky_vec) + 1e-6
        )
        angles.append(np.arccos(np.clip(cos_angle, -1, 1)))

        return angles

    @staticmethod
    def _get_palm_to_tip_distances(keypoints: np.ndarray) -> List[float]:
        """
        计算手掌中心到各指尖的距离

        手掌中心定义为手腕和中指根部的中点
        """
        palm_center = (keypoints[0] + keypoints[9]) / 2
        tips = [4, 8, 12, 16, 20]

        # 归一化
        palm_width = np.linalg.norm(keypoints[5] - keypoints[17])
        if palm_width < 1e-6:
            palm_width = 1.0

        distances = []
        for tip in tips:
            dist = np.linalg.norm(keypoints[tip] - palm_center)
            distances.append(dist / palm_width)

        return distances

    @staticmethod
    def _normalize_keypoints(keypoints: np.ndarray) -> np.ndarray:
        """
        归一化关键点坐标

        以手腕为原点，手掌宽度为单位
        """
        # 以手腕为原点
        normalized = keypoints - keypoints[0]

        # 以手掌宽度为单位缩放
        palm_width = np.linalg.norm(keypoints[5] - keypoints[17])
        if palm_width < 1e-6:
            palm_width = 1.0

        normalized = normalized / palm_width

        return normalized


class GestureClassifierNet(nn.Module):
    """
    手势分类网络

    架构：
    - 输入: 关键点特征向量
    - 隐藏层: 全连接 + BatchNorm + Dropout
    - 输出: 手势类别概率

    为什么用全连接而不是RNN？
    - 关键点特征已经是空间关系的抽象
    - 不需要建模时序关系
    - 全连接网络足够且更快
    """

    def __init__(self, input_dim: int = 66, num_classes: int = 7):
        """
        Args:
            input_dim: 输入特征维度
            num_classes: 手势类别数
        """
        super().__init__()

        self.network = nn.Sequential(
            # 第1层
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),

            # 第2层
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),

            # 第3层
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(inplace=True),

            # 输出层
            nn.Linear(32, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: 特征向量 (B, input_dim)

        Returns:
            logits: (B, num_classes)
        """
        return self.network(x)


class GestureClassifier:
    """
    手势分类器

    封装了特征提取和分类推理
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "cpu",
    ):
        """
        初始化手势分类器

        Args:
            model_path: 预训练模型路径
            device: 推理设备
        """
        self.device = torch.device(device)
        self.feature_extractor = KeypointFeatureExtractor()
        self.model = GestureClassifierNet().to(self.device)

        if model_path is not None:
            self.model.load_state_dict(
                torch.load(model_path, map_location=self.device)
            )

        self.model.eval()
        self.classes = GESTURE_CLASSES

    def classify(self, keypoints: np.ndarray) -> dict:
        """
        对关键点进行手势分类

        Args:
            keypoints: (21, 2) 关键点坐标

        Returns:
            dict: 分类结果
                - gesture: 手势名称
                - gesture_zh: 手势中文名
                - confidence: 置信度
                - probabilities: 各类别概率
        """
        # 提取特征
        features = self.feature_extractor.extract_features(keypoints)

        # 转换为tensor
        input_tensor = (
            torch.from_numpy(features).unsqueeze(0).to(self.device)
        )

        # 推理
        with torch.no_grad():
            logits = self.model(input_tensor)
            probs = F.softmax(logits, dim=1)

        # 获取结果
        probs_np = probs.cpu().numpy()[0]
        pred_idx = np.argmax(probs_np)
        gesture_name = self.classes[pred_idx]

        return {
            "gesture": gesture_name,
            "gesture_zh": GESTURE_NAMES_ZH.get(gesture_name, gesture_name),
            "confidence": float(probs_np[pred_idx]),
            "probabilities": {
                self.classes[i]: float(p) for i, p in enumerate(probs_np)
            },
        }

    def classify_rule_based(self, keypoints: np.ndarray) -> dict:
        """
        基于规则的手势分类（无需训练）

        适用于学习和演示目的

        Args:
            keypoints: (21, 2) 关键点坐标

        Returns:
            dict: 分类结果
        """
        # 获取手指伸展状态
        finger_states = KeypointFeatureExtractor._get_finger_states(keypoints)
        thumb, index, middle, ring, pinky = finger_states

        # 规则分类
        gesture = "none"

        # 拳头：所有手指都弯曲
        if not any(finger_states):
            gesture = "fist"

        # 张开手掌：所有手指都伸展
        elif all(finger_states):
            gesture = "open_palm"

        # 剪刀手：食指和中指伸展
        elif index and middle and not ring and not pinky:
            gesture = "peace"

        # 竖大拇指：只有拇指伸展
        elif thumb and not index and not middle and not ring and not pinky:
            gesture = "thumbs_up"

        # 指向：只有食指伸展
        elif not thumb and index and not middle and not ring and not pinky:
            gesture = "pointing"

        # OK手势：拇指和食指接近（需要额外判断）
        elif thumb and index:
            # 检查拇指尖和食指尖是否接近
            tip_dist = np.linalg.norm(keypoints[4] - keypoints[8])
            palm_width = np.linalg.norm(keypoints[5] - keypoints[17])
            if palm_width > 0 and tip_dist / palm_width < 0.3:
                gesture = "ok"

        return {
            "gesture": gesture,
            "gesture_zh": GESTURE_NAMES_ZH.get(gesture, gesture),
            "confidence": 0.9,  # 规则方法给固定置信度
            "method": "rule_based",
        }

    def batch_classify(self, keypoints_list: List[np.ndarray]) -> List[dict]:
        """
        批量分类

        Args:
            keypoints_list: 关键点列表

        Returns:
            List[dict]: 分类结果列表
        """
        return [self.classify(kp) for kp in keypoints_list]
