"""视频理解评估脚本"""

import argparse
import os
import sys

import torch
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from video_understanding.data.video_dataset import SyntheticVideoDataset
from video_understanding.models.classifier import VideoContentClassifier


def main():
    parser = argparse.ArgumentParser(description="视频分类评估")
    parser.add_argument("--checkpoint", type=str, help="模型检查点路径")
    parser.add_argument("--synthetic", action="store_true", help="使用合成数据")
    parser.add_argument("--num-classes", type=int, default=10)
    parser.add_argument("--num-frames", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 创建数据集
    dataset = SyntheticVideoDataset(
        num_samples=100, num_frames=args.num_frames,
        num_classes=args.num_classes, frame_size=(112, 112), seed=999
    )
    loader = DataLoader(dataset, batch_size=args.batch_size)

    # 创建模型
    model = VideoContentClassifier(
        num_classes=args.num_classes, pretrained=False
    ).to(device)

    if args.checkpoint and os.path.exists(args.checkpoint):
        model.load_state_dict(torch.load(args.checkpoint, map_location=device))
        print(f"加载检查点: {args.checkpoint}")

    # 评估
    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for frames, labels in loader:
            frames, labels = frames.to(device), labels.to(device)
            logits = model(frames)
            preds = logits.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += frames.size(0)

    accuracy = correct / total
    print(f"评估结果: 准确率 = {accuracy:.4f} ({correct}/{total})")


if __name__ == "__main__":
    main()
