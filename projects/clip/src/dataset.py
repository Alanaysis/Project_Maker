"""Dataset utilities for CLIP training."""

import torch
from torch.utils.data import Dataset, DataLoader
from typing import Optional, List, Dict, Tuple
import json
from pathlib import Path


class ImageTextDataset(Dataset):
    """
    Dataset for image-text pairs.
    """

    def __init__(
        self,
        data_path: str,
        tokenizer=None,
        image_transform=None,
        max_text_length: int = 77,
    ):
        """
        Initialize dataset.

        Args:
            data_path: Path to data directory or JSON file
            tokenizer: Text tokenizer
            image_transform: Image transformation
            max_text_length: Maximum text length
        """
        self.tokenizer = tokenizer
        self.image_transform = image_transform
        self.max_text_length = max_text_length

        # Load data
        self.data = self._load_data(data_path)

    def _load_data(self, data_path: str) -> List[Dict]:
        """Load data from path."""
        path = Path(data_path)

        if path.is_file() and path.suffix == ".json":
            with open(path, "r") as f:
                return json.load(f)
        elif path.is_dir():
            # Load from directory structure
            data = []
            for img_path in path.glob("*.jpg"):
                # Look for corresponding text file
                txt_path = img_path.with_suffix(".txt")
                if txt_path.exists():
                    with open(txt_path, "r") as f:
                        text = f.read().strip()
                    data.append({
                        "image_path": str(img_path),
                        "text": text,
                    })
            return data
        else:
            raise ValueError(f"Invalid data path: {data_path}")

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Get item by index.

        Returns:
            Dictionary with 'images', 'input_ids', 'attention_mask'
        """
        item = self.data[idx]

        # Load and transform image
        # In real implementation, would load image from path
        # For now, create a dummy image
        if self.image_transform:
            image = self.image_transform(item.get("image_path"))
        else:
            # Dummy image for testing
            image = torch.randn(3, 224, 224)

        # Tokenize text
        if self.tokenizer:
            text_inputs = self.tokenizer(
                item["text"],
                padding="max_length",
                truncation=True,
                max_length=self.max_text_length,
                return_tensors="pt",
            )
            input_ids = text_inputs["input_ids"].squeeze(0)
            attention_mask = text_inputs["attention_mask"].squeeze(0)
        else:
            # Dummy tokenization for testing
            input_ids = torch.randint(0, 10000, (self.max_text_length,))
            attention_mask = torch.ones(self.max_text_length)

        return {
            "images": image,
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }


class SyntheticDataset(Dataset):
    """
    Synthetic dataset for testing and demonstration.
    """

    def __init__(
        self,
        num_samples: int = 1000,
        image_size: int = 224,
        vocab_size: int = 10000,
        max_seq_length: int = 77,
    ):
        self.num_samples = num_samples
        self.image_size = image_size
        self.vocab_size = vocab_size
        self.max_seq_length = max_seq_length

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        return {
            "images": torch.randn(3, self.image_size, self.image_size),
            "input_ids": torch.randint(1, self.vocab_size, (self.max_seq_length,)),
            "attention_mask": torch.ones(self.max_seq_length),
        }


def create_dataloader(
    dataset: Dataset,
    batch_size: int = 32,
    shuffle: bool = True,
    num_workers: int = 4,
) -> DataLoader:
    """
    Create a DataLoader.

    Args:
        dataset: Dataset instance
        batch_size: Batch size
        shuffle: Whether to shuffle
        num_workers: Number of workers

    Returns:
        DataLoader instance
    """
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=True,
    )
