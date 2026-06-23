"""
YOLO v1 Network Architecture.

Implements a simplified YOLO v1 architecture for object detection.

Architecture Overview:
- Input: 448x448x3 image
- Backbone: Series of convolutional layers for feature extraction
- Head: Fully connected layers for prediction
- Output: S x S x (B * 5 + C) tensor

Where:
- S = grid size (7 for YOLOv1)
- B = number of boxes per cell (2 for YOLOv1)
- C = number of classes (20 for PASCAL VOC)

Each cell predicts:
- B boxes with (x, y, w, h, confidence)
- C class probabilities
"""

import torch
import torch.nn as nn
from typing import List, Tuple, Optional


class ConvBlock(nn.Module):
    """Convolution + BatchNorm + LeakyReLU block."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        stride: int = 1,
        padding: int = 0,
    ):
        super().__init__()
        self.conv = nn.Conv2d(
            in_channels, out_channels, kernel_size, stride, padding, bias=False
        )
        self.bn = nn.BatchNorm2d(out_channels)
        self.act = nn.LeakyReLU(0.1, inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.bn(self.conv(x)))


class YOLOv1(nn.Module):
    """
    YOLO v1 object detection network.

    Simplified version of the original YOLOv1 architecture.
    Uses fewer layers for faster training and inference.

    Args:
        grid_size: Number of grid cells (S). Default: 7
        num_boxes: Number of bounding boxes per cell (B). Default: 2
        num_classes: Number of object classes (C). Default: 20
    """

    def __init__(
        self,
        grid_size: int = 7,
        num_boxes: int = 2,
        num_classes: int = 20,
    ):
        super().__init__()
        self.grid_size = grid_size
        self.num_boxes = num_boxes
        self.num_classes = num_classes
        self.output_size = num_boxes * 5 + num_classes

        # Backbone: Convolutional layers for feature extraction
        # Input: 3 x 448 x 448
        self.backbone = nn.Sequential(
            # Layer 1: 3 -> 64 channels, 7x7 kernel
            ConvBlock(3, 64, kernel_size=7, stride=2, padding=3),  # -> 64 x 224 x 224
            nn.MaxPool2d(2, stride=2),  # -> 64 x 112 x 112

            # Layer 2: 64 -> 192 channels, 3x3 kernel
            ConvBlock(64, 192, kernel_size=3, padding=1),  # -> 192 x 112 x 112
            nn.MaxPool2d(2, stride=2),  # -> 192 x 56 x 56

            # Layer 3-4: 192 -> 128 -> 256 channels
            ConvBlock(192, 128, kernel_size=1),  # -> 128 x 56 x 56
            ConvBlock(128, 256, kernel_size=3, padding=1),  # -> 256 x 56 x 56
            ConvBlock(256, 256, kernel_size=1),  # -> 256 x 56 x 56
            ConvBlock(256, 512, kernel_size=3, padding=1),  # -> 512 x 56 x 56
            nn.MaxPool2d(2, stride=2),  # -> 512 x 28 x 28

            # Layer 5-8: Repeated 3x3 and 1x1 convolutions
            ConvBlock(512, 256, kernel_size=1),
            ConvBlock(256, 512, kernel_size=3, padding=1),
            ConvBlock(512, 256, kernel_size=1),
            ConvBlock(256, 512, kernel_size=3, padding=1),
            ConvBlock(512, 256, kernel_size=1),
            ConvBlock(256, 512, kernel_size=3, padding=1),
            ConvBlock(512, 256, kernel_size=1),
            ConvBlock(256, 512, kernel_size=3, padding=1),
            ConvBlock(512, 512, kernel_size=1),
            ConvBlock(512, 1024, kernel_size=3, padding=1),  # -> 1024 x 28 x 28
            nn.MaxPool2d(2, stride=2),  # -> 1024 x 14 x 14

            # Layer 9-10: More convolutions
            ConvBlock(1024, 512, kernel_size=1),
            ConvBlock(512, 1024, kernel_size=3, padding=1),
            ConvBlock(1024, 512, kernel_size=1),
            ConvBlock(512, 1024, kernel_size=3, padding=1),
            ConvBlock(1024, 1024, kernel_size=3, padding=1),  # -> 1024 x 14 x 14
            ConvBlock(1024, 1024, kernel_size=3, stride=2, padding=1),  # -> 1024 x 7 x 7
        )

        # Detection head
        self.head = nn.Sequential(
            ConvBlock(1024, 1024, kernel_size=3, padding=1),
            ConvBlock(1024, 1024, kernel_size=3, padding=1),
        )

        # Fully connected layers for prediction
        # Flatten: 1024 * 7 * 7 = 50176
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(1024 * grid_size * grid_size, 4096),
            nn.LeakyReLU(0.1, inplace=True),
            nn.Dropout(0.5),
            nn.Linear(4096, grid_size * grid_size * self.output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor of shape (batch, 3, 448, 448)

        Returns:
            Predictions of shape (batch, S*S*(B*5+C))
            Can be reshaped to (batch, S, S, B*5+C)
        """
        x = self.backbone(x)
        x = self.head(x)
        x = self.fc(x)
        return x

    def predict(
        self, x: torch.Tensor, confidence_threshold: float = 0.1
    ) -> List[dict]:
        """
        Run inference and return decoded predictions.

        Args:
            x: Input tensor of shape (batch, 3, H, W)
            confidence_threshold: Minimum confidence to keep detection

        Returns:
            List of detection dictionaries
        """
        from .utils import decode_predictions

        raw = self.forward(x)
        batch_size = raw.shape[0]
        # Reshape to (batch, S, S, B*5+C)
        predictions = raw.view(
            batch_size, self.grid_size, self.grid_size, self.output_size
        )
        return decode_predictions(
            predictions,
            grid_size=self.grid_size,
            num_boxes=self.num_boxes,
            num_classes=self.num_classes,
            confidence_threshold=confidence_threshold,
        )


class TinyYOLOv1(nn.Module):
    """
    A tiny YOLO v1 variant for testing and prototyping.

    Much smaller than the full YOLOv1, suitable for:
    - Unit testing
    - Quick experiments
    - Learning the architecture

    Args:
        grid_size: Number of grid cells (S). Default: 7
        num_boxes: Number of bounding boxes per cell (B). Default: 2
        num_classes: Number of object classes (C). Default: 20
    """

    def __init__(
        self,
        grid_size: int = 7,
        num_boxes: int = 2,
        num_classes: int = 20,
    ):
        super().__init__()
        self.grid_size = grid_size
        self.num_boxes = num_boxes
        self.num_classes = num_classes
        self.output_size = num_boxes * 5 + num_classes

        self.features = nn.Sequential(
            # Simple backbone
            ConvBlock(3, 16, kernel_size=3, stride=1, padding=1),  # -> 16 x H x W
            nn.MaxPool2d(2, stride=2),
            ConvBlock(16, 32, kernel_size=3, padding=1),  # -> 32 x H/2 x H/2
            nn.MaxPool2d(2, stride=2),
            ConvBlock(32, 64, kernel_size=3, padding=1),  # -> 64 x H/4 x H/4
            nn.MaxPool2d(2, stride=2),
            ConvBlock(64, 128, kernel_size=3, padding=1),  # -> 128 x H/8 x H/8
            nn.MaxPool2d(2, stride=2),
            ConvBlock(128, 256, kernel_size=3, padding=1),  # -> 256 x H/16 x H/16
            nn.MaxPool2d(2, stride=2),
            ConvBlock(256, 512, kernel_size=3, padding=1),  # -> 512 x H/32 x H/32
            nn.MaxPool2d(2, stride=2),
            ConvBlock(512, 1024, kernel_size=3, padding=1),  # -> 1024 x H/64 x H/64
        )

        # Global average pooling to handle different input sizes
        self.pool = nn.AdaptiveAvgPool2d((grid_size, grid_size))

        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(1024 * grid_size * grid_size, 256),
            nn.LeakyReLU(0.1, inplace=True),
            nn.Dropout(0.5),
            nn.Linear(256, grid_size * grid_size * self.output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor of shape (batch, 3, H, W)

        Returns:
            Predictions of shape (batch, S*S*(B*5+C))
        """
        x = self.features(x)
        x = self.pool(x)
        x = self.head(x)
        return x

    def predict(
        self, x: torch.Tensor, confidence_threshold: float = 0.1
    ) -> List[dict]:
        """
        Run inference and return decoded predictions.
        """
        from .utils import decode_predictions

        raw = self.forward(x)
        batch_size = raw.shape[0]
        predictions = raw.view(
            batch_size, self.grid_size, self.grid_size, self.output_size
        )
        return decode_predictions(
            predictions,
            grid_size=self.grid_size,
            num_boxes=self.num_boxes,
            num_classes=self.num_classes,
            confidence_threshold=confidence_threshold,
        )
