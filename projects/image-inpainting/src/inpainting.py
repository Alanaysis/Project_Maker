"""
High-Level Image Inpainting Pipeline.

This module provides the ImageInpainter class that orchestrates the entire
inpainting workflow:

1. Load/prepare input image
2. Apply mask (corrupt the image)
3. Run the context encoder to generate inpainted content
4. Blend the inpainted region with the original image
5. Evaluate quality metrics

The ImageInpainter supports both:
- Training mode: with discriminator and adversarial losses
- Inference mode: simple forward pass through the generator
"""

import torch
import torch.nn as nn
import torch.optim as optim
from typing import Optional, Tuple, Dict
from .context_encoder import UNetGenerator, PatchDiscriminator, weights_init
from .mask import apply_mask
from .losses import InpaintingLoss
from .metrics import compute_psnr, compute_ssim, compute_l1_error


class ImageInpainter:
    """Image inpainting pipeline using context encoder.

    This class manages the generator (and optional discriminator) for
    image inpainting, providing methods for training and inference.

    Args:
        image_size: Input image size (height, width). Default: (128, 128).
        ngf: Number of generator filters. Default: 64.
        ndf: Number of discriminator filters. Default: 64.
        lambda_rec: Weight for reconstruction loss. Default: 1.0.
        lambda_adv: Weight for adversarial loss. Default: 0.001.
        learning_rate: Learning rate for optimizers. Default: 0.0002.
        beta1: Beta1 parameter for Adam optimizer. Default: 0.5.
        device: Device to use ('cuda' or 'cpu'). Auto-detected if None.
    """

    def __init__(
        self,
        image_size: Tuple[int, int] = (128, 128),
        ngf: int = 64,
        ndf: int = 64,
        lambda_rec: float = 1.0,
        lambda_adv: float = 0.001,
        learning_rate: float = 0.0002,
        beta1: float = 0.5,
        device: Optional[str] = None,
    ):
        self.image_size = image_size
        self.lambda_rec = lambda_rec
        self.lambda_adv = lambda_adv

        # Device selection
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Auto-determine number of downsample blocks based on image size
        # We need spatial size >= 2 at the last encoder before bottleneck
        import math
        min_dim = min(image_size)
        num_downsamples = max(3, int(math.log2(min_dim)) - 1)

        # Initialize networks
        self.generator = UNetGenerator(
            in_channels=4, out_channels=3, ngf=ngf, num_downsamples=num_downsamples
        ).to(self.device)
        self.discriminator = PatchDiscriminator(in_channels=6, ndf=ndf).to(self.device)

        # Apply weight initialization
        self.generator.apply(weights_init)
        self.discriminator.apply(weights_init)

        # Loss function
        self.criterion = InpaintingLoss(
            lambda_rec=lambda_rec,
            lambda_adv=lambda_adv,
            rec_loss_type="l1",
            adv_loss_type="hinge",
        ).to(self.device)

        # Optimizers
        self.optimizer_g = optim.Adam(
            self.generator.parameters(),
            lr=learning_rate,
            betas=(beta1, 0.999),
        )
        self.optimizer_d = optim.Adam(
            self.discriminator.parameters(),
            lr=learning_rate,
            betas=(beta1, 0.999),
        )

    def inpaint(
        self,
        image: torch.Tensor,
        mask: torch.Tensor,
        blend: bool = True,
    ) -> torch.Tensor:
        """Perform inference: inpaint a masked image.

        Args:
            image: Original image tensor (C, H, W) or (B, C, H, W), range [-1, 1].
            mask: Binary mask tensor (1, H, W) or (B, 1, H, W).
                1 = masked (missing) region, 0 = known region.
            blend: If True, blend inpainted output with original image in
                known regions. If False, return raw generator output.

        Returns:
            Inpainted image tensor with the same shape as input.

        Example:
            >>> inpainter = ImageInpainter(image_size=(128, 128))
            >>> image = torch.rand(3, 128, 128) * 2 - 1  # [-1, 1]
            >>> mask = generate_center_mask((128, 128))
            >>> result = inpainter.inpaint(image, mask)
        """
        self.generator.eval()

        # Prepare input
        if image.dim() == 3:
            image = image.unsqueeze(0)
            mask = mask.unsqueeze(0)
            squeeze = True
        else:
            squeeze = False
            # Ensure mask has batch dimension
            if mask.dim() == 3:
                mask = mask.unsqueeze(0).expand(image.size(0), -1, -1, -1)

        image = image.to(self.device)
        mask = mask.to(self.device)

        with torch.no_grad():
            # Create masked input: [masked_image, mask]
            masked_image = image * (1 - mask)
            input_tensor = torch.cat([masked_image, mask], dim=1)

            # Generate inpainted image
            output = self.generator(input_tensor)

            # Blend: use original pixels in known regions
            if blend:
                result = image * (1 - mask) + output * mask
            else:
                result = output

        if squeeze:
            result = result.squeeze(0)

        return result.cpu()

    def train_step(
        self,
        images: torch.Tensor,
        masks: torch.Tensor,
    ) -> Dict[str, float]:
        """Perform a single training step.

        This implements the standard GAN training procedure:
        1. Train discriminator: classify real vs fake
        2. Train generator: fool discriminator + match ground truth

        Args:
            images: Ground truth images (B, C, H, W), range [-1, 1].
            masks: Binary masks (B, 1, H, W).

        Returns:
            Dictionary with loss values for logging:
            - 'd_loss': Discriminator loss
            - 'g_loss': Total generator loss
            - 'rec_loss': Reconstruction loss component
            - 'adv_loss': Adversarial loss component
        """
        images = images.to(self.device)
        masks = masks.to(self.device)
        batch_size = images.size(0)

        # Create masked input
        masked_images = images * (1 - masks)
        input_tensor = torch.cat([masked_images, masks], dim=1)

        # ---- Train Discriminator ----
        self.optimizer_d.zero_grad()

        # Generate fake images
        with torch.no_grad():
            fake_images = self.generator(input_tensor)

        # Discriminator predictions
        # Real: concatenate ground truth with condition
        real_pair = torch.cat([images, masked_images], dim=1)
        # Fake: concatenate inpainted with condition
        fake_pair = torch.cat([fake_images.detach(), masked_images], dim=1)

        real_pred = self.discriminator(real_pair)
        fake_pred = self.discriminator(fake_pair)

        d_loss = self.criterion.discriminator_loss(real_pred, fake_pred)
        d_loss.backward()
        self.optimizer_d.step()

        # ---- Train Generator ----
        self.optimizer_g.zero_grad()

        # Re-generate fake images (need fresh computation graph)
        fake_images = self.generator(input_tensor)

        # Discriminator prediction on fake (for generator loss)
        fake_pair = torch.cat([fake_images, masked_images], dim=1)
        fake_pred = self.discriminator(fake_pair)

        # Combined generator loss
        g_loss, rec_loss, adv_loss = self.criterion.generator_loss(
            fake_images, images, masks, fake_pred
        )
        g_loss.backward()
        self.optimizer_g.step()

        return {
            "d_loss": d_loss.item(),
            "g_loss": g_loss.item(),
            "rec_loss": rec_loss.item(),
            "adv_loss": adv_loss.item(),
        }

    def evaluate(
        self,
        images: torch.Tensor,
        masks: torch.Tensor,
    ) -> Dict[str, float]:
        """Evaluate inpainting quality on a batch of images.

        Args:
            images: Ground truth images (B, C, H, W) or (C, H, W), range [-1, 1].
            masks: Binary masks (B, 1, H, W) or (1, H, 1, W).

        Returns:
            Dictionary with evaluation metrics:
            - 'psnr': Peak Signal-to-Noise Ratio (dB, higher is better)
            - 'ssim': Structural Similarity Index (higher is better)
            - 'l1_error': Mean L1 error (lower is better)
        """
        # Inpaint
        if images.dim() == 3:
            images = images.unsqueeze(0)
            masks = masks.unsqueeze(0)

        results = self.inpaint(images, masks, blend=True)

        # Compute metrics per sample and average
        psnr_vals = []
        ssim_vals = []
        l1_vals = []

        for i in range(images.size(0)):
            # Convert from [-1, 1] to [0, 1] for metric computation
            pred = (results[i] + 1) / 2
            target = (images[i].cpu() + 1) / 2
            mask = masks[i].cpu()

            psnr_vals.append(compute_psnr(pred, target, mask))
            ssim_vals.append(compute_ssim(pred, target, mask))
            l1_vals.append(compute_l1_error(pred, target, mask))

        return {
            "psnr": sum(psnr_vals) / len(psnr_vals),
            "ssim": sum(ssim_vals) / len(ssim_vals),
            "l1_error": sum(l1_vals) / len(l1_vals),
        }

    def save(self, path: str) -> None:
        """Save model checkpoints.

        Args:
            path: File path to save the checkpoint.
        """
        torch.save({
            "generator": self.generator.state_dict(),
            "discriminator": self.discriminator.state_dict(),
            "optimizer_g": self.optimizer_g.state_dict(),
            "optimizer_d": self.optimizer_d.state_dict(),
        }, path)

    def load(self, path: str) -> None:
        """Load model checkpoints.

        Args:
            path: File path to load the checkpoint from.
        """
        checkpoint = torch.load(path, map_location=self.device)
        self.generator.load_state_dict(checkpoint["generator"])
        self.discriminator.load_state_dict(checkpoint["discriminator"])
        self.optimizer_g.load_state_dict(checkpoint["optimizer_g"])
        self.optimizer_d.load_state_dict(checkpoint["optimizer_d"])
