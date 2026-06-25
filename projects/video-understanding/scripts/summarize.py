"""视频摘要脚本

从视频文件生成摘要，包括关键帧提取和内容分析。
"""

import argparse
import json
import os
import sys

import cv2
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from video_understanding.core.content_analyzer import ContentAnalyzer
from video_understanding.data.frame_sampler import FrameSampler
from video_understanding.models.summarizer import VideoSummarizer
from video_understanding.utils.video_utils import extract_frames, frames_to_tensor, get_video_info


def main():
    parser = argparse.ArgumentParser(description="视频摘要生成")
    parser.add_argument("video", type=str, help="视频文件路径")
    parser.add_argument("--num-frames", type=int, default=16, help="采样帧数")
    parser.add_argument("--num-keyframes", type=int, default=5, help="关键帧数")
    parser.add_argument("--output", type=str, default=None, help="输出 JSON 路径")
    parser.add_argument("--save-keyframes", action="store_true", help="保存关键帧图片")
    args = parser.parse_args()

    # 获取视频信息
    info = get_video_info(args.video)
    print(f"视频信息: {info}")

    # 采样帧
    print(f"采样 {args.num_frames} 帧...")
    frames = extract_frames(args.video, method="uniform", num_frames=args.num_frames)
    print(f"采样到 {len(frames)} 帧")

    # 转为张量
    tensor = frames_to_tensor(frames)

    # 生成摘要
    summarizer = VideoSummarizer(num_keyframes=args.num_keyframes)
    summary = summarizer.generate_summary(tensor)

    # 内容分析
    analyzer = ContentAnalyzer(num_frames=args.num_frames)
    analysis = analyzer.analyze_frames(tensor)

    # 输出结果
    result = {
        "video_info": info,
        "summary": {
            "num_frames": summary["num_frames"],
            "num_keyframes": summary["num_keyframes"],
            "keyframe_indices": summary["keyframe_indices"],
            "keyframe_scores": [round(s, 4) for s in summary["keyframe_scores"]],
            "scene_changes": summary["scene_changes"],
            "average_importance": round(summary["average_importance"], 4),
        },
        "analysis": {
            "predicted_class": analysis["predictions"]["predicted_class"],
            "confidence": round(analysis["predictions"]["confidence"], 4),
            "feature_dim": analysis["feature_dim"],
        },
    }

    print("\n=== 视频摘要 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存到: {args.output}")

    # 保存关键帧
    if args.save_keyframes:
        os.makedirs("keyframes", exist_ok=True)
        for i, idx in enumerate(summary["keyframe_indices"]):
            path = f"keyframes/keyframe_{i:03d}_frame_{idx:04d}.jpg"
            cv2.imwrite(path, frames[idx])
            print(f"保存关键帧: {path}")


if __name__ == "__main__":
    main()
