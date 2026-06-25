"""Tests for video dataset."""

import pytest
import torch

from action_recognition.data.video_dataset import VideoDataset
from action_recognition.data.frame_sampler import FrameSampler


class TestVideoDataset:
    """Test suite for VideoDataset."""

    def test_synthetic_dataset(self):
        dataset = VideoDataset(synthetic=True, num_synthetic_classes=5, num_synthetic_samples=50)
        assert len(dataset) == 50
        assert dataset.num_classes == 5

    def test_synthetic_getitem(self):
        dataset = VideoDataset(synthetic=True, num_synthetic_classes=5, num_frames=8)
        video, label = dataset[0]
        assert isinstance(video, torch.Tensor)
        assert video.shape == (8, 3, 224, 224)
        assert isinstance(label, int)
        assert 0 <= label < 5

    def test_synthetic_with_custom_sampler(self):
        sampler = FrameSampler(num_frames=4, strategy="uniform")
        dataset = VideoDataset(synthetic=True, frame_sampler=sampler, num_synthetic_samples=10)
        video, label = dataset[0]
        assert video.shape[0] == 4

    def test_synthetic_class_names(self):
        dataset = VideoDataset(synthetic=True, num_synthetic_classes=3)
        names = dataset.get_class_names()
        assert len(names) == 3
        assert names == ["action_0", "action_1", "action_2"]

    def test_invalid_data_root(self):
        with pytest.raises(ValueError, match="data_root must be a valid directory"):
            VideoDataset(data_root="/nonexistent/path")

    def test_synthetic_deterministic(self):
        dataset = VideoDataset(
            synthetic=True, num_synthetic_classes=2, num_synthetic_samples=5, num_frames=4
        )
        video1, label1 = dataset[0]
        video2, label2 = dataset[0]
        # Synthetic data is random each call, but shape should be consistent
        assert video1.shape == video2.shape
        assert label1 == label2

    def test_synthetic_batch(self):
        from torch.utils.data import DataLoader

        dataset = VideoDataset(synthetic=True, num_synthetic_samples=10, num_frames=4)
        loader = DataLoader(dataset, batch_size=4, shuffle=True)
        batch_videos, batch_labels = next(iter(loader))
        assert batch_videos.shape == (4, 4, 3, 224, 224)
        assert batch_labels.shape == (4,)
