"""
特征匹配演示脚本

展示如何使用SIFT/ORB进行特征点检测和匹配。
"""

import cv2
import numpy as np
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.detector import FeatureDetector
from src.descriptor import DescriptorExtractor
from src.matcher import FeatureMatcher
from src.visualizer import Visualizer


def create_sample_images():
    """
    创建示例图像

    Returns:
        (图像1, 图像2) 元组
    """
    # 创建第一张图像
    img1 = np.zeros((300, 400), dtype=np.uint8)
    cv2.rectangle(img1, (50, 50), (150, 150), 255, -1)
    cv2.circle(img1, (300, 100), 50, 200, -1)
    cv2.putText(img1, "OpenCV", (100, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)

    # 创建第二张图像（轻微变换）
    img2 = np.zeros((300, 400), dtype=np.uint8)
    M = np.float32([[1, 0, 15], [0, 1, 10]])
    img2 = cv2.warpAffine(img1, M, (400, 300))

    return img1, img2


def demo_feature_detection():
    """
    演示特征点检测
    """
    print("=" * 60)
    print("特征点检测演示")
    print("=" * 60)

    # 创建示例图像
    img = np.zeros((300, 400), dtype=np.uint8)
    cv2.rectangle(img, (50, 50), (150, 150), 255, -1)
    cv2.circle(img, (300, 100), 50, 200, -1)
    cv2.putText(img, "Feature", (100, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)

    # SIFT检测
    print("\n1. SIFT特征检测")
    sift_detector = FeatureDetector(method='sift')
    sift_kp, sift_desc = sift_detector.detect_and_compute(img)
    print(f"   检测到 {len(sift_kp)} 个特征点")
    print(f"   描述子形状: {sift_desc.shape}")

    # ORB检测
    print("\n2. ORB特征检测")
    orb_detector = FeatureDetector(method='orb')
    orb_kp, orb_desc = orb_detector.detect_and_compute(img)
    print(f"   检测到 {len(orb_kp)} 个特征点")
    print(f"   描述子形状: {orb_desc.shape}")

    # 绘制特征点
    vis = Visualizer()
    sift_img = vis.draw_keypoints(img, sift_kp)
    orb_img = vis.draw_keypoints(img, orb_kp)

    # 保存结果
    os.makedirs('output', exist_ok=True)
    cv2.imwrite('output/sift_keypoints.jpg', sift_img)
    cv2.imwrite('output/orb_keypoints.jpg', orb_img)
    print("\n结果已保存到 output/ 目录")


def demo_feature_matching():
    """
    演示特征匹配
    """
    print("\n" + "=" * 60)
    print("特征匹配演示")
    print("=" * 60)

    # 创建示例图像
    img1, img2 = create_sample_images()

    # SIFT匹配
    print("\n1. SIFT特征匹配")
    sift_detector = FeatureDetector(method='sift')
    sift_matcher = FeatureMatcher(method='bf', cross_check=True)

    kp1, des1 = sift_detector.detect_and_compute(img1)
    kp2, des2 = sift_detector.detect_and_compute(img2)

    sift_matches = sift_matcher.match(des1, des2)
    sift_matches = sorted(sift_matches, key=lambda x: x.distance)

    print(f"   图像1特征点: {len(kp1)}")
    print(f"   图像2特征点: {len(kp2)}")
    print(f"   匹配数量: {len(sift_matches)}")
    print(f"   平均距离: {np.mean([m.distance for m in sift_matches]):.2f}")

    # ORB匹配
    print("\n2. ORB特征匹配")
    orb_detector = FeatureDetector(method='orb')
    orb_matcher = FeatureMatcher(method='bf', cross_check=True, norm_type=cv2.NORM_HAMMING)

    kp1_orb, des1_orb = orb_detector.detect_and_compute(img1)
    kp2_orb, des2_orb = orb_detector.detect_and_compute(img2)

    orb_matches = orb_matcher.match(des1_orb, des2_orb)
    orb_matches = sorted(orb_matches, key=lambda x: x.distance)

    print(f"   图像1特征点: {len(kp1_orb)}")
    print(f"   图像2特征点: {len(kp2_orb)}")
    print(f"   匹配数量: {len(orb_matches)}")
    print(f"   平均距离: {np.mean([m.distance for m in orb_matches]):.2f}")

    # 绘制匹配结果
    vis = Visualizer()
    sift_match_img = vis.draw_matches(img1, kp1, img2, kp2, sift_matches)
    orb_match_img = vis.draw_matches(img1, kp1_orb, img2, kp2_orb, orb_matches)

    # 保存结果
    os.makedirs('output', exist_ok=True)
    cv2.imwrite('output/sift_matches.jpg', sift_match_img)
    cv2.imwrite('output/orb_matches.jpg', orb_match_img)
    print("\n结果已保存到 output/ 目录")


def demo_ratio_test():
    """
    演示比率测试
    """
    print("\n" + "=" * 60)
    print("比率测试演示")
    print("=" * 60)

    # 创建示例图像
    img1, img2 = create_sample_images()

    # 使用SIFT
    detector = FeatureDetector(method='sift')
    matcher = FeatureMatcher(method='bf', cross_check=False)

    kp1, des1 = detector.detect_and_compute(img1)
    kp2, des2 = detector.detect_and_compute(img2)

    # KNN匹配
    knn_matches = matcher.knn_match(des1, des2, k=2)

    # 应用比率测试
    for ratio in [0.5, 0.6, 0.7, 0.8]:
        good_matches = matcher.ratio_test(knn_matches, ratio=ratio)
        print(f"   比率阈值 {ratio}: {len(good_matches)} 个匹配")


def demo_comparison():
    """
    演示方法对比
    """
    print("\n" + "=" * 60)
    print("方法对比演示")
    print("=" * 60)

    # 创建示例图像
    img1, img2 = create_sample_images()

    results = {}

    for method in ['sift', 'orb']:
        detector = FeatureDetector(method=method)
        matcher = FeatureMatcher(method='bf', cross_check=True)

        kp1, des1 = detector.detect_and_compute(img1)
        kp2, des2 = detector.detect_and_compute(img2)

        matches = matcher.match(des1, des2)

        results[method] = {
            'keypoints1': len(kp1),
            'keypoints2': len(kp2),
            'matches': len(matches),
            'avg_distance': np.mean([m.distance for m in matches]) if matches else 0
        }

    print("\n对比结果:")
    print("-" * 60)
    print(f"{'方法':<10} {'特征点1':<10} {'特征点2':<10} {'匹配数':<10} {'平均距离':<10}")
    print("-" * 60)
    for method, stats in results.items():
        print(f"{method.upper():<10} {stats['keypoints1']:<10} {stats['keypoints2']:<10} "
              f"{stats['matches']:<10} {stats['avg_distance']:<10.2f}")


def main():
    """主函数"""
    print("特征匹配 SIFT/ORB 演示程序")
    print("=" * 60)

    # 运行演示
    demo_feature_detection()
    demo_feature_matching()
    demo_ratio_test()
    demo_comparison()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
