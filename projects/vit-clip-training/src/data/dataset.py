"""
Dataset and DataLoader for CLIP Training

⭐ Data Format:
- Image-text pairs
- Images: PIL Images or file paths
- Texts: Raw text strings

💡 Data Sources:
- COCO Captions: 330K images, 5 captions each
- CC3M: 3.3M image-text pairs
- LAION-400M: 400M image-text pairs (web-scraped)

🎯 Data Augmentation:
- Random resized crop
- Horizontal flip
- Color jitter
- Normalization (ImageNet stats)
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union

import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image

# Simple tokenizer for demonstration
# In production, use CLIP's BPE tokenizer


class SimpleTokenizer:
    """
    Simple character-level tokenizer for demonstration.

    ⭐ In production, use CLIP's BPE tokenizer:
    - Handles subword tokenization
    - Supports 49,408 tokens
    - Better handling of rare words

    💡 Why BPE?
    - Balances vocabulary size and sequence length
    - Handles out-of-vocabulary words
    - More efficient than character-level
    """

    def __init__(self, vocab_size: int = 49408, max_length: int = 77):
        self.vocab_size = vocab_size
        self.max_length = max_length
        # Simple character mapping for demo
        self.char_to_idx = {chr(i): i for i in range(128)}
        self.idx_to_char = {i: chr(i) for i in range(128)}
        # Special tokens
        self.pad_token = 0
        self.sos_token = 1  # Start of sequence
        self.eos_token = 2  # End of sequence

    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs."""
        tokens = [self.sos_token]
        for char in text[:self.max_length - 2]:  # Leave room for SOS and EOS
            if char in self.char_to_idx:
                tokens.append(self.char_to_idx[char])
            else:
                tokens.append(3  # Unknown token
                )
        tokens.append(self.eos_token)

        # Pad to max_length
        while len(tokens) < self.max_length:
            tokens.append(self.pad_token)

        return tokens

    def decode(self, tokens: List[int]) -> str:
        """Decode token IDs to text."""
        chars = []
        for t in tokens:
            if t in [self.pad_token, self.sos_token, self.eos_token]:
                continue
            if t in self.idx_to_char:
                chars.append(self.idx_to_char[t])
        return "".join(chars)

    def __call__(self, text: str) -> torch.Tensor:
        """Tokenize and return tensor."""
        return torch.tensor(self.encode(text), dtype=torch.long)


class ImageTextDataset(Dataset):
    """
    Dataset for image-text pairs.

    ⭐ Supports multiple data formats:
    1. Directory with images and JSON captions file
    2. List of (image_path, text) tuples
    3. Custom data loading functions

    💡 Data loading strategies:
    - Lazy loading: Load images on-the-fly (memory efficient)
    - Eager loading: Pre-load all images (faster training)
    - Cached loading: Load once, cache in memory

    Example:
        >>> dataset = ImageTextDataset(
        ...     image_dir="data/images",
        ...     captions_file="data/captions.json",
        ... )
        >>> image, text = dataset[0]
    """

    def __init__(
        self,
        image_dir: Optional[str] = None,
        captions_file: Optional[str] = None,
        data_pairs: Optional[List[Tuple[str, str]]] = None,
        tokenizer: Optional[SimpleTokenizer] = None,
        image_transform: Optional[transforms.Compose] = None,
        max_length: int = 77,
        image_size: int = 224,
    ):
        """
        Args:
            image_dir: Directory containing images
            captions_file: JSON file with captions (format: {image_name: caption})
            data_pairs: List of (image_path, text) tuples
            tokenizer: Text tokenizer
            image_transform: Image transformations
            max_length: Maximum text sequence length
            image_size: Image size for resizing
        """
        self.image_dir = image_dir
        self.tokenizer = tokenizer or SimpleTokenizer(max_length=max_length)
        self.max_length = max_length

        # Default image transforms
        if image_transform is None:
            self.image_transform = transforms.Compose([
                transforms.Resize((image_size, image_size)),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],  # ImageNet stats
                    std=[0.229, 0.224, 0.225],
                ),
            ])
        else:
            self.image_transform = image_transform

        # Load data pairs
        if data_pairs is not None:
            self.data_pairs = data_pairs
        elif image_dir and captions_file:
            self.data_pairs = self._load_from_files(image_dir, captions_file)
        else:
            raise ValueError("Either data_pairs or (image_dir, captions_file) required")

    def _load_from_files(
        self,
        image_dir: str,
        captions_file: str,
    ) -> List[Tuple[str, str]]:
        """Load data pairs from image directory and captions file."""
        data_pairs = []

        # Load captions
        with open(captions_file, "r") as f:
            captions = json.load(f)

        # Create pairs
        for image_name, caption in captions.items():
            image_path = os.path.join(image_dir, image_name)
            if os.path.exists(image_path):
                data_pairs.append((image_path, caption))

        return data_pairs

    def __len__(self) -> int:
        return len(self.data_pairs)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Get a single item.

        Returns:
            Tuple of (image_tensor, text_tokens)
        """
        image_path, text = self.data_pairs[idx]

        # Load and transform image
        try:
            image = Image.open(image_path).convert("RGB")
            image = self.image_transform(image)
        except Exception as e:
            # Return a blank image if loading fails
            print(f"Warning: Failed to load image {image_path}: {e}")
            image = torch.zeros(3, 224, 224)

        # Tokenize text
        text_tokens = self.tokenizer(text)

        return image, text_tokens


class SyntheticDataset(Dataset):
    """
    Synthetic dataset for testing and development.

    Generates random image-text pairs.

    💡 Use cases:
    - Testing data pipeline
    - Debugging model architecture
    - Quick experiments without real data

    Example:
        >>> dataset = SyntheticDataset(num_samples=100)
        >>> image, text = dataset[0]
    """

    def __init__(
        self,
        num_samples: int = 1000,
        image_size: int = 224,
        vocab_size: int = 49408,
        seq_len: int = 77,
    ):
        self.num_samples = num_samples
        self.image_size = image_size
        self.vocab_size = vocab_size
        self.seq_len = seq_len

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Generate random image and text pair."""
        # Random image
        image = torch.randn(3, self.image_size, self.image_size)

        # Random text tokens
        text = torch.randint(0, self.vocab_size, (self.seq_len,))

        return image, text


def create_dataloader(
    dataset: Dataset,
    batch_size: int = 32,
    shuffle: bool = True,
    num_workers: int = 4,
    pin_memory: bool = True,
) -> DataLoader:
    """
    Create a DataLoader with appropriate settings.

    Args:
        dataset: Dataset instance
        batch_size: Batch size
        shuffle: Whether to shuffle
        num_workers: Number of data loading workers
        pin_memory: Whether to pin memory for GPU transfer

    Returns:
        DataLoader instance
    """
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=True,  # Drop last incomplete batch for consistent batch size
    )


def create_synthetic_dataloader(
    num_samples: int = 1000,
    batch_size: int = 32,
    image_size: int = 224,
) -> DataLoader:
    """
    Create a DataLoader with synthetic data.

    💡 Useful for quick testing without real data.

    Args:
        num_samples: Number of synthetic samples
        batch_size: Batch size
        image_size: Image size

    Returns:
        DataLoader instance
    """
    dataset = SyntheticDataset(
        num_samples=num_samples,
        image_size=image_size,
    )
    return create_dataloader(dataset, batch_size=batch_size, num_workers=0)
