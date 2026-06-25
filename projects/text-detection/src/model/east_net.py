"""
EAST Network - Complete Text Detection Model

Combines backbone, neck, and head into a unified text detection network.
"""

import torch
import torch.nn as nn
from typing import Dict, Tuple

from .backbone import VGGBackbone, LightBackbone
from .neck import UNetNeck, FPNNeck
from .head import EASTHead


class EASTNet(nn.Module):
    """
    EAST: Efficient and Accurate Scene Text Detector

    Architecture:
    1. Backbone: VGG-like feature extractor
    2. Neck: U-Net feature merging
    3. Head: Score + Geometry prediction

    Args:
        backbone_type: 'vgg' or 'light'
        neck_type: 'unet' or 'fpn'
        geo_type: 'rbox' or 'quad'
        in_channels: Input image channels
    """

    def __init__(self, backbone_type: str = 'vgg', neck_type: str = 'unet',
                 geo_type: str = 'rbox', in_channels: int = 3):
        super().__init__()

        # Backbone
        if backbone_type == 'vgg':
            self.backbone = VGGBackbone(in_channels)
            backbone_channels = [64, 128, 256, 512, 512]
        elif backbone_type == 'light':
            self.backbone = LightBackbone(in_channels)
            backbone_channels = [32, 64, 128, 256, 256]
        else:
            raise ValueError(f"Unknown backbone: {backbone_type}")

        # Neck
        neck_out = 32
        if neck_type == 'unet':
            self.neck = UNetNeck(backbone_channels, neck_out)
        elif neck_type == 'fpn':
            self.neck = FPNNeck(backbone_channels, neck_out)
        else:
            raise ValueError(f"Unknown neck: {neck_type}")

        # Head
        self.head = EASTHead(neck_out, geo_type)

        self.geo_type = geo_type

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass.

        Args:
            x: Input image [B, C, H, W]

        Returns:
            Dictionary with:
                - 'score': Score map [B, 1, H/4, W/4]
                - 'geo': Geometry map [B, 5 or 8, H/4, W/4]
                - 'features': Backbone feature maps
        """
        # Extract features
        features = self.backbone(x)

        # Merge features
        merged = self.neck(features)

        # Predict
        score, geo = self.head(merged)

        return {
            'score': score,
            'geo': geo,
            'features': features,
        }

    def predict(self, x: torch.Tensor, score_thresh: float = 0.5):
        """
        Predict text regions.

        Args:
            x: Input image [B, C, H, W]
            score_thresh: Score threshold

        Returns:
            List of predictions per image
        """
        self.eval()
        with torch.no_grad():
            output = self.forward(x)

        predictions = []
        for i in range(x.shape[0]):
            score_map = output['score'][i, 0].cpu().numpy()
            geo_map = output['geo'][i].cpu().numpy()

            predictions.append({
                'score_map': score_map,
                'geo_map': geo_map,
            })

        return predictions


class TextDetector:
    """
    High-level text detection API.

    Combines model inference with post-processing.
    """

    def __init__(self, model: EASTNet, score_thresh: float = 0.5,
                 nms_thresh: float = 0.4, use_lanms: bool = True):
        """
        Args:
            model: EAST network
            score_thresh: Score threshold for text detection
            nms_thresh: NMS IoU threshold
            use_lanms: Use Locality-Aware NMS
        """
        self.model = model
        self.score_thresh = score_thresh
        self.nms_thresh = nms_thresh
        self.use_lanms = use_lanms

    def detect(self, images: torch.Tensor) -> list:
        """
        Detect text in images.

        Args:
            images: [B, C, H, W] normalized images

        Returns:
            List of detection results per image
        """
        from ..postprocess.nms import decode_rbox, nms, lanms

        self.model.eval()
        with torch.no_grad():
            output = self.model(images)

        results = []
        for i in range(images.shape[0]):
            score_map = output['score'][i, 0].cpu().numpy()
            geo_map = output['geo'][i].cpu().numpy()

            # Decode boxes
            boxes, scores = decode_rbox(score_map, geo_map,
                                         self.score_thresh, scale=4.0)

            if len(boxes) > 0:
                # Apply NMS
                if self.use_lanms:
                    boxes, scores = lanms(boxes, scores, self.nms_thresh)
                    if isinstance(boxes, list):
                        boxes = np.array(boxes)
                        scores = np.array(scores)
                else:
                    keep = nms(boxes, scores, self.nms_thresh)
                    boxes = boxes[keep]
                    scores = scores[keep]

            results.append({
                'boxes': boxes,
                'scores': scores,
                'score_map': score_map,
            })

        return results


def build_east_model(config: dict) -> EASTNet:
    """
    Build EAST model from config.

    Args:
        config: Model configuration dictionary

    Returns:
        EAST network
    """
    return EASTNet(
        backbone_type=config.get('backbone', 'vgg'),
        neck_type=config.get('neck', 'unet'),
        geo_type=config.get('geo_type', 'rbox'),
        in_channels=config.get('in_channels', 3),
    )


# Import numpy for TextDetector
import numpy as np
