"""
Dataset for Text Detection

Provides synthetic data generation and dataset class for training.
"""

import torch
from torch.utils.data import Dataset
import numpy as np
from typing import Tuple, Optional


class TextDetectionDataset(Dataset):
    """
    Dataset for text detection with synthetic data generation.

    Generates images with text-like rectangles for training.
    """

    def __init__(self, num_samples: int = 1000, img_size: int = 512,
                 max_texts: int = 10, transform=None):
        """
        Args:
            num_samples: Number of synthetic samples
            img_size: Image size (square)
            max_texts: Maximum number of text regions per image
            transform: Optional transform
        """
        self.num_samples = num_samples
        self.img_size = img_size
        self.max_texts = max_texts
        self.transform = transform

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Returns:
            image: [3, H, W] normalized image
            score_map: [1, H/4, W/4] text probability map
            geo_map: [5, H/4, W/4] geometry map (top, right, bottom, left, angle)
            mask: [1, H/4, W/4] valid region mask
        """
        np.random.seed(idx)

        # Generate random background
        img = np.random.randint(200, 255, (self.img_size, self.img_size, 3), dtype=np.uint8)

        # Feature map size
        feat_size = self.img_size // 4
        score_map = np.zeros((feat_size, feat_size), dtype=np.float32)
        geo_map = np.zeros((5, feat_size, feat_size), dtype=np.float32)
        mask = np.ones((feat_size, feat_size), dtype=np.float32)

        # Generate random text regions
        num_texts = np.random.randint(1, self.max_texts + 1)

        for _ in range(num_texts):
            # Random text box (ensure it fits in image)
            max_w = min(150, self.img_size - 10)
            max_h = min(40, self.img_size - 10)
            w = np.random.randint(20, max_w)
            h = np.random.randint(10, max_h)
            x = np.random.randint(0, max(1, self.img_size - w))
            y = np.random.randint(0, max(1, self.img_size - h))
            angle = np.random.uniform(-0.2, 0.2)  # Small rotation

            # Draw text region on image
            color = np.random.randint(0, 100, 3).tolist()
            img[y:y+h, x:x+w] = color

            # Update score map (downscaled by 4)
            fx1, fy1 = x // 4, y // 4
            fx2, fy2 = (x + w) // 4, (y + h) // 4

            # Shrink text region slightly for training
            shrink = 2
            sx1, sy1 = fx1 + shrink, fy1 + shrink
            sx2, sy2 = fx2 - shrink, fy2 - shrink

            if sx1 < sx2 and sy1 < sy2:
                score_map[sy1:sy2, sx1:sx2] = 1.0

                # Update geometry map
                for py in range(fy1, min(fy2, feat_size)):
                    for px in range(fx1, min(fx2, feat_size)):
                        geo_map[0, py, px] = (py - fy1) * 4  # top
                        geo_map[1, py, px] = (fx2 - px) * 4  # right
                        geo_map[2, py, px] = (fy2 - py) * 4  # bottom
                        geo_map[3, py, px] = (px - fx1) * 4  # left
                        geo_map[4, py, px] = angle            # angle

        # Normalize image
        img = img.astype(np.float32) / 255.0
        img = (img - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
        img = torch.from_numpy(img.transpose(2, 0, 1))

        score_map = torch.from_numpy(score_map).unsqueeze(0)
        geo_map = torch.from_numpy(geo_map)
        mask = torch.from_numpy(mask).unsqueeze(0)

        return img, score_map, geo_map, mask


class SyntheticTextGenerator:
    """
    Generate synthetic text detection data for testing.
    """

    def __init__(self, img_size: int = 512):
        self.img_size = img_size

    def generate_sample(self, num_texts: int = 5) -> Tuple[np.ndarray, list]:
        """
        Generate a synthetic image with text regions.

        Args:
            num_texts: Number of text regions to generate

        Returns:
            image: [H, W, 3] RGB image
            boxes: List of [x1, y1, x2, y2] text boxes
        """
        # White background
        img = np.ones((self.img_size, self.img_size, 3), dtype=np.uint8) * 255
        boxes = []

        for _ in range(num_texts):
            w = np.random.randint(40, 200)
            h = np.random.randint(15, 50)
            x = np.random.randint(0, self.img_size - w)
            y = np.random.randint(0, self.img_size - h)

            # Draw text-like pattern
            color = np.random.randint(0, 80, 3).tolist()
            img[y:y+h, x:x+w] = color

            # Add some noise
            noise = np.random.randint(-20, 20, (h, w, 3), dtype=np.int16)
            img[y:y+h, x:x+w] = np.clip(
                img[y:y+h, x:x+w].astype(np.int16) + noise, 0, 255
            ).astype(np.uint8)

            boxes.append([x, y, x + w, y + h])

        return img, boxes

    def generate_batch(self, batch_size: int, num_texts: int = 5) -> Tuple[np.ndarray, list]:
        """
        Generate a batch of synthetic images.

        Args:
            batch_size: Number of images
            num_texts: Number of text regions per image

        Returns:
            images: [B, H, W, 3] RGB images
            batch_boxes: List of box lists
        """
        images = []
        batch_boxes = []

        for _ in range(batch_size):
            img, boxes = self.generate_sample(num_texts)
            images.append(img)
            batch_boxes.append(boxes)

        return np.stack(images), batch_boxes
