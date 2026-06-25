"""
人脸数据库示例

演示如何管理人脸数据库。
"""

import sys
import os
import numpy as np

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import FaceRecognizer, normalize_feature


def main():
    """主函数"""
    print("=== 人脸数据库示例 ===\n")

    # 1. 创建识别器
    print("1. 创建人脸识别器...")
    recognizer = FaceRecognizer(threshold=0.6)

    # 2. 创建模拟数据
    print("\n2. 创建模拟人脸数据...")
    people = {
        "张三": [normalize_feature(np.random.randn(128)) for _ in range(3)],
        "李四": [normalize_feature(np.random.randn(128)) for _ in range(2)],
        "王五": [normalize_feature(np.random.randn(128)) for _ in range(4)],
    }

    # 3. 添加到数据库
    print("\n3. 添加人脸到数据库...")
    for name, features in people.items():
        for feature in features:
            recognizer.add_face(name, feature)
        print(f"   添加 {name}: {len(features)} 个样本")

    # 4. 显示数据库信息
    print("\n4. 数据库信息...")
    info = recognizer.get_database_info()
    print(f"   人数: {info['num_people']}")
    print(f"   总样本数: {info['num_samples']}")
    print(f"   人名列表: {info['names']}")
    print(f"   匹配阈值: {info['threshold']}")
    print(f"   距离度量: {info['distance_metric']}")

    # 5. 测试识别
    print("\n5. 测试识别功能...")
    for name, features in people.items():
        # 使用同一人的一个特征查询
        query = features[0]
        identity, confidence = recognizer.identify(query)
        print(f"   查询 {name}: 识别结果={identity}, 置信度={confidence:.4f}")

    # 6. 查找相似人脸
    print("\n6. 查找相似人脸...")
    query = people["张三"][0]
    results = recognizer.find_similar(query, top_k=3)
    print("   与张三最相似的人:")
    for name, sim in results:
        print(f"     {name}: {sim:.4f}")

    # 7. 保存数据库
    print("\n7. 保存数据库...")
    save_path = "face_database"
    recognizer.save_database(save_path)
    print(f"   保存到: {save_path}")

    # 8. 加载数据库
    print("\n8. 加载数据库...")
    new_recognizer = FaceRecognizer()
    new_recognizer.load_database(save_path)
    new_info = new_recognizer.get_database_info()
    print(f"   加载后人数: {new_info['num_people']}")
    print(f"   加载后样本数: {new_info['num_samples']}")

    # 9. 测试加载后的识别
    print("\n9. 测试加载后的识别...")
    query = people["李四"][0]
    identity, confidence = new_recognizer.identify(query)
    print(f"   查询李四: 识别结果={identity}, 置信度={confidence:.4f}")

    # 10. 移除人脸
    print("\n10. 移除人脸...")
    recognizer.remove_face("王五")
    info = recognizer.get_database_info()
    print(f"    移除王五后人数: {info['num_people']}")
    print(f"    人名列表: {info['names']}")

    # 11. 批量操作
    print("\n11. 批量操作示例...")
    batch_features = [normalize_feature(np.random.randn(128)) for _ in range(5)]
    for i, feature in enumerate(batch_features):
        recognizer.add_face(f"新人_{i+1}", feature)
    info = recognizer.get_database_info()
    print(f"    添加后人数: {info['num_people']}")

    print("\n=== 示例完成 ===")


def demo_advanced_features():
    """高级功能演示"""
    print("=== 高级功能演示 ===\n")

    recognizer = FaceRecognizer(threshold=0.5)

    # 1. 添加多角度特征
    print("1. 添加多角度特征...")
    base_feature = normalize_feature(np.random.randn(128))

    # 模拟不同角度的特征
    angles = ["front", "left", "right", "up", "down"]
    for angle in angles:
        # 添加微小变化模拟不同角度
        feature = normalize_feature(base_feature + np.random.randn(128) * 0.1)
        recognizer.add_face("张三", feature, metadata={"angle": angle})

    print(f"   添加了 {len(angles)} 个角度的特征")

    # 2. 测试不同角度的识别
    print("\n2. 测试不同角度的识别...")
    for angle in ["front", "left", "right"]:
        # 模拟该角度的查询
        query = normalize_feature(base_feature + np.random.randn(128) * 0.15)
        identity, confidence = recognizer.identify(query)
        print(f"   {angle} 角度: 识别结果={identity}, 置信度={confidence:.4f}")

    # 3. 测试阈值敏感性
    print("\n3. 测试阈值敏感性...")
    query = normalize_feature(base_feature + np.random.randn(128) * 0.2)
    for threshold in [0.3, 0.5, 0.7, 0.9]:
        recognizer.set_threshold(threshold)
        identity, confidence = recognizer.identify(query)
        print(f"   阈值={threshold}: 识别结果={identity}, 置信度={confidence:.4f}")

    print("\n=== 高级功能演示完成 ===")


if __name__ == "__main__":
    main()
    demo_advanced_features()
