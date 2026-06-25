"""
Detection Head for EAST Text Detection

Produces score map and geometry map from merged features.
"""

import torch
import torch.nn as nn


class EASTHead(nn.Module):
    """
    EAST detection head.

    Outputs:
        - Score map: [B, 1, H, W] - text probability
        - Geometry map (RBOX): [B, 5, H, W] - distances to top/right/bottom/left + angle
        - Geometry map (QUAD): [B, 8, H, W] - 4 corner offsets (dx, dy)

    Args:
        in_channels: Input feature channels
        geo_type: 'rbox' or 'quad'
    """

    def __init__(self, in_channels: int = 32, geo_type: str = 'rbox'):
        super().__init__()
        self.geo_type = geo_type

        # Shared layers
        self.shared = nn.Sequential(
            nn.Conv2d(in_channels, 64, 3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
        )

        # Score branch: text/non-text classification
        self.score_branch = nn.Sequential(
            nn.Conv2d(64, 32, 3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 1, 1),
            nn.Sigmoid(),
        )

        # Geometry branch
        if geo_type == 'rbox':
            geo_out = 5  # top, right, bottom, left, angle
        else:
            geo_out = 8  # 4 corners * 2 coordinates

        self.geo_branch = nn.Sequential(
            nn.Conv2d(64, 32, 3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, geo_out, 1),
            nn.Sigmoid(),  # Output in [0, 1], will be scaled later
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x: torch.Tensor):
        """
        Args:
            x: Merged features [B, C, H, W]

        Returns:
            score_map: [B, 1, H, W]
            geo_map: [B, 5 or 8, H, W]
        """
        shared_feat = self.shared(x)
        score = self.score_branch(shared_feat)
        geo = self.geo_branch(shared_feat)
        return score, geo


class DBHead(nn.Module):
    """
    DBNet-style detection head with Differentiable Binarization.

    Args:
        in_channels: Input feature channels
        k: Binarization sharpness parameter
    """

    def __init__(self, in_channels: int = 32, k: int = 50):
        super().__init__()
        self.k = k

        # Probability map
        self.prob_head = nn.Sequential(
            nn.Conv2d(in_channels, 64, 3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(64, 32, 2, stride=2),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(32, 1, 2, stride=2),
            nn.Sigmoid(),
        )

        # Threshold map
        self.thresh_head = nn.Sequential(
            nn.Conv2d(in_channels, 64, 3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(64, 32, 2, stride=2),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(32, 1, 2, stride=2),
            nn.Sigmoid(),
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, (nn.Conv2d, nn.ConvTranspose2d)):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def differentiable_binarize(self, prob: torch.Tensor, thresh: torch.Tensor) -> torch.Tensor:
        """
        Differentiable binarization: approximates step function.

        B = 1 / (1 + exp(-k * (P - T)))

        Args:
            prob: Probability map [B, 1, H, W]
            thresh: Threshold map [B, 1, H, W]

        Returns:
            Binary approximation map [B, 1, H, W]
        """
        return 1.0 / (1.0 + torch.exp(-self.k * (prob - thresh)))

    def forward(self, x: torch.Tensor):
        """
        Args:
            x: Merged features [B, C, H, W]

        Returns:
            prob_map: [B, 1, H/4, W/4] probability map
            thresh_map: [B, 1, H/4, W/4] threshold map
            binary_map: [B, 1, H/4, W/4] binarized map
        """
        prob = self.prob_head(x)
        thresh = self.thresh_head(x)
        binary = self.differentiable_binarize(prob, thresh)
        return prob, thresh, binary
