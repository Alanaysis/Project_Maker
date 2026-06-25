"""
Text Detection Training Example

Trains EAST model on synthetic data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import torch
import torch.optim as optim
from torch.utils.data import DataLoader

from src.model import EASTNet
from src.loss.east_loss import EASTLoss
from src.data.dataset import TextDetectionDataset


def train_one_epoch(model, dataloader, criterion, optimizer, device):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    total_score_loss = 0
    total_geo_loss = 0

    for batch_idx, (images, score_maps, geo_maps, masks) in enumerate(dataloader):
        images = images.to(device)
        score_maps = score_maps.to(device)
        geo_maps = geo_maps.to(device)
        masks = masks.to(device)

        # Forward
        output = model(images)
        loss, score_loss, geo_loss = criterion(
            output['score'], output['geo'],
            score_maps, geo_maps, masks
        )

        # Backward
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        total_score_loss += score_loss.item()
        total_geo_loss += geo_loss.item()

    n = len(dataloader)
    return total_loss / n, total_score_loss / n, total_geo_loss / n


def main():
    print("=" * 60)
    print("Text Detection Training")
    print("=" * 60)

    # Hyperparameters
    config = {
        'epochs': 3,
        'batch_size': 4,
        'learning_rate': 1e-3,
        'img_size': 256,
        'num_samples': 100,
        'backbone': 'light',
    }

    print(f"\nConfig: {config}")

    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")

    # Create model
    print("\n[1/4] Creating model...")
    model = EASTNet(backbone_type=config['backbone'], neck_type='unet', geo_type='rbox')
    model = model.to(device)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Model parameters: {total_params:,}")

    # Create dataset
    print("\n[2/4] Creating dataset...")
    train_dataset = TextDetectionDataset(
        num_samples=config['num_samples'],
        img_size=config['img_size']
    )
    train_loader = DataLoader(
        train_dataset,
        batch_size=config['batch_size'],
        shuffle=True,
        num_workers=0
    )
    print(f"  Dataset size: {len(train_dataset)}")
    print(f"  Batches per epoch: {len(train_loader)}")

    # Loss and optimizer
    print("\n[3/4] Setting up training...")
    criterion = EASTLoss(lambda_score=1.0, lambda_geo=1.0)
    optimizer = optim.Adam(model.parameters(), lr=config['learning_rate'])
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config['epochs'])

    # Training loop
    print("\n[4/4] Training...")
    print("-" * 60)

    for epoch in range(config['epochs']):
        loss, score_loss, geo_loss = train_one_epoch(
            model, train_loader, criterion, optimizer, device
        )
        scheduler.step()

        lr = optimizer.param_groups[0]['lr']
        print(f"Epoch {epoch+1}/{config['epochs']}: "
              f"Loss={loss:.4f}, Score={score_loss:.4f}, Geo={geo_loss:.4f}, "
              f"LR={lr:.6f}")

    print("-" * 60)

    # Save model
    save_path = os.path.join(os.path.dirname(__file__), '..', 'checkpoints', 'east_model.pth')
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': config,
    }, save_path)
    print(f"\nModel saved to: {save_path}")

    print("\n" + "=" * 60)
    print("Training completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
