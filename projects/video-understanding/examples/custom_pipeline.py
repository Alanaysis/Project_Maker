"""
自定义视频理解管道示例

展示如何组合各个组件构建自定义的视频理解管道。
"""

import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from video_understanding.core.keyframe_extractor import KeyframeExtractor
from video_understanding.data.frame_sampler import FrameSampler
from video_understanding.models.feature_extractor import VideoFeatureExtractor
from video_understanding.utils.video_utils import frames_to_tensor


class CustomVideoPipeline:
    """自定义视频理解管道

    展示如何将各个组件组合成自定义管道。

    流程: 帧采样 -> 特征提取 -> 关键帧 -> 摘要
    """

    def __init__(
        self,
        num_sample_frames: int = 32,
        num_keyframes: int = 5,
        feature_dim: int = 256,
    ):
        self.sampler = FrameSampler(num_frames=num_sample_frames, method="uniform")
        self.extractor = VideoFeatureExtractor(
            backbone="resnet18", pretrained=False, feature_dim=feature_dim
        )
        self.keyframe_extractor = KeyframeExtractor(
            method="histogram", max_keyframes=num_keyframes
        )
        self.feature_dim = feature_dim

    def process(self, frames_np: list) -> dict:
        """处理视频帧

        Args:
            frames_np: numpy 帧列表

        Returns:
            处理结果字典
        """
        # 1. 采样
        total = len(frames_np)
        indices = self.sampler.sample(total)
        sampled_frames = [frames_np[i] for i in indices]

        # 2. 特征提取
        tensor = frames_to_tensor(sampled_frames)
        features = self.extractor.extract_frame_features(tensor)
        video_feature = self.extractor.temporal_pool(features)

        # 3. 关键帧
        kf_indices, kf_scores = self.keyframe_extractor.extract(sampled_frames)

        return {
            "num_original_frames": total,
            "num_sampled_frames": len(sampled_frames),
            "video_feature": video_feature.detach().numpy(),
            "feature_dim": video_feature.shape[-1],
            "keyframe_indices": kf_indices,
            "keyframe_scores": kf_scores,
        }

    def compare_frames(self, frames1_np: list, frames2_np: list) -> float:
        """比较两个视频的相似度

        Args:
            frames1_np: 第一个视频的帧列表
            frames2_np: 第二个视频的帧列表

        Returns:
            余弦相似度
        """
        t1 = frames_to_tensor(frames1_np)
        t2 = frames_to_tensor(frames2_np)

        f1 = self.extractor(t1)
        f2 = self.extractor(t2)

        # 余弦相似度
        sim = torch.cosine_similarity(f1.unsqueeze(0), f2.unsqueeze(0))
        return sim.item()


def main():
    print("自定义视频理解管道示例\n")

    # 创建管道
    pipeline = CustomVideoPipeline(
        num_sample_frames=16, num_keyframes=3, feature_dim=256
    )

    # 模拟视频帧
    frames1 = [np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8) for _ in range(30)]
    frames2 = [np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8) for _ in range(25)]

    # 处理视频 1
    print("处理视频 1...")
    result1 = pipeline.process(frames1)
    print(f"  原始帧数: {result1['num_original_frames']}")
    print(f"  采样帧数: {result1['num_sampled_frames']}")
    print(f"  特征维度: {result1['feature_dim']}")
    print(f"  关键帧: {result1['keyframe_indices']}")

    # 处理视频 2
    print("\n处理视频 2...")
    result2 = pipeline.process(frames2)
    print(f"  原始帧数: {result2['num_original_frames']}")
    print(f"  关键帧: {result2['keyframe_indices']}")

    # 比较相似度
    similarity = pipeline.compare_frames(frames1, frames2)
    print(f"\n视频相似度: {similarity:.4f}")

    print("\n完成!")


if __name__ == "__main__":
    main()
