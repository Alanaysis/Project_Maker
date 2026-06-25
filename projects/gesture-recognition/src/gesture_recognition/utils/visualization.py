"""
Visualization - 可视化工具

功能：
1. 绘制手部关键点和骨架
2. 绘制识别结果
3. 创建手势对比图
4. 绘制训练曲线

学习要点：
- 理解OpenCV绘图API
- 掌握matplotlib可视化技巧
- 学会创建信息丰富的可视化
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Optional, Tuple


# 手部关键点连接定义
HAND_CONNECTIONS = [
    # 拇指
    (0, 1), (1, 2), (2, 3), (3, 4),
    # 食指
    (0, 5), (5, 6), (6, 7), (7, 8),
    # 中指
    (0, 9), (9, 10), (10, 11), (11, 12),
    # 无名指
    (0, 13), (13, 14), (14, 15), (15, 16),
    # 小指
    (0, 17), (17, 18), (18, 19), (19, 20),
]

# 手指颜色
FINGER_COLORS = {
    "thumb": (255, 0, 0),     # 红色
    "index": (0, 255, 0),     # 绿色
    "middle": (0, 0, 255),    # 蓝色
    "ring": (255, 255, 0),    # 青色
    "pinky": (255, 0, 255),   # 粉色
}

# 关键点索引到手指的映射
KEYPOINT_TO_FINGER = {
    0: "wrist",
    1: "thumb", 2: "thumb", 3: "thumb", 4: "thumb",
    5: "index", 6: "index", 7: "index", 8: "index",
    9: "middle", 10: "middle", 11: "middle", 12: "middle",
    13: "ring", 14: "ring", 15: "ring", 16: "ring",
    17: "pinky", 18: "pinky", 19: "pinky", 20: "pinky",
}

# 默认关键点颜色（非手指特定）
DEFAULT_COLOR = (200, 200, 200)


def draw_hand_landmarks(
    image: np.ndarray,
    keypoints: np.ndarray,
    connections: Optional[List[Tuple[int, int]]] = None,
    point_radius: int = 4,
    line_thickness: int = 2,
    color_by_finger: bool = True,
) -> np.ndarray:
    """
    在图像上绘制手部关键点和骨架

    Args:
        image: BGR格式的输入图像
        keypoints: (21, 2) 关键点坐标，可以是像素坐标或归一化坐标
        connections: 关键点连接关系
        point_radius: 关键点半径
        line_thickness: 连线粗细
        color_by_finger: 是否按手指着色

    Returns:
        np.ndarray: 绘制后的图像
    """
    vis = image.copy()
    h, w = image.shape[:2]

    if connections is None:
        connections = HAND_CONNECTIONS

    # 检查是否需要归一化坐标转换
    if keypoints.max() <= 1.0:
        # 归一化坐标，需要转换为像素坐标
        pixel_keypoints = keypoints.copy()
        pixel_keypoints[:, 0] *= w
        pixel_keypoints[:, 1] *= h
    else:
        pixel_keypoints = keypoints

    # 绘制连线
    for start_idx, end_idx in connections:
        start = tuple(pixel_keypoints[start_idx].astype(int))
        end = tuple(pixel_keypoints[end_idx].astype(int))

        # 获取颜色
        if color_by_finger:
            finger = KEYPOINT_TO_FINGER.get(start_idx, "wrist")
            color = FINGER_COLORS.get(finger, DEFAULT_COLOR)
        else:
            color = (0, 255, 0)

        cv2.line(vis, start, end, color, line_thickness)

    # 绘制关键点
    for i, kp in enumerate(pixel_keypoints):
        center = tuple(kp.astype(int))

        # 关键点颜色
        if color_by_finger:
            finger = KEYPOINT_TO_FINGER.get(i, "wrist")
            color = FINGER_COLORS.get(finger, DEFAULT_COLOR)
        else:
            color = (0, 255, 0)

        # 特殊标记：手腕用更大的圆
        radius = point_radius * 2 if i == 0 else point_radius

        cv2.circle(vis, center, radius, color, -1)
        cv2.circle(vis, center, radius, (255, 255, 255), 1)  # 白色边框

    return vis


def draw_gesture_result(
    image: np.ndarray,
    result: dict,
    position: str = "top_left",
) -> np.ndarray:
    """
    绘制手势识别结果

    Args:
        image: BGR格式的输入图像
        result: 识别结果字典
        position: 显示位置 ('top_left', 'top_right', 'bottom_left', 'bottom_right')

    Returns:
        np.ndarray: 绘制后的图像
    """
    vis = image.copy()
    h, w = image.shape[:2]

    # 准备文本
    gesture = result.get("gesture_zh", result.get("gesture", "Unknown"))
    confidence = result.get("confidence", 0)
    text = f"{gesture}: {confidence:.2f}"

    # 计算位置
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    thickness = 2
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)

    margin = 20
    if position == "top_left":
        org = (margin, margin + text_h)
    elif position == "top_right":
        org = (w - text_w - margin, margin + text_h)
    elif position == "bottom_left":
        org = (margin, h - margin)
    else:
        org = (w - text_w - margin, h - margin)

    # 绘制背景矩形
    bg_tl = (org[0] - 5, org[1] - text_h - 5)
    bg_br = (org[0] + text_w + 5, org[1] + 5)
    cv2.rectangle(vis, bg_tl, bg_br, (0, 0, 0), -1)

    # 绘制文本
    cv2.putText(vis, text, org, font, font_scale, (0, 255, 0), thickness)

    return vis


def draw_multiple_hands(
    image: np.ndarray,
    results: List[dict],
    draw_bbox: bool = True,
    draw_keypoints: bool = True,
    draw_label: bool = True,
) -> np.ndarray:
    """
    绘制多只手的识别结果

    Args:
        image: BGR格式的输入图像
        results: 识别结果列表
        draw_bbox: 是否绘制边界框
        draw_keypoints: 是否绘制关键点
        draw_label: 是否绘制标签

    Returns:
        np.ndarray: 绘制后的图像
    """
    vis = image.copy()

    # 不同手的颜色
    hand_colors = [
        (0, 255, 0),    # 绿色
        (255, 0, 0),    # 蓝色
        (0, 0, 255),    # 红色
        (255, 255, 0),  # 青色
    ]

    for i, result in enumerate(results):
        color = hand_colors[i % len(hand_colors)]

        # 绘制边界框
        if draw_bbox and "bbox" in result:
            x, y, w, h = result["bbox"]
            cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)

        # 绘制关键点
        if draw_keypoints and "keypoints_pixel" in result:
            vis = draw_hand_landmarks(
                vis,
                result["keypoints_pixel"],
                color_by_finger=False,
            )

        # 绘制标签
        if draw_label:
            gesture = result.get("gesture_zh", result.get("gesture", ""))
            confidence = result.get("confidence", 0)
            label = f"{gesture} ({confidence:.2f})"

            # 标签位置
            if "bbox" in result:
                x, y, _, _ = result["bbox"]
                label_pos = (x, y - 10)
            else:
                label_pos = (10, 30 * (i + 1))

            cv2.putText(
                vis, label, label_pos,
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
            )

    return vis


def create_gesture_gallery(
    gestures: List[str],
    images: List[np.ndarray],
    cols: int = 4,
) -> np.ndarray:
    """
    创建手势展示图

    Args:
        gestures: 手势名称列表
        images: 对应图像列表
        cols: 每行显示数量

    Returns:
        np.ndarray: 拼接后的图像
    """
    n = len(images)
    rows = (n + cols - 1) // cols

    # 获取单个图像尺寸
    h, w = images[0].shape[:2]

    # 创建画布
    gallery = np.zeros((rows * (h + 30), cols * w, 3), dtype=np.uint8)

    for i, (gesture, img) in enumerate(zip(gestures, images)):
        row = i // cols
        col = i % cols

        y_start = row * (h + 30)
        x_start = col * w

        # 放置图像
        gallery[y_start:y_start + h, x_start:x_start + w] = img

        # 放置标签
        label_y = y_start + h + 20
        label_x = x_start + w // 2 - 30
        cv2.putText(
            gallery, gesture, (label_x, label_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1
        )

    return gallery


def plot_training_curves(
    train_losses: List[float],
    val_losses: List[float],
    train_accs: List[float],
    val_accs: List[float],
    save_path: Optional[str] = None,
):
    """
    绘制训练曲线

    Args:
        train_losses: 训练损失列表
        val_losses: 验证损失列表
        train_accs: 训练准确率列表
        val_accs: 验证准确率列表
        save_path: 保存路径
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    # 损失曲线
    ax1.plot(train_losses, label="Train Loss")
    ax1.plot(val_losses, label="Val Loss")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.set_title("Training and Validation Loss")
    ax1.legend()
    ax1.grid(True)

    # 准确率曲线
    ax2.plot(train_accs, label="Train Accuracy")
    ax2.plot(val_accs, label="Val Accuracy")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy")
    ax2.set_title("Training and Validation Accuracy")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")

    plt.show()


def visualize_keypoints_2d(
    keypoints: np.ndarray,
    title: str = "Hand Keypoints",
    save_path: Optional[str] = None,
):
    """
    使用matplotlib可视化2D关键点

    Args:
        keypoints: (21, 2) 关键点坐标
        title: 图表标题
        save_path: 保存路径
    """
    fig, ax = plt.subplots(1, 1, figsize=(6, 8))

    # 绘制连线
    for start_idx, end_idx in HAND_CONNECTIONS:
        start = keypoints[start_idx]
        end = keypoints[end_idx]
        ax.plot([start[0], end[0]], [start[1], end[1]], "b-", linewidth=2)

    # 绘制关键点
    ax.scatter(keypoints[:, 0], keypoints[:, 1], c="red", s=50, zorder=5)

    # 标注关键点索引
    for i, (x, y) in enumerate(keypoints):
        ax.annotate(str(i), (x, y), textcoords="offset points", xytext=(5, 5))

    ax.set_title(title)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.invert_yaxis()  # 图像坐标系y轴向下
    ax.set_aspect("equal")
    ax.grid(True)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")

    plt.show()
