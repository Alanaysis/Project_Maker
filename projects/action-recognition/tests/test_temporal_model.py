"""Tests for temporal modeling module."""

import pytest
import torch

from action_recognition.models.temporal_model import TemporalModel


class TestTemporalModel:
    """Test suite for TemporalModel."""

    def test_lstm_initialization(self):
        model = TemporalModel(input_dim=512, arch="lstm")
        assert model.arch == "lstm"
        assert model.output_dim == 256

    def test_gru_initialization(self):
        model = TemporalModel(input_dim=512, arch="gru")
        assert model.arch == "gru"
        assert model.output_dim == 256

    def test_transformer_initialization(self):
        model = TemporalModel(input_dim=512, arch="transformer")
        assert model.arch == "transformer"
        assert model.output_dim == 512  # transformer output dim = input dim

    def test_invalid_arch(self):
        with pytest.raises(ValueError, match="Unsupported architecture"):
            TemporalModel(input_dim=512, arch="invalid")

    def test_lstm_forward(self):
        model = TemporalModel(input_dim=512, arch="lstm", hidden_dim=128)
        x = torch.randn(4, 8, 512)  # (B, T, feat_dim)
        out = model(x)
        assert out.shape == (4, 128)

    def test_gru_forward(self):
        model = TemporalModel(input_dim=512, arch="gru", hidden_dim=128)
        x = torch.randn(4, 8, 512)
        out = model(x)
        assert out.shape == (4, 128)

    def test_transformer_forward(self):
        model = TemporalModel(input_dim=512, arch="transformer", hidden_dim=128)
        x = torch.randn(4, 8, 512)
        out = model(x)
        assert out.shape == (4, 512)

    def test_bidirectional_lstm(self):
        model = TemporalModel(
            input_dim=512, arch="lstm", hidden_dim=128, bidirectional=True
        )
        x = torch.randn(4, 8, 512)
        out = model(x)
        assert out.shape == (4, 256)  # 128 * 2

    def test_with_lengths(self):
        model = TemporalModel(input_dim=512, arch="lstm", hidden_dim=128)
        x = torch.randn(4, 8, 512)
        lengths = torch.tensor([8, 6, 4, 2])
        out = model(x, lengths)
        assert out.shape == (4, 128)

    def test_transformer_with_lengths(self):
        model = TemporalModel(input_dim=512, arch="transformer", hidden_dim=128)
        x = torch.randn(4, 8, 512)
        lengths = torch.tensor([8, 6, 4, 2])
        out = model(x, lengths)
        assert out.shape == (4, 512)

    def test_dropout_applied(self):
        model = TemporalModel(input_dim=512, arch="lstm", dropout=0.5)
        model.train()
        x = torch.randn(4, 8, 512)
        out1 = model(x)
        out2 = model(x)
        # With dropout, outputs should differ in training mode
        assert not torch.allclose(out1, out2, atol=1e-6)
