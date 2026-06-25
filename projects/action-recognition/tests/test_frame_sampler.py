"""Tests for frame sampling strategies."""

import pytest

from action_recognition.data.frame_sampler import FrameSampler


class TestFrameSampler:
    """Test suite for FrameSampler."""

    def test_default_initialization(self):
        sampler = FrameSampler()
        assert sampler.num_frames == 16
        assert sampler.strategy == "uniform"

    def test_invalid_strategy(self):
        with pytest.raises(ValueError, match="Unknown strategy"):
            FrameSampler(strategy="invalid")

    def test_invalid_num_frames(self):
        with pytest.raises(ValueError, match="num_frames must be positive"):
            FrameSampler(num_frames=0)

    def test_uniform_sample_short_video(self):
        sampler = FrameSampler(num_frames=16, strategy="uniform")
        indices = sampler.sample(10)
        assert len(indices) == 10
        assert indices == list(range(10))

    def test_uniform_sample_long_video(self):
        sampler = FrameSampler(num_frames=8, strategy="uniform")
        indices = sampler.sample(100)
        assert len(indices) == 8
        assert all(0 <= i < 100 for i in indices)
        # Should be roughly evenly spaced
        for i in range(len(indices) - 1):
            assert indices[i] < indices[i + 1]

    def test_random_sample_short_video(self):
        sampler = FrameSampler(num_frames=16, strategy="random")
        indices = sampler.sample(10)
        assert len(indices) == 10
        assert indices == list(range(10))

    def test_random_sample_long_video(self):
        sampler = FrameSampler(num_frames=8, strategy="random")
        indices = sampler.sample(100)
        assert len(indices) == 8
        assert all(0 <= i < 100 for i in indices)
        # Should be sorted
        assert indices == sorted(indices)

    def test_dense_sample(self):
        sampler = FrameSampler(num_frames=8, strategy="dense", stride=4)
        indices = sampler.sample(100)
        assert len(indices) == 8
        # Check stride is consistent
        for i in range(len(indices) - 1):
            assert indices[i + 1] - indices[i] == 4

    def test_temporal_jitter_sample(self):
        sampler = FrameSampler(num_frames=8, strategy="temporal_jitter")
        indices = sampler.sample(100)
        assert len(indices) == 8
        assert all(0 <= i < 100 for i in indices)

    def test_zero_frames_error(self):
        sampler = FrameSampler(num_frames=8)
        with pytest.raises(ValueError, match="total_frames must be >= 1"):
            sampler.sample(0)

    def test_repr(self):
        sampler = FrameSampler(num_frames=16, strategy="uniform")
        repr_str = repr(sampler)
        assert "FrameSampler" in repr_str
        assert "16" in repr_str
        assert "uniform" in repr_str
