"""DnCNN (Deep Convolutional Neural Network for Image Denoising)

Reference: Beyond a Gaussian Denoiser: Residual Learning of Deep CNN for Image Denoising (Zhang et al., 2017)

Architecture:
    Input -> [Conv + ReLU] -> [Conv + BN + ReLU] x (depth-2) -> [Conv] -> Output

    The model predicts the residual (noise), so:
    denoised_image = noisy_image - predicted_noise
"""

from typing import Optional
import torch
import torch.nn as nn


class DnCNN(nn.Module):
    """DnCNN model for image denoising.

    The model learns to predict the noise in the image using residual learning.
    Architecture:
        1. First layer: Conv2d + ReLU (feature extraction)
        2. Middle layers: Conv2d + BatchNorm2d + ReLU (depth-2 blocks)
        3. Last layer: Conv2d (noise prediction)

    Args:
        in_channels: Number of input channels (1 for grayscale, 3 for RGB)
        out_channels: Number of output channels (same as in_channels)
        num_features: Number of feature maps in hidden layers
        depth: Total number of convolutional layers (default: 17)
        use_bn: Whether to use batch normalization (default: True)
    """

    def __init__(
        self,
        in_channels: int = 1,
        out_channels: Optional[int] = None,
        num_features: int = 64,
        depth: int = 17,
        use_bn: bool = True,
    ):
        super().__init__()

        # Default out_channels to in_channels if not specified
        if out_channels is None:
            out_channels = in_channels

        self.depth = depth
        self.in_channels = in_channels
        self.out_channels = out_channels

        # First layer: Conv + ReLU
        layers = [
            nn.Conv2d(in_channels, num_features, kernel_size=3, padding=1, bias=True),
            nn.ReLU(inplace=True),
        ]

        # Middle layers: Conv + BN + ReLU
        for _ in range(depth - 2):
            layers.append(
                nn.Conv2d(num_features, num_features, kernel_size=3, padding=1, bias=not use_bn)
            )
            if use_bn:
                layers.append(nn.BatchNorm2d(num_features))
            layers.append(nn.ReLU(inplace=True))

        # Last layer: Conv (no activation)
        layers.append(
            nn.Conv2d(num_features, out_channels, kernel_size=3, padding=1, bias=True)
        )

        self.network = nn.Sequential(*layers)

        # Initialize weights
        self._initialize_weights()

    def _initialize_weights(self):
        """Initialize network weights using Kaiming initialization."""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Noisy input image [B, C, H, W]

        Returns:
            Predicted noise [B, C, H, W]
        """
        return self.network(x)

    def denoise(self, x: torch.Tensor) -> torch.Tensor:
        """Remove noise from image.

        Args:
            x: Noisy input image [B, C, H, W]

        Returns:
            Denoised image [B, C, H, W]
        """
        noise = self.forward(x)
        return x - noise


class DnCNNLight(nn.Module):
    """Lightweight DnCNN variant with fewer parameters.

    Suitable for faster inference and lower resource usage.

    Args:
        in_channels: Number of input channels
        out_channels: Number of output channels
        num_features: Number of feature maps (default: 32)
        depth: Total number of layers (default: 8)
    """

    def __init__(
        self,
        in_channels: int = 1,
        out_channels: Optional[int] = None,
        num_features: int = 32,
        depth: int = 8,
    ):
        super().__init__()

        # Default out_channels to in_channels if not specified
        if out_channels is None:
            out_channels = in_channels

        # First layer
        layers = [
            nn.Conv2d(in_channels, num_features, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
        ]

        # Middle layers (no BN for lightweight version)
        for _ in range(depth - 2):
            layers.extend([
                nn.Conv2d(num_features, num_features, kernel_size=3, padding=1),
                nn.ReLU(inplace=True),
            ])

        # Last layer
        layers.append(
            nn.Conv2d(num_features, out_channels, kernel_size=3, padding=1)
        )

        self.network = nn.Sequential(*layers)
        self._initialize_weights()

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, nonlinearity='relu')
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)

    def denoise(self, x: torch.Tensor) -> torch.Tensor:
        return x - self.forward(x)


def create_model(
    model_type: str = "dncnn",
    in_channels: int = 1,
    depth: int = 17,
    num_features: int = 64,
    pretrained_path: Optional[str] = None,
) -> nn.Module:
    """Factory function to create denoising models.

    Args:
        model_type: Type of model ("dncnn" or "dncnn_light")
        in_channels: Number of input channels
        depth: Network depth
        num_features: Number of features
        pretrained_path: Path to pretrained weights

    Returns:
        Initialized model
    """
    if model_type == "dncnn":
        model = DnCNN(
            in_channels=in_channels,
            out_channels=in_channels,
            num_features=num_features,
            depth=depth,
        )
    elif model_type == "dncnn_light":
        model = DnCNNLight(
            in_channels=in_channels,
            out_channels=in_channels,
            num_features=num_features,
            depth=depth,
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    if pretrained_path is not None:
        state_dict = torch.load(pretrained_path, map_location='cpu')
        model.load_state_dict(state_dict)

    return model


if __name__ == "__main__":
    # Test model creation
    model = DnCNN(in_channels=1, depth=17)
    x = torch.randn(1, 1, 64, 64)

    print("DnCNN Model Summary:")
    print(f"  Input shape: {x.shape}")

    noise_pred = model(x)
    print(f"  Noise prediction shape: {noise_pred.shape}")

    denoised = model.denoise(x)
    print(f"  Denoised image shape: {denoised.shape}")

    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Total parameters: {total_params:,}")
    print(f"  Trainable parameters: {trainable_params:,}")
