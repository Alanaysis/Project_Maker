"""
Image Inpainting - Context Encoder based image restoration.

This package implements image inpainting using context encoders (U-Net architecture)
with adversarial training to fill in missing regions of images.

Core modules:
    - context_encoder: U-Net generator and PatchGAN discriminator
    - mask: Mask generation utilities (rectangular, irregular, center)
    - losses: Reconstruction and adversarial loss functions
    - metrics: Image quality metrics (PSNR, SSIM)
    - inpainting: High-level inpainting pipeline
"""

from .context_encoder import UNetGenerator, PatchDiscriminator
from .mask import generate_center_mask, generate_random_rect_mask, generate_irregular_mask, apply_mask
from .losses import ReconstructionLoss, AdversarialLoss, InpaintingLoss
from .metrics import compute_psnr, compute_ssim
from .inpainting import ImageInpainter

__version__ = "0.1.0"
__all__ = [
    "UNetGenerator",
    "PatchDiscriminator",
    "generate_center_mask",
    "generate_random_rect_mask",
    "generate_irregular_mask",
    "apply_mask",
    "ReconstructionLoss",
    "AdversarialLoss",
    "InpaintingLoss",
    "compute_psnr",
    "compute_ssim",
    "ImageInpainter",
]
