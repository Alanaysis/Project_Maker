"""
基础人脸检测示例

演示如何使用 FaceDetector 进行人脸检测。
"""

import sys
import os
import cv2
import numpy as np

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import FaceDetector, draw_faces, create_test_image


def main():
    """主函数"""
    print("=== 基础人脸检测示例 ===\n")

    # 1. 创建检测器
    print("1. 创建 Haar 检测器...")
    detector = FaceDetector(method="haar")
    print(f"   检测方法: {detector.method_name}")

    # 2. 创建测试图像
    print("\n2. 创建测试图像...")
    image = create_test_image(width=400, height=400, with_face=True)
    print(f"   图像尺寸: {image.shape}")

    # 3. 检测人脸
    print("\n3. 检测人脸...")
    faces = detector.detect(image)
    print(f"   检测到 {len(faces)} 张人脸")

    for i, face in enumerate(faces):
        print(f"   人脸 {i+1}: 位置=({face.x}, {face.y}), "
              f"大小=({face.width}x{face.height}), "
              f"置信度={face.confidence:.2f}")

    # 4. 检测并裁剪
    print("\n4. 检测并裁剪人脸...")
    cropped_faces = detector.detect_and_crop(image, target_size=(160, 160))
    print(f"   裁剪了 {len(cropped_faces)} 张人脸")

    for i, face in enumerate(cropped_faces):
        print(f"   人脸 {i+1}: 尺寸={face.shape}")

    # 5. 可视化结果
    print("\n5. 绘制检测结果...")
    result = draw_faces(image, faces)
    print("   绘制完成")

    # 6. 测试 MTCNN 检测器
    print("\n6. 测试 MTCNN 检测器...")
    try:
        mtcnn_detector = FaceDetector(method="mtcnn")
        faces_mtcnn = mtcnn_detector.detect(image)
        print(f"   MTCNN 检测到 {len(faces_mtcnn)} 张人脸")

        for i, face in enumerate(faces_mtcnn):
            print(f"   人脸 {i+1}: 关键点={list(face.landmarks.keys())}")
    except Exception as e:
        print(f"   MTCNN 检测失败: {e}")

    print("\n=== 示例完成 ===")


def demo_with_real_image(image_path: str):
    """
    使用真实图像进行检测

    Args:
        image_path: 图像路径
    """
    print(f"=== 使用真实图像检测: {image_path} ===\n")

    # 加载图像
    if not os.path.exists(image_path):
        print(f"错误: 图像文件不存在: {image_path}")
        return

    image = cv2.imread(image_path)
    if image is None:
        print(f"错误: 无法加载图像: {image_path}")
        return

    print(f"图像尺寸: {image.shape}")

    # 创建检测器
    detector = FaceDetector(method="haar")

    # 检测人脸
    faces = detector.detect(image)
    print(f"检测到 {len(faces)} 张人脸")

    # 绘制结果
    result = draw_faces(image, faces)

    # 保存结果
    output_path = "detection_result.jpg"
    cv2.imwrite(output_path, result)
    print(f"结果已保存到: {output_path}")


if __name__ == "__main__":
    main()

    # 如果提供了图像路径，使用真实图像
    if len(sys.argv) > 1:
        demo_with_real_image(sys.argv[1])
