"""
DETR 训练示例
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.detr import build_detr
from src.loss import SetCriterion
from src.matcher import build_matcher
from src.dataset import create_simple_dataset, collate_fn


def train_one_epoch(model, criterion, data_loader, optimizer, device):
    """
    训练一个epoch
    """
    model.train()
    criterion.train()

    total_loss = 0
    num_batches = 0

    for batch_idx, (images, targets) in enumerate(data_loader):
        images = images.to(device)
        targets = [{k: v.to(device) for k, v in t.items()} for t in targets]

        # 前向传播
        outputs = model(images)

        # 计算损失
        losses = criterion(outputs, targets)
        total_loss_batch = sum(losses.values())

        # 反向传播
        optimizer.zero_grad()
        total_loss_batch.backward()
        optimizer.step()

        total_loss += total_loss_batch.item()
        num_batches += 1

        if batch_idx % 10 == 0:
            print(f"Batch {batch_idx}: Loss = {total_loss_batch.item():.4f}")

    return total_loss / num_batches


def main():
    """
    主训练函数
    """
    # 超参数
    num_classes = 5
    num_queries = 100
    hidden_dim = 256
    nhead = 8
    num_encoder_layers = 6
    num_decoder_layers = 6
    batch_size = 4
    num_epochs = 5
    learning_rate = 1e-4
    weight_decay = 1e-4

    # 设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    # 创建数据集
    print("Creating dataset...")
    train_dataset = create_simple_dataset(
        num_samples=200,
        image_size=320,
        num_classes=num_classes,
        max_objects=5
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0
    )

    # 创建模型
    print("Building model...")
    model = build_detr(
        num_classes=num_classes,
        num_queries=num_queries,
        backbone_model='resnet18',
        train_backbone=True,
        hidden_dim=hidden_dim,
        nhead=nhead,
        num_encoder_layers=num_encoder_layers,
        num_decoder_layers=num_decoder_layers
    )
    model = model.to(device)

    # 创建损失函数
    matcher = build_matcher(cost_class=1, cost_bbox=5, cost_giou=2)
    weight_dict = {'loss_ce': 1, 'loss_bbox': 5, 'loss_giou': 2}
    criterion = SetCriterion(
        num_classes=num_classes,
        matcher=matcher,
        weight_dict=weight_dict,
        eos_coef=0.1,
        losses=['labels', 'boxes']
    )
    criterion = criterion.to(device)

    # 创建优化器
    param_dicts = [
        {"params": [p for n, p in model.named_parameters() if "backbone" not in n and p.requires_grad]},
        {
            "params": [p for n, p in model.named_parameters() if "backbone" in n and p.requires_grad],
            "lr": learning_rate * 0.1,
        },
    ]
    optimizer = optim.AdamW(param_dicts, lr=learning_rate, weight_decay=weight_decay)

    # 学习率调度器
    lr_scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=200, gamma=0.1)

    # 训练循环
    print("Starting training...")
    for epoch in range(num_epochs):
        print(f"\nEpoch {epoch + 1}/{num_epochs}")
        print("-" * 50)

        train_loss = train_one_epoch(model, criterion, train_loader, optimizer, device)
        lr_scheduler.step()

        print(f"Epoch {epoch + 1} - Average Loss: {train_loss:.4f}")

    # 保存模型
    save_path = os.path.join(os.path.dirname(__file__), 'detr_model.pth')
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'epoch': num_epochs,
    }, save_path)
    print(f"\nModel saved to {save_path}")

    # 测试推理
    print("\nTesting inference...")
    model.eval()
    with torch.no_grad():
        test_images = torch.randn(1, 3, 320, 320).to(device)
        outputs = model(test_images)

        pred_logits = outputs['pred_logits']
        pred_boxes = outputs['pred_boxes']

        # 获取预测类别和置信度
        prob = pred_logits.softmax(-1)
        scores, labels = prob[..., :-1].max(-1)

        print(f"Predictions shape: {pred_logits.shape}")
        print(f"Number of queries: {num_queries}")
        print(f"Max confidence: {scores.max().item():.4f}")
        print(f"Predicted classes: {labels[0].unique().tolist()}")


if __name__ == '__main__':
    main()
