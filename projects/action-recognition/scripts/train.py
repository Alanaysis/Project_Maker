#!/usr/bin/env python3
"""
Training script for action recognition model.

Usage:
    python scripts/train.py --config configs/default.yaml
    python scripts/train.py --synthetic --epochs 5 --batch-size 4
"""

import argparse
import os
import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from action_recognition.models.action_classifier import ActionClassifier
from action_recognition.data.video_dataset import VideoDataset
from action_recognition.data.frame_sampler import FrameSampler


def parse_args():
    parser = argparse.ArgumentParser(description="Train action recognition model")
    parser.add_argument("--data-root", type=str, default="", help="Path to data directory")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic data for testing")
    parser.add_argument("--num-classes", type=int, default=10, help="Number of action classes")
    parser.add_argument("--backbone", type=str, default="resnet18", help="CNN backbone")
    parser.add_argument("--temporal-arch", type=str, default="lstm", help="Temporal architecture")
    parser.add_argument("--hidden-dim", type=int, default=256, help="Hidden dimension")
    parser.add_argument("--num-frames", type=int, default=8, help="Frames per clip")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--device", type=str, default=None, help="Device (cuda/cpu)")
    parser.add_argument("--save-dir", type=str, default="checkpoints", help="Save directory")
    return parser.parse_args()


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for videos, labels in loader:
        videos = videos.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(videos)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * videos.size(0)
        _, predicted = outputs.max(1)
        correct += predicted.eq(labels).sum().item()
        total += labels.size(0)

    return total_loss / total, correct / total


def validate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for videos, labels in loader:
            videos = videos.to(device)
            labels = labels.to(device)

            outputs = model(videos)
            loss = criterion(outputs, labels)

            total_loss += loss.item() * videos.size(0)
            _, predicted = outputs.max(1)
            correct += predicted.eq(labels).sum().item()
            total += labels.size(0)

    return total_loss / total, correct / total


def main():
    args = parse_args()

    # Device
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Dataset
    sampler = FrameSampler(num_frames=args.num_frames, strategy="uniform")

    if args.synthetic:
        print("Using synthetic data for testing")
        train_dataset = VideoDataset(
            synthetic=True,
            num_synthetic_classes=args.num_classes,
            num_synthetic_samples=100,
            frame_sampler=sampler,
        )
        val_dataset = VideoDataset(
            synthetic=True,
            num_synthetic_classes=args.num_classes,
            num_synthetic_samples=20,
            frame_sampler=sampler,
        )
    else:
        train_dataset = VideoDataset(
            data_root=os.path.join(args.data_root, "train"),
            frame_sampler=sampler,
        )
        val_dataset = VideoDataset(
            data_root=os.path.join(args.data_root, "val"),
            frame_sampler=sampler,
            class_to_idx=train_dataset.class_to_idx,
        )

    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=0
    )
    val_loader = DataLoader(
        val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0
    )

    # Model
    model = ActionClassifier(
        num_classes=train_dataset.num_classes,
        backbone=args.backbone,
        temporal_arch=args.temporal_arch,
        hidden_dim=args.hidden_dim,
        pretrained=not args.synthetic,
    ).to(device)

    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Training setup
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

    # Training loop
    os.makedirs(args.save_dir, exist_ok=True)
    best_acc = 0.0

    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device
        )
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        scheduler.step()

        print(
            f"Epoch {epoch}/{args.epochs} | "
            f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
            f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}"
        )

        if val_acc > best_acc:
            best_acc = val_acc
            save_path = os.path.join(args.save_dir, "best_model.pth")
            torch.save(model.state_dict(), save_path)
            print(f"  -> Saved best model (acc={best_acc:.4f})")

    print(f"\nTraining complete. Best validation accuracy: {best_acc:.4f}")


if __name__ == "__main__":
    main()
