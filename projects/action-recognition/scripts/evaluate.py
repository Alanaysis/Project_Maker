#!/usr/bin/env python3
"""
Evaluation script for action recognition model.

Usage:
    python scripts/evaluate.py --checkpoint checkpoints/best_model.pth --synthetic
    python scripts/evaluate.py --checkpoint checkpoints/best_model.pth --data-root data/val
"""

import argparse
import os
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from action_recognition.models.action_classifier import ActionClassifier
from action_recognition.data.video_dataset import VideoDataset
from action_recognition.data.frame_sampler import FrameSampler


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate action recognition model")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--data-root", type=str, default="", help="Path to test data")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic data")
    parser.add_argument("--num-classes", type=int, default=10, help="Number of classes")
    parser.add_argument("--backbone", type=str, default="resnet18", help="CNN backbone")
    parser.add_argument("--temporal-arch", type=str, default="lstm", help="Temporal architecture")
    parser.add_argument("--hidden-dim", type=int, default=256, help="Hidden dimension")
    parser.add_argument("--num-frames", type=int, default=8, help="Frames per clip")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size")
    parser.add_argument("--top-k", type=int, default=5, help="Top-k predictions to show")
    parser.add_argument("--device", type=str, default=None, help="Device")
    return parser.parse_args()


def main():
    args = parse_args()
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    # Dataset
    sampler = FrameSampler(num_frames=args.num_frames, strategy="uniform")

    if args.synthetic:
        dataset = VideoDataset(
            synthetic=True,
            num_synthetic_classes=args.num_classes,
            num_synthetic_samples=50,
            frame_sampler=sampler,
        )
    else:
        dataset = VideoDataset(data_root=args.data_root, frame_sampler=sampler)

    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)

    # Model
    model = ActionClassifier(
        num_classes=dataset.num_classes,
        backbone=args.backbone,
        temporal_arch=args.temporal_arch,
        hidden_dim=args.hidden_dim,
    ).to(device)

    # Load checkpoint
    checkpoint = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(checkpoint)
    model.eval()

    print(f"Loaded checkpoint: {args.checkpoint}")
    print(f"Evaluating on {len(dataset)} samples...")

    # Evaluate
    correct = 0
    total = 0
    top5_correct = 0

    with torch.no_grad():
        for videos, labels in loader:
            videos = videos.to(device)
            labels = labels.to(device)

            outputs = model(videos)

            # Top-1 accuracy
            _, predicted = outputs.max(1)
            correct += predicted.eq(labels).sum().item()

            # Top-5 accuracy
            _, top5_pred = outputs.topk(min(5, dataset.num_classes), dim=1)
            for i in range(labels.size(0)):
                if labels[i] in top5_pred[i]:
                    top5_correct += 1

            total += labels.size(0)

    top1_acc = correct / total
    top5_acc = top5_correct / total

    print(f"\nResults:")
    print(f"  Top-1 Accuracy: {top1_acc:.4f} ({correct}/{total})")
    print(f"  Top-5 Accuracy: {top5_acc:.4f} ({top5_correct}/{total})")


if __name__ == "__main__":
    main()
