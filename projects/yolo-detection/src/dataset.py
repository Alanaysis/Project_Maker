"""
Dataset handling for YOLO object detection.

Provides:
- Simple synthetic dataset for testing
- VOC-style dataset loader
- Data augmentation utilities
- Custom collate function for DataLoader
"""

import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
from typing import List, Tuple, Optional, Dict, Any


class SimpleDetectionDataset(Dataset):
    """
    Simple synthetic dataset for testing YOLO.

    Generates random images with simple geometric shapes as objects.
    Useful for:
    - Testing the training pipeline
    - Verifying the loss function
    - Quick experiments without real data

    Args:
        num_samples: Number of samples in dataset
        image_size: Image size (assumes square)
        grid_size: YOLO grid size
        num_classes: Number of object classes
        max_objects: Maximum objects per image
        seed: Random seed for reproducibility
    """

    def __init__(
        self,
        num_samples: int = 100,
        image_size: int = 448,
        grid_size: int = 7,
        num_classes: int = 5,
        max_objects: int = 3,
        seed: int = 42,
    ):
        super().__init__()
        self.num_samples = num_samples
        self.image_size = image_size
        self.grid_size = grid_size
        self.num_classes = num_classes
        self.max_objects = max_objects

        # Generate random samples
        np.random.seed(seed)
        self.samples = self._generate_samples()

    def _generate_samples(self) -> List[Dict[str, Any]]:
        """Generate random detection samples."""
        samples = []
        for _ in range(self.num_samples):
            # Random number of objects
            num_objects = np.random.randint(1, self.max_objects + 1)

            boxes = []
            labels = []
            for _ in range(num_objects):
                # Random box: [x_center, y_center, width, height]
                w = np.random.randint(20, 100)
                h = np.random.randint(20, 100)
                x = np.random.randint(w // 2, self.image_size - w // 2)
                y = np.random.randint(h // 2, self.image_size - h // 2)
                boxes.append([x, y, w, h])
                labels.append(np.random.randint(0, self.num_classes))

            # Create simple image with colored rectangles
            image = np.random.randint(0, 50, (3, self.image_size, self.image_size), dtype=np.uint8)
            for box, label in zip(boxes, labels):
                x, y, w, h = box
                x1, y1 = int(x - w / 2), int(y - h / 2)
                x2, y2 = int(x + w / 2), int(y + h / 2)
                # Draw colored rectangle
                color = [(label * 50) % 256, (label * 100 + 50) % 256, (label * 150 + 100) % 256]
                image[0, y1:y2, x1:x2] = color[0]
                image[1, y1:y2, x1:x2] = color[1]
                image[2, y1:y2, x1:x2] = color[2]

            samples.append({
                "image": image,
                "boxes": np.array(boxes, dtype=np.float32),
                "labels": np.array(labels, dtype=np.int64),
            })

        return samples

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        sample = self.samples[idx]

        # Normalize image to [0, 1]
        image = torch.from_numpy(sample["image"]).float() / 255.0
        boxes = torch.from_numpy(sample["boxes"])
        labels = torch.from_numpy(sample["labels"])

        # Create target tensor
        target = self._create_target(boxes, labels)

        return image, {
            "target": target,
            "boxes": boxes,
            "labels": labels,
        }

    def _create_target(
        self, boxes: torch.Tensor, labels: torch.Tensor
    ) -> torch.Tensor:
        """Create YOLO target tensor from boxes and labels."""
        from .loss import create_target_tensor

        return create_target_tensor(
            boxes=boxes.tolist(),
            labels=labels.tolist(),
            grid_size=self.grid_size,
            num_boxes=2,
            num_classes=self.num_classes,
            image_size=self.image_size,
        )


class MultiScaleDataset(Dataset):
    """
    Dataset that applies multi-scale training.

    Randomly resizes images during training to improve
    detection of objects at different scales.

    Args:
        base_dataset: Base dataset to wrap
        scales: List of image sizes to sample from
    """

    def __init__(self, base_dataset: Dataset, scales: List[int] = None):
        self.base_dataset = base_dataset
        self.scales = scales or [320, 352, 384, 416, 448]

    def __len__(self) -> int:
        return len(self.base_dataset)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        image, target = self.base_dataset[idx]

        # Random scale
        scale = np.random.choice(self.scales)
        if scale != image.shape[-1]:
            image = torch.nn.functional.interpolate(
                image.unsqueeze(0), size=scale, mode="bilinear", align_corners=False
            ).squeeze(0)

        return image, target


def collate_fn(batch: List[Tuple[torch.Tensor, Dict]]) -> Tuple[torch.Tensor, Dict]:
    """
    Custom collate function for DataLoader.

    Handles variable-sized bounding box annotations by padding.

    Args:
        batch: List of (image, target_dict) tuples

    Returns:
        images: Stacked image tensor (batch, C, H, W)
        targets: Dictionary with batched targets
    """
    images = []
    targets_list = []

    for image, target in batch:
        images.append(image)
        targets_list.append(target)

    # Stack images (assumes same size)
    images = torch.stack(images, dim=0)

    # Stack target tensors
    target_tensors = torch.stack([t["target"] for t in targets_list], dim=0)

    # Collect raw boxes and labels (variable length, keep as lists)
    boxes_list = [t["boxes"] for t in targets_list]
    labels_list = [t["labels"] for t in targets_list]

    return images, {
        "target": target_tensors,
        "boxes": boxes_list,
        "labels": labels_list,
    }


def create_dataloader(
    dataset: Dataset,
    batch_size: int = 8,
    shuffle: bool = True,
    num_workers: int = 0,
) -> DataLoader:
    """
    Create a DataLoader with the custom collate function.

    Args:
        dataset: PyTorch Dataset
        batch_size: Batch size
        shuffle: Whether to shuffle
        num_workers: Number of data loading workers

    Returns:
        DataLoader instance
    """
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        collate_fn=collate_fn,
        pin_memory=True,
    )
