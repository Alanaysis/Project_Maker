"""
Feature Neck for Text Detection

Implements U-Net style feature merging for multi-scale feature fusion.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class ConvBlock(nn.Module):
    """Conv + BN + ReLU block."""

    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.conv = nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False)
        self.bn = nn.BatchNorm2d(out_ch)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.relu(self.bn(self.conv(x)))


class UNetNeck(nn.Module):
    """
    U-Net style feature merging neck.

    Progressively merges multi-scale features from backbone
    using upsampling and lateral connections.

    Args:
        in_channels_list: List of channels for each feature level
        out_channels: Output channels after merging
    """

    def __init__(self, in_channels_list: list, out_channels: int = 32):
        super().__init__()

        # Lateral connections to reduce channels
        self.lateral_convs = nn.ModuleList()
        for ch in in_channels_list:
            self.lateral_convs.append(
                nn.Conv2d(ch, out_channels, 1, bias=False)
            )

        # Smooth layers after merging
        self.smooth_convs = nn.ModuleList()
        for _ in range(len(in_channels_list) - 1):
            self.smooth_convs.append(
                ConvBlock(out_channels, out_channels)
            )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, features: list) -> torch.Tensor:
        """
        Forward pass.

        Args:
            features: List of feature maps from backbone [f1, f2, ..., fN]
                      f1 has highest resolution, fN has lowest

        Returns:
            Merged feature map at highest resolution
        """
        # Apply lateral connections
        laterals = [conv(f) for conv, f in zip(self.lateral_convs, features)]

        # Top-down merging
        for i in range(len(laterals) - 1, 0, -1):
            # Upsample and add
            upsampled = F.interpolate(
                laterals[i],
                size=laterals[i-1].shape[2:],
                mode='bilinear',
                align_corners=False
            )
            laterals[i-1] = laterals[i-1] + upsampled

        # Apply smooth convs (from low to high resolution)
        result = laterals[-1]
        for i in range(len(self.smooth_convs) - 1, -1, -1):
            result = F.interpolate(
                result,
                size=laterals[i].shape[2:],
                mode='bilinear',
                align_corners=False
            )
            result = self.smooth_convs[i](result + laterals[i])

        return result


class FPNNeck(nn.Module):
    """
    Feature Pyramid Network neck.

    Similar to UNetNeck but with additional top-down pathway
    and lateral connections at each level.

    Args:
        in_channels_list: List of channels for each feature level
        out_channels: Output channels after merging
    """

    def __init__(self, in_channels_list: list, out_channels: int = 32):
        super().__init__()

        # Lateral connections
        self.lateral_convs = nn.ModuleList()
        for ch in in_channels_list:
            self.lateral_convs.append(
                nn.Conv2d(ch, out_channels, 1, bias=False)
            )

        # Output convs
        self.output_convs = nn.ModuleList()
        for _ in in_channels_list:
            self.output_convs.append(
                ConvBlock(out_channels, out_channels)
            )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, features: list) -> torch.Tensor:
        """
        Forward pass.

        Args:
            features: List of feature maps from backbone

        Returns:
            Merged feature map at highest resolution
        """
        # Apply lateral connections
        laterals = [conv(f) for conv, f in zip(self.lateral_convs, features)]

        # Top-down pathway
        for i in range(len(laterals) - 1, 0, -1):
            upsampled = F.interpolate(
                laterals[i],
                size=laterals[i-1].shape[2:],
                mode='bilinear',
                align_corners=False
            )
            laterals[i-1] = laterals[i-1] + upsampled

        # Apply output convs and upsample all to highest resolution
        target_size = laterals[0].shape[2:]
        outputs = []

        for i, (lateral, conv) in enumerate(zip(laterals, self.output_convs)):
            out = conv(lateral)
            if i > 0:
                out = F.interpolate(
                    out,
                    size=target_size,
                    mode='bilinear',
                    align_corners=False
                )
            outputs.append(out)

        # Sum all outputs
        return sum(outputs)
