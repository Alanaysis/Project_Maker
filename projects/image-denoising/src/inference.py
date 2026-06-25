"""Inference utilities for image denoising.

Provides:
- Single image denoising
- Batch denoising
- Tiled denoising for large images
- Visualization utilities
"""

from typing import Optional, Tuple, Union
import numpy as np
import torch
import torch.nn as nn
from PIL import Image

from .model import DnCNN, create_model


class Denoiser:
    """Image denoiser using trained DnCNN model.

    Args:
        model_path: Path to trained model checkpoint
        model_type: Type of model ("dncnn" or "dncnn_light")
        device: Device to use for inference
        tile_size: Size of tiles for processing large images (None for no tiling)
        tile_overlap: Overlap between tiles
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        model: Optional[nn.Module] = None,
        model_type: str = "dncnn",
        device: str = "cpu",
        tile_size: Optional[int] = 256,
        tile_overlap: int = 32,
    ):
        self.device = device
        self.tile_size = tile_size
        self.tile_overlap = tile_overlap

        if model is not None:
            self.model = model.to(device)
        elif model_path is not None:
            self.model = self._load_model(model_path, model_type)
        else:
            raise ValueError("Either model or model_path must be provided")

        self.model.eval()

    def _load_model(self, model_path: str, model_type: str) -> nn.Module:
        """Load model from checkpoint.

        Args:
            model_path: Path to checkpoint
            model_type: Type of model

        Returns:
            Loaded model
        """
        checkpoint = torch.load(model_path, map_location=self.device)

        # Determine model parameters from checkpoint
        if 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
        else:
            state_dict = checkpoint

        # Infer model configuration from state dict
        first_conv_weight = None
        for key, value in state_dict.items():
            if 'weight' in key and value.dim() == 4:
                first_conv_weight = value
                break

        if first_conv_weight is not None:
            in_channels = first_conv_weight.shape[1]
            num_features = first_conv_weight.shape[0]
        else:
            in_channels = 1
            num_features = 64

        # Create model
        model = create_model(
            model_type=model_type,
            in_channels=in_channels,
            num_features=num_features,
        )
        model.load_state_dict(state_dict)

        return model.to(self.device)

    def denoise_image(
        self,
        image: Union[np.ndarray, torch.Tensor, Image.Image],
        normalize: bool = True,
    ) -> np.ndarray:
        """Denoise a single image.

        Args:
            image: Input noisy image (H, W), (H, W, C), or (C, H, W)
            normalize: Whether to normalize output to [0, 1]

        Returns:
            Denoised image as numpy array
        """
        # Convert to numpy if needed
        if isinstance(image, Image.Image):
            image = np.array(image, dtype=np.float32) / 255.0

        if isinstance(image, torch.Tensor):
            image = image.numpy()

        # Store original shape and dtype
        original_shape = image.shape
        original_dtype = image.dtype

        # Ensure float32 and [0, 1] range
        if image.dtype == np.uint8:
            image = image.astype(np.float32) / 255.0
        else:
            image = image.astype(np.float32)

        # Handle different input shapes
        if image.ndim == 2:
            # Grayscale [H, W] -> [1, H, W]
            image = image[np.newaxis, :]
            squeeze_batch = True
        elif image.ndim == 3:
            if image.shape[2] in [1, 3, 4]:
                # [H, W, C] -> [C, H, W]
                image = np.transpose(image, (2, 0, 1))
                if image.shape[0] == 4:
                    image = image[:3]  # Remove alpha channel
                squeeze_batch = True
            else:
                # Already [C, H, W]
                squeeze_batch = False
        else:
            raise ValueError(f"Unsupported image shape: {image.shape}")

        # Process image
        if self.tile_size is not None and (image.shape[1] > self.tile_size or image.shape[2] > self.tile_size):
            denoised = self._denoise_tiled(image)
        else:
            denoised = self._denoise_single(image)

        # Normalize if requested
        if normalize:
            denoised = np.clip(denoised, 0.0, 1.0)

        # Restore original shape
        if squeeze_batch:
            if original_shape.ndim == 2 or (original_shape.ndim == 3 and original_shape[2] in [1, 3, 4]):
                denoised = denoised.squeeze()
                if original_shape.ndim == 3:
                    denoised = np.transpose(denoised, (1, 2, 0))

        return denoised

    def _denoise_single(self, image: np.ndarray) -> np.ndarray:
        """Denoise image without tiling.

        Args:
            image: Input image [C, H, W]

        Returns:
            Denoised image [C, H, W]
        """
        # Convert to tensor
        tensor = torch.from_numpy(image).float().unsqueeze(0).to(self.device)

        # Denoise
        with torch.no_grad():
            noise_pred = self.model(tensor)
            denoised = tensor - noise_pred

        # Convert back to numpy
        return denoised.cpu().squeeze().numpy()

    def _denoise_tiled(self, image: np.ndarray) -> np.ndarray:
        """Denoise large image using tiling.

        Args:
            image: Input image [C, H, W]

        Returns:
            Denoised image [C, H, W]
        """
        c, h, w = image.shape
        tile_size = self.tile_size
        overlap = self.tile_overlap

        # Calculate tile positions
        stride = tile_size - overlap
        n_tiles_h = max(1, (h - overlap + stride - 1) // stride)
        n_tiles_w = max(1, (w - overlap + stride - 1) // stride)

        # Initialize output
        output = np.zeros_like(image)
        weight_map = np.zeros((1, h, w), dtype=np.float32)

        for i in range(n_tiles_h):
            for j in range(n_tiles_w):
                # Calculate tile boundaries
                top = min(i * stride, h - tile_size)
                left = min(j * stride, w - tile_size)
                bottom = top + tile_size
                right = left + tile_size

                # Extract tile
                tile = image[:, top:bottom, left:right]

                # Denoise tile
                denoised_tile = self._denoise_single(tile)

                # Create weight map for blending (higher weight in center)
                weight = np.ones((1, tile_size, tile_size), dtype=np.float32)

                # Taper edges
                for k in range(min(overlap // 2, tile_size // 4)):
                    fade = (k + 1) / (overlap // 2 + 1)
                    weight[:, k, :] *= fade
                    weight[:, -(k + 1), :] *= fade
                    weight[:, :, k] *= fade
                    weight[:, :, -(k + 1)] *= fade

                # Accumulate
                output[:, top:bottom, left:right] += denoised_tile * weight
                weight_map[:, top:bottom, left:right] += weight

        # Normalize
        output = output / (weight_map + 1e-8)

        return output

    def denoise_batch(
        self,
        images: list,
        batch_size: int = 8,
    ) -> list:
        """Denoise a batch of images.

        Args:
            images: List of input images
            batch_size: Batch size for processing

        Returns:
            List of denoised images
        """
        results = []

        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]

            # Process batch
            batch_tensors = []
            for img in batch:
                if isinstance(img, np.ndarray):
                    if img.ndim == 2:
                        img = img[np.newaxis, :]
                    elif img.ndim == 3 and img.shape[2] in [1, 3]:
                        img = np.transpose(img, (2, 0, 1))
                    batch_tensors.append(torch.from_numpy(img).float())
                else:
                    batch_tensors.append(img)

            # Stack into batch
            batch_tensor = torch.stack(batch_tensors).to(self.device)

            # Denoise
            with torch.no_grad():
                noise_pred = self.model(batch_tensor)
                denoised = batch_tensor - noise_pred

            # Convert back to list
            for j in range(denoised.shape[0]):
                results.append(denoised[j].cpu().numpy())

        return results


def denoise_image_file(
    input_path: str,
    output_path: str,
    model_path: Optional[str] = None,
    model: Optional[nn.Module] = None,
    device: str = "cpu",
) -> None:
    """Denoise an image file.

    Args:
        input_path: Path to noisy image
        output_path: Path to save denoised image
        model_path: Path to trained model
        model: Pre-loaded model instance
        device: Device to use
    """
    # Load image
    image = Image.open(input_path).convert('L')  # Grayscale
    image_np = np.array(image, dtype=np.float32) / 255.0

    # Create denoiser
    denoiser = Denoiser(
        model_path=model_path,
        model=model,
        device=device,
    )

    # Denoise
    denoised = denoiser.denoise_image(image_np)

    # Save
    denoised_uint8 = (denoised * 255).astype(np.uint8)
    Image.fromarray(denoised_uint8).save(output_path)


def create_denoiser(
    model_path: Optional[str] = None,
    model_type: str = "dncnn",
    device: str = "cpu",
) -> Denoiser:
    """Create a denoiser instance.

    Args:
        model_path: Path to trained model
        model_type: Type of model
        device: Device to use

    Returns:
        Denoiser instance
    """
    return Denoiser(
        model_path=model_path,
        model_type=model_type,
        device=device,
    )


if __name__ == "__main__":
    print("Inference Utilities")
    print("=" * 40)

    # Create a simple model for testing
    from .model import DnCNN
    model = DnCNN(in_channels=1, depth=5, num_features=16)

    # Create denoiser
    denoiser = Denoiser(model=model, device="cpu", tile_size=None)

    # Test with random image
    noisy_image = np.random.rand(64, 64).astype(np.float32)
    print(f"Input shape: {noisy_image.shape}")

    denoised = denoiser.denoise_image(noisy_image)
    print(f"Output shape: {denoised.shape}")
    print(f"Output range: [{denoised.min():.3f}, {denoised.max():.3f}]")

    # Test batch processing
    images = [np.random.rand(32, 32).astype(np.float32) for _ in range(5)]
    denoised_batch = denoiser.denoise_batch(images)
    print(f"\nBatch processing:")
    print(f"  Input: {len(images)} images")
    print(f"  Output: {len(denoised_batch)} images")
