"""
视频理解基础示例

演示视频理解的核心功能：
1. 特征提取
2. 内容分类
3. 关键帧提取
4. 视频摘要
"""

import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from video_understanding.core.content_analyzer import ContentAnalyzer
from video_understanding.core.keyframe_extractor import KeyframeExtractor
from video_understanding.models.classifier import VideoContentClassifier
from video_understanding.models.feature_extractor import VideoFeatureExtractor
from video_understanding.models.summarizer import VideoSummarizer


def demo_feature_extraction():
    """演示特征提取"""
    print("=" * 60)
    print("1. 视频特征提取")
    print("=" * 60)

    # 创建特征提取器
    extractor = VideoFeatureExtractor(
        backbone="resnet18", pretrained=False, feature_dim=256
    )

    # 模拟视频帧 (16帧, 3通道, 112x112)
    frames = torch.randn(16, 3, 112, 112)

    # 提取帧级特征
    frame_features = extractor.extract_frame_features(frames)
    print(f"  帧特征形状: {frame_features.shape}")

    # 提取视频级特征
    video_feature = extractor(frames)
    print(f"  视频特征形状: {video_feature.shape}")

    # 不同池化方式
    for pooling in ["mean", "max", "attention"]:
        ext = VideoFeatureExtractor(
            backbone="resnet18", pretrained=False, pooling=pooling
        )
        feat = ext(frames)
        print(f"  {pooling} 池化特征: {feat.shape}")

    return video_feature


def demo_content_classification():
    """演示内容分类"""
    print("\n" + "=" * 60)
    print("2. 视频内容分类")
    print("=" * 60)

    # 创建分类器
    classifier = VideoContentClassifier(
        num_classes=10, backbone="resnet18", pretrained=False
    )

    # 模拟视频
    frames = torch.randn(1, 8, 3, 112, 112)  # (B, T, C, H, W)

    # 前向传播
    logits = classifier(frames)
    print(f"  分类 logits 形状: {logits.shape}")

    # 预测
    results = classifier.predict(frames, top_k=5)
    print(f"  预测类别: {results[0]['predicted_class']}")
    print(f"  置信度: {results[0]['confidence']:.4f}")
    print(f"  Top-5 类别: {results[0]['top_classes']}")
    print(f"  Top-5 概率: {[f'{p:.4f}' for p in results[0]['top_probs']]}")

    # 提取特征（不含分类）
    features = classifier.get_features(frames.squeeze(0))
    print(f"  特征形状: {features.shape}")


def demo_keyframe_extraction():
    """演示关键帧提取"""
    print("\n" + "=" * 60)
    print("3. 关键帧提取")
    print("=" * 60)

    import numpy as np

    # 创建不同颜色的合成帧
    frames = []
    for i in range(20):
        color = (i * 12 % 256, (i * 37) % 256, (i * 73) % 256)
        frame = np.full((100, 100, 3), color, dtype=np.uint8)
        frames.append(frame)

    # 不同方法提取关键帧
    for method in ["histogram", "threshold", "clustering"]:
        extractor = KeyframeExtractor(method=method, max_keyframes=5)
        indices, scores = extractor.extract(frames)
        print(f"  {method}: 关键帧索引={indices}, 分数={[f'{s:.3f}' for s in scores]}")


def demo_video_summarization():
    """演示视频摘要"""
    print("\n" + "=" * 60)
    print("4. 视频摘要生成")
    print("=" * 60)

    # 创建摘要生成器
    summarizer = VideoSummarizer(num_keyframes=3)

    # 模拟视频帧
    frames = torch.randn(16, 3, 112, 112)

    # 生成摘要
    summary = summarizer.generate_summary(frames)
    print(f"  总帧数: {summary['num_frames']}")
    print(f"  关键帧数: {summary['num_keyframes']}")
    print(f"  关键帧索引: {summary['keyframe_indices']}")
    print(f"  关键帧分数: {[f'{s:.4f}' for s in summary['keyframe_scores']]}")
    print(f"  场景变化点: {summary['scene_changes']}")
    print(f"  平均重要性: {summary['average_importance']:.4f}")


def demo_content_analyzer():
    """演示完整的内容分析流程"""
    print("\n" + "=" * 60)
    print("5. 完整内容分析")
    print("=" * 60)

    # 创建分析器
    analyzer = ContentAnalyzer(num_classes=10, num_frames=8, num_keyframes=3)

    # 模拟视频帧
    frames = torch.randn(8, 3, 112, 112)

    # 分析
    results = analyzer.analyze_frames(frames)
    print(f"  视频特征维度: {results['feature_dim']}")
    print(f"  预测类别: {results['predictions']['predicted_class']}")
    print(f"  置信度: {results['predictions']['confidence']:.4f}")
    print(f"  关键帧索引: {results['keyframe_indices']}")
    print(f"  重要性分数: {[f'{s:.4f}' for s in results['importance_scores']]}")

    # 帧间相似度
    similarity = analyzer.compute_frame_similarity(frames)
    print(f"  相似度矩阵形状: {similarity.shape}")
    print(f"  对角线均值: {similarity.diagonal().mean():.4f}")

    # 片段检测
    segments = analyzer.detect_segments(frames)
    print(f"  检测到 {len(segments)} 个片段: {segments}")


def main():
    print("视频理解 (Video Understanding) - 功能演示\n")

    demo_feature_extraction()
    demo_content_classification()
    demo_keyframe_extraction()
    demo_video_summarization()
    demo_content_analyzer()

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
