"""
基础手势识别示例

演示如何使用手势识别系统：
1. 创建合成手部图像
2. 检测手部
3. 提取关键点
4. 分类手势

使用方法：
    python examples/basic_recognition.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import cv2
import numpy as np
from gesture_recognition import GestureRecognizer
from gesture_recognition.models.gesture_classifier import (
    GESTURE_CLASSES,
    GESTURE_NAMES_ZH,
    KeypointFeatureExtractor,
)
from gesture_recognition.utils.visualization import draw_hand_landmarks


def create_synthetic_hand_image(gesture_type: int = 1) -> np.ndarray:
    """
    创建合成手部图像

    Args:
        gesture_type: 手势类型 (0-6)

    Returns:
        np.ndarray: BGR格式的合成图像
    """
    # 创建空白图像
    image = np.ones((480, 640, 3), dtype=np.uint8) * 200

    # 根据手势类型生成不同的手部区域
    if gesture_type == 0:  # fist
        # 绘制拳头形状的椭圆
        cv2.ellipse(image, (320, 240), (80, 100), 0, 0, 360, (150, 120, 100), -1)
        cv2.ellipse(image, (320, 240), (80, 100), 0, 0, 360, (100, 80, 60), 2)

    elif gesture_type == 1:  # open_palm
        # 绘制张开手掌
        # 手掌
        cv2.ellipse(image, (320, 280), (70, 90), 0, 0, 360, (150, 120, 100), -1)
        # 手指
        for i, dx in enumerate([-60, -30, 0, 30, 60]):
            length = 120 if i != 0 else 80
            angle = -10 + i * 5
            x = 320 + dx
            y = 200 - length
            cv2.ellipse(
                image, (x, 200), (15, length), angle, 0, 360, (150, 120, 100), -1
            )

    elif gesture_type == 2:  # peace
        # 绘制剪刀手
        cv2.ellipse(image, (320, 280), (70, 90), 0, 0, 360, (150, 120, 100), -1)
        # 食指和中指
        cv2.ellipse(image, (305, 200), (15, 80), -5, 0, 360, (150, 120, 100), -1)
        cv2.ellipse(image, (335, 200), (15, 80), 5, 0, 360, (150, 120, 100), -1)

    elif gesture_type == 3:  # thumbs_up
        # 绘制竖大拇指
        cv2.ellipse(image, (320, 280), (70, 90), 0, 0, 360, (150, 120, 100), -1)
        # 大拇指
        cv2.ellipse(image, (280, 180), (15, 80), 0, 0, 360, (150, 120, 100), -1)

    elif gesture_type == 4:  # pointing
        # 绘制指向手势
        cv2.ellipse(image, (320, 280), (70, 90), 0, 0, 360, (150, 120, 100), -1)
        # 食指
        cv2.ellipse(image, (305, 200), (15, 80), -5, 0, 360, (150, 120, 100), -1)

    elif gesture_type == 5:  # ok
        # 绘制OK手势
        cv2.ellipse(image, (320, 280), (70, 90), 0, 0, 360, (150, 120, 100), -1)
        # 拇指和食指形成圆
        cv2.circle(image, (290, 220), 25, (150, 120, 100), -1)
        cv2.circle(image, (290, 220), 10, (200, 180, 160), -1)

    else:  # none
        cv2.putText(
            image, "No Hand", (250, 250),
            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (100, 100, 100), 3
        )

    # 添加噪声使图像更真实
    noise = np.random.normal(0, 10, image.shape).astype(np.uint8)
    image = cv2.add(image, noise)

    return image


def demo_rule_based_recognition():
    """
    演示基于规则的手势识别

    这种方法不需要训练，直接使用规则判断
    """
    print("=" * 50)
    print("Demo: Rule-based Gesture Recognition")
    print("=" * 50)

    recognizer = GestureRecognizer(use_neural_classifier=False)

    for gesture_id, gesture_name in GESTURE_CLASSES.items():
        # 创建合成图像
        image = create_synthetic_hand_image(gesture_id)

        # 识别
        results = recognizer.recognize(image)

        print(f"\nGesture: {gesture_name} ({GESTURE_NAMES_ZH.get(gesture_name, '')})")
        if results:
            for result in results:
                print(f"  Detected: {result.gesture_zh} (confidence: {result.confidence:.2f})")
        else:
            print("  No hand detected")


def demo_keypoint_extraction():
    """
    演示关键点提取

    展示如何从关键点中提取特征
    """
    print("\n" + "=" * 50)
    print("Demo: Keypoint Feature Extraction")
    print("=" * 50)

    from gesture_recognition.data.hand_dataset import HandDataset

    # 创建数据集获取关键点
    dataset = HandDataset(num_samples=10, num_classes=7)

    # 获取不同手势的关键点
    for gesture_id in range(7):
        # 获取该手势的样本
        sample = dataset.data[gesture_id]
        keypoints = np.array(sample["keypoints"])

        # 提取特征
        features = KeypointFeatureExtractor.extract_features(keypoints)

        # 获取手指状态
        finger_states = KeypointFeatureExtractor._get_finger_states(keypoints)

        gesture_name = GESTURE_CLASSES[gesture_id]
        print(f"\n{gesture_name}:")
        print(f"  Finger states (thumb-index-middle-ring-pinky): {finger_states}")
        print(f"  Feature vector length: {len(features)}")


def demo_visualization():
    """
    演示可视化功能

    展示如何绘制手部关键点
    """
    print("\n" + "=" * 50)
    print("Demo: Visualization")
    print("=" * 50)

    from gesture_recognition.data.hand_dataset import HandDataset

    # 创建数据集
    dataset = HandDataset(num_samples=7, num_classes=7)

    # 为每种手势创建可视化
    for gesture_id in range(7):
        sample = dataset.data[gesture_id]
        keypoints = np.array(sample["keypoints"])

        # 创建空白图像
        image = np.ones((400, 400, 3), dtype=np.uint8) * 255

        # 缩放关键点到图像尺寸
        pixel_keypoints = keypoints.copy()
        pixel_keypoints[:, 0] *= 400
        pixel_keypoints[:, 1] *= 400

        # 绘制关键点
        vis = draw_hand_landmarks(image, pixel_keypoints, color_by_finger=True)

        # 添加标签
        gesture_name = GESTURE_CLASSES[gesture_id]
        cv2.putText(
            vis, gesture_name, (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2
        )

        # 保存图像
        save_path = f"examples/output_{gesture_name}.png"
        cv2.imwrite(save_path, vis)
        print(f"Saved: {save_path}")


def main():
    """主函数"""
    print("Gesture Recognition Demo")
    print("=" * 50)

    # 演示1: 基于规则的识别
    demo_rule_based_recognition()

    # 演示2: 关键点特征提取
    demo_keypoint_extraction()

    # 演示3: 可视化
    demo_visualization()

    print("\n" + "=" * 50)
    print("Demo completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
