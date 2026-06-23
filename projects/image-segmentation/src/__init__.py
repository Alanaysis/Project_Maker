"""
Image Segmentation - A from-scratch implementation of U-Net for semantic segmentation.

This package implements:
- UNet: A U-Net architecture with encoder-decoder and skip connections
- DoubleConv: Double convolution block used throughout the network
- SegmentationDataset: Simple dataset for segmentation tasks
- DiceLoss / BCEDiceLoss: Loss functions for segmentation
"""

from .unet import UNet
from .encoder import Encoder
from .decoder import Decoder
from .blocks import DoubleConv, Down, Up
from .dataset import SegmentationDataset
from .loss import DiceLoss, BCEDiceLoss

__version__ = "0.1.0"
__all__ = [
    "UNet",
    "Encoder",
    "Decoder",
    "DoubleConv",
    "Down",
    "Up",
    "SegmentationDataset",
    "DiceLoss",
    "BCEDiceLoss",
]
