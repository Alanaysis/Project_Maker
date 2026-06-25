"""
人脸对比示例

演示如何比较两张人脸是否为同一人。
"""

import sys
import os
import numpy as np

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import FeatureExtractor, FaceRecognizer, cosine_similarity, normalize_feature


def main():
    """主函数"""
    print("=== 人脸对比示例 ===\n")

    # 1. 创建特征提取器
    print("1. 创建特征提取器...")
    extractor = FeatureExtractor(model_type="custom", embedding_size=128)
    print(f"   嵌入维度: {extractor.get_embedding_size()}")

    # 2. 创建人脸识别器
    print("\n2. 创建人脸识别器...")
    recognizer = FaceRecognizer(threshold=0.6)
    print(f"   匹配阈值: {recognizer.threshold}")

    # 3. 模拟人脸特征
    print("\n3. 模拟人脸特征...")

    # 同一个人的不同特征（添加微小扰动）
    person1_feature1 = normalize_feature(np.random.randn(128))
    person1_feature2 = normalize_feature(person1_feature1 + np.random.randn(128) * 0.1)

    # 不同人的特征
    person2_feature = normalize_feature(np.random.randn(128))

    print("   生成了 3 个特征向量")

    # 4. 比较同一人的特征
    print("\n4. 比较同一人的特征...")
    is_same, similarity = recognizer.verify(person1_feature1, person1_feature2)
    print(f"   相似度: {similarity:.4f}")
    print(f"   是否匹配: {is_same}")

    # 5. 比较不同人的特征
    print("\n5. 比较不同人的特征...")
    is_same, similarity = recognizer.verify(person1_feature1, person2_feature)
    print(f"   相似度: {similarity:.4f}")
    print(f"   是否匹配: {is_same}")

    # 6. 添加人脸到数据库
    print("\n6. 添加人脸到数据库...")
    recognizer.add_face("张三", person1_feature1)
    recognizer.add_face("李四", person2_feature)
    print(f"   数据库中有 {recognizer.get_database_info()['num_people']} 人")

    # 7. 识别查询
    print("\n7. 识别查询...")

    # 使用张三的特征查询
    identity, confidence = recognizer.identify(person1_feature2)
    print(f"   查询张三的特征: 识别结果={identity}, 置信度={confidence:.4f}")

    # 使用李四的特征查询
    identity, confidence = recognizer.identify(person2_feature)
    print(f"   查询李四的特征: 识别结果={identity}, 置信度={confidence:.4f}")

    # 8. 查找相似人脸
    print("\n8. 查找相似人脸...")
    results = recognizer.find_similar(person1_feature2, top_k=2)
    for name, sim in results:
        print(f"   {name}: {sim:.4f}")

    # 9. 调整阈值
    print("\n9. 测试不同阈值...")
    for threshold in [0.3, 0.5, 0.7, 0.9]:
        recognizer.set_threshold(threshold)
        is_same, _ = recognizer.verify(person1_feature1, person1_feature2)
        print(f"   阈值={threshold}: 匹配={is_same}")

    print("\n=== 示例完成 ===")


def demo_with_images(image1_path: str, image2_path: str):
    """
    使用真实图像进行对比

    Args:
        image1_path: 图像 1 路径
        image2_path: 图像 2 路径
    """
    import cv2

    print(f"=== 图像对比 ===\n")
    print(f"图像 1: {image1_path}")
    print(f"图像 2: {image2_path}\n")

    # 加载图像
    img1 = cv2.imread(image1_path)
    img2 = cv2.imread(image2_path)

    if img1 is None or img2 is None:
        print("错误: 无法加载图像")
        return

    # 创建组件
    from src import FaceDetector
    detector = FaceDetector(method="haar")
    extractor = FeatureExtractor(model_type="custom", embedding_size=128)
    recognizer = FaceRecognizer(threshold=0.6)

    # 检测人脸
    faces1 = detector.detect(img1)
    faces2 = detector.detect(img2)

    print(f"图像 1 检测到 {len(faces1)} 张人脸")
    print(f"图像 2 检测到 {len(faces2)} 张人脸")

    if len(faces1) == 0 or len(faces2) == 0:
        print("错误: 未检测到人脸")
        return

    # 裁剪人脸
    cropped1 = detector.detect_and_crop(img1)[0]
    cropped2 = detector.detect_and_crop(img2)[0]

    # 提取特征
    feature1 = extractor.extract(cropped1)
    feature2 = extractor.extract(cropped2)

    # 比较
    is_same, similarity = recognizer.verify(feature1, feature2)

    print(f"\n比较结果:")
    print(f"  相似度: {similarity:.4f}")
    print(f"  是否同一人: {'是' if is_same else '否'}")


if __name__ == "__main__":
    main()

    # 如果提供了图像路径
    if len(sys.argv) >= 3:
        demo_with_images(sys.argv[1], sys.argv[2])
