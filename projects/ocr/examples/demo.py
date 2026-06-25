"""OCR 演示脚本"""

import sys
import os
import numpy as np
import cv2

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import OCREngine, SimpleTextDetector, TextRecognizer
from src.utils import create_test_image, draw_results


def demo_basic():
    """基础演示"""
    print("=" * 50)
    print("OCR 基础演示")
    print("=" * 50)

    # 创建 OCR 引擎
    engine = OCREngine()

    # 创建测试图像
    image = create_test_image("Hello World", (200, 600))

    # 处理图像
    results = engine.process(image)

    # 打印结果
    print(f"\n检测到 {len(results)} 个文字区域：")
    for i, result in enumerate(results):
        print(f"  {i+1}. 文本: '{result['text']}', 置信度: {result['confidence']:.4f}")

    # 可视化
    vis = engine.visualize(image, results)

    # 保存结果
    output_path = os.path.join(os.path.dirname(__file__), "output_basic.jpg")
    cv2.imwrite(output_path, vis)
    print(f"\n结果已保存到: {output_path}")


def demo_detection():
    """检测演示"""
    print("\n" + "=" * 50)
    print("文字检测演示")
    print("=" * 50)

    # 创建检测器
    detector = SimpleTextDetector()

    # 创建测试图像
    image = np.zeros((300, 800, 3), dtype=np.uint8)
    cv2.putText(image, "Line 1: Hello", (50, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
    cv2.putText(image, "Line 2: World", (50, 180),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
    cv2.putText(image, "Line 3: OCR", (50, 280),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)

    # 检测
    bboxes = detector.detect(image)

    print(f"\n检测到 {len(bboxes)} 个文字区域：")
    for i, bbox in enumerate(bboxes):
        x, y = bbox[0]
        print(f"  {i+1}. 位置: ({x}, {y})")

    # 可视化
    vis = image.copy()
    for bbox in bboxes:
        pts = bbox.astype(np.int32)
        cv2.polylines(vis, [pts], True, (0, 255, 0), 2)

    # 保存结果
    output_path = os.path.join(os.path.dirname(__file__), "output_detection.jpg")
    cv2.imwrite(output_path, vis)
    print(f"\n结果已保存到: {output_path}")


def demo_recognition():
    """识别演示"""
    print("\n" + "=" * 50)
    print("文字识别演示")
    print("=" * 50)

    # 创建识别器
    recognizer = TextRecognizer()

    # 创建测试图像
    image = np.zeros((32, 200), dtype=np.uint8)
    cv2.putText(image, "OCR", (20, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, 255, 2)

    # 识别
    text, confidence = recognizer.recognize(image)

    print(f"\n识别结果：")
    print(f"  文本: '{text}'")
    print(f"  置信度: {confidence:.4f}")


def demo_batch():
    """批量处理演示"""
    print("\n" + "=" * 50)
    print("批量处理演示")
    print("=" * 50)

    # 创建 OCR 引擎
    engine = OCREngine()

    # 创建多张测试图像
    images = [
        create_test_image("Hello", (200, 400)),
        create_test_image("World", (200, 400)),
        create_test_image("OCR", (200, 400)),
    ]

    # 批量处理
    all_results = engine.process_batch(images)

    print(f"\n处理了 {len(images)} 张图像：")
    for i, results in enumerate(all_results):
        print(f"  图像 {i+1}: 检测到 {len(results)} 个文字区域")


def demo_evaluator():
    """评估演示"""
    print("\n" + "=" * 50)
    print("评估演示")
    print("=" * 50)

    from src.evaluator import OCREvaluator

    # 创建评估器
    evaluator = OCREvaluator()

    # 添加模拟结果
    test_cases = [
        ("hello", "hello"),
        ("world", "world"),
        ("helo", "hello"),
        ("ocr", "ocr"),
        ("test", "tset"),
    ]

    for pred, gt in test_cases:
        evaluator.add_result(pred, gt)

    # 打印评估报告
    evaluator.print_summary()


def main():
    """主函数"""
    print("OCR 文字识别系统演示")
    print("=" * 50)

    # 运行各个演示
    demo_basic()
    demo_detection()
    demo_recognition()
    demo_batch()
    demo_evaluator()

    print("\n" + "=" * 50)
    print("演示完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()