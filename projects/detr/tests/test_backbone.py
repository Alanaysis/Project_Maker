"""
骨干网络测试
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.backbone import Backbone, build_backbone, FrozenBatchNorm2d
from src.utils import NestedTensor


class TestBackbone:
    """骨干网络测试类"""

    def test_backbone_resnet18(self):
        """测试ResNet18骨干网络"""
        backbone = Backbone('resnet18', train_backbone=True)
        assert backbone.num_channels == [512]

        # 创建输入
        x = torch.randn(2, 3, 320, 320)
        mask = torch.zeros(2, 320, 320, dtype=torch.bool)
        tensor_list = NestedTensor(x, mask)

        output = backbone(tensor_list)
        assert '0' in output
        assert output['0'].tensors.shape == (2, 512, 10, 10)

    def test_backbone_resnet50(self):
        """测试ResNet50骨干网络"""
        backbone = Backbone('resnet50', train_backbone=True)
        assert backbone.num_channels == [2048]

        x = torch.randn(2, 3, 320, 320)
        mask = torch.zeros(2, 320, 320, dtype=torch.bool)
        tensor_list = NestedTensor(x, mask)

        output = backbone(tensor_list)
        assert output['0'].tensors.shape == (2, 2048, 10, 10)

    def test_build_backbone(self):
        """测试构建骨干网络"""
        backbone = build_backbone('resnet18', train_backbone=True, hidden_dim=256)
        assert backbone.num_channels == [512]

        x = torch.randn(2, 3, 320, 320)
        mask = torch.zeros(2, 320, 320, dtype=torch.bool)
        tensor_list = NestedTensor(x, mask)

        features, pos = backbone(tensor_list)
        assert len(features) == 1
        assert len(pos) == 1
        assert features[0].tensors.shape == (2, 512, 10, 10)
        assert pos[0].shape == (2, 256, 10, 10)

    def test_frozen_batch_norm(self):
        """测试冻结的BatchNorm"""
        fbn = FrozenBatchNorm2d(64)
        x = torch.randn(2, 64, 10, 10)
        out = fbn(x)
        assert out.shape == x.shape

    def test_backbone_trainable_params(self):
        """测试骨干网络参数可训练性"""
        # 训练模式
        backbone_train = Backbone('resnet18', train_backbone=True)
        for param in backbone_train.parameters():
            assert param.requires_grad

        # 冻结模式
        backbone_frozen = Backbone('resnet18', train_backbone=False)
        for param in backbone_frozen.parameters():
            assert not param.requires_grad


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
