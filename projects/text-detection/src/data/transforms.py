"""
Data Transforms for Text Detection

Provides augmentation and preprocessing transforms.
"""

import torch
import numpy as np
from typing import Tuple


class TextDetectionTransform:
    """
    Transform pipeline for text detection.

    Handles image normalization and geometry map scaling.
    """

    def __init__(self, img_size: int = 512, mean=None, std=None):
        self.img_size = img_size
        self.mean = mean or [0.485, 0.456, 0.406]
        self.std = std or [0.229, 0.224, 0.225]

    def __call__(self, image: np.ndarray,
                 score_map: np.ndarray = None,
                 geo_map: np.ndarray = None):
        """
        Apply transforms.

        Args:
            image: [H, W, 3] RGB image (uint8)
            score_map: [H/4, W/4] score map (optional)
            geo_map: [5, H/4, W/4] geometry map (optional)

        Returns:
            Transformed tensors
        """
        # Normalize image
        img = image.astype(np.float32) / 255.0
        img = (img - np.array(self.mean)) / np.array(self.std)
        img_tensor = torch.from_numpy(img.transpose(2, 0, 1))

        if score_map is not None and geo_map is not None:
            score_tensor = torch.from_numpy(score_map).unsqueeze(0).float()
            geo_tensor = torch.from_numpy(geo_map).float()
            return img_tensor, score_tensor, geo_tensor

        return img_tensor


class RandomRotate:
    """Random rotation augmentation for text detection."""

    def __init__(self, max_angle: float = 15.0):
        self.max_angle = max_angle

    def __call__(self, image: np.ndarray, boxes: list) -> Tuple[np.ndarray, list]:
        """
        Apply random rotation.

        Args:
            image: [H, W, 3] RGB image
            boxes: List of [x1, y1, x2, y2]

        Returns:
            Rotated image and updated boxes
        """
        import cv2

        angle = np.random.uniform(-self.max_angle, self.max_angle)
        h, w = image.shape[:2]
        center = (w // 2, h // 2)

        # Rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1.0)

        # Rotate image
        rotated = cv2.warpAffine(image, M, (w, h), borderValue=(255, 255, 255))

        # Rotate boxes
        new_boxes = []
        for box in boxes:
            x1, y1, x2, y2 = box
            corners = np.array([
                [x1, y1, 1],
                [x2, y1, 1],
                [x2, y2, 1],
                [x1, y2, 1],
            ])
            rotated_corners = (M @ corners.T).T
            rx1 = rotated_corners[:, 0].min()
            ry1 = rotated_corners[:, 1].min()
            rx2 = rotated_corners[:, 0].max()
            ry2 = rotated_corners[:, 1].max()
            new_boxes.append([rx1, ry1, rx2, ry2])

        return rotated, new_boxes


class RandomCrop:
    """Random crop that preserves text regions."""

    def __init__(self, crop_ratio: float = 0.8):
        self.crop_ratio = crop_ratio

    def __call__(self, image: np.ndarray, boxes: list) -> Tuple[np.ndarray, list]:
        """
        Apply random crop preserving at least one text region.

        Args:
            image: [H, W, 3] RGB image
            boxes: List of [x1, y1, x2, y2]

        Returns:
            Cropped image and updated boxes
        """
        h, w = image.shape[:2]
        ch, cw = int(h * self.crop_ratio), int(w * self.crop_ratio)

        # Random crop position
        y = np.random.randint(0, h - ch + 1)
        x = np.random.randint(0, w - cw + 1)

        # Crop image
        cropped = image[y:y+ch, x:x+cw]

        # Update boxes
        new_boxes = []
        for box in boxes:
            x1, y1, x2, y2 = box
            # Clip to crop region
            nx1 = max(0, x1 - x)
            ny1 = max(0, y1 - y)
            nx2 = min(cw, x2 - x)
            ny2 = min(ch, y2 - y)

            # Only keep if box is still visible
            if nx2 > nx1 and ny2 > ny1:
                new_boxes.append([nx1, ny1, nx2, ny2])

        return cropped, new_boxes


class ColorJitter:
    """Color jitter augmentation."""

    def __init__(self, brightness: float = 0.2, contrast: float = 0.2,
                 saturation: float = 0.2):
        self.brightness = brightness
        self.contrast = contrast
        self.saturation = saturation

    def __call__(self, image: np.ndarray) -> np.ndarray:
        """
        Apply color jitter.

        Args:
            image: [H, W, 3] RGB image (uint8)

        Returns:
            Augmented image
        """
        img = image.astype(np.float32)

        # Brightness
        if np.random.random() < 0.5:
            factor = 1 + np.random.uniform(-self.brightness, self.brightness)
            img = img * factor

        # Contrast
        if np.random.random() < 0.5:
            factor = 1 + np.random.uniform(-self.contrast, self.contrast)
            gray = img.mean(axis=2, keepdims=True)
            img = (img - gray) * factor + gray

        return np.clip(img, 0, 255).astype(np.uint8)
