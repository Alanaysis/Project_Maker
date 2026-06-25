"""
CNN 骨干网络
使用 ResNet 提取图像特征
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.models import resnet18, resnet50
from typing import Dict, List

from .utils import NestedTensor, PositionEmbeddingSine


class FrozenBatchNorm2d(torch.nn.Module):
    """
    冻结的BatchNorm2d，用于推理和微调
    """
    def __init__(self, n):
        super().__init__()
        self.register_buffer("weight", torch.ones(n))
        self.register_buffer("bias", torch.zeros(n))
        self.register_buffer("running_mean", torch.zeros(n))
        self.register_buffer("running_var", torch.ones(n))

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
        num_batches_tracked_key = prefix + 'num_batches_tracked'
        if num_batches_tracked_key in state_dict:
            del state_dict[num_batches_tracked_key]
        super()._load_from_state_dict(
            state_dict, prefix, local_metadata, strict,
            missing_keys, unexpected_keys, error_msgs
        )

    def forward(self, x):
        w = self.weight.reshape(1, -1, 1, 1)
        b = self.bias.reshape(1, -1, 1, 1)
        rv = self.running_var.reshape(1, -1, 1, 1)
        rm = self.running_mean.reshape(1, -1, 1, 1)
        eps = 1e-5
        scale = w * (rv + eps).rsqrt()
        bias = b - rm * scale
        return x * scale + bias


class BackboneBase(nn.Module):
    """
    骨干网络基类
    """
    def __init__(self, backbone: nn.Module, train_backbone: bool, num_channels: List[int]):
        super().__init__()
        if not train_backbone:
            for name, parameter in backbone.named_parameters():
                parameter.requires_grad_(False)

        # 获取ResNet的不同层
        self.body = backbone
        self.num_channels = num_channels

    def forward(self, tensor_list: NestedTensor):
        xs = self.body(tensor_list.tensors)
        out: Dict[str, NestedTensor] = {}
        m = tensor_list.mask
        assert m is not None
        mask = F.interpolate(m[None].float(), size=xs.shape[-2:]).to(torch.bool)[0]
        out['0'] = NestedTensor(xs, mask)
        return out


class Backbone(BackboneBase):
    """
    ResNet骨干网络
    """
    def __init__(self, model_name: str = 'resnet18', train_backbone: bool = True):
        if model_name == 'resnet18':
            backbone = resnet18(pretrained=False)
            num_channels = [512]
        elif model_name == 'resnet50':
            backbone = resnet50(pretrained=False)
            num_channels = [2048]
        else:
            raise ValueError(f"不支持的骨干网络: {model_name}")

        # 移除最后的全连接层和平均池化层
        backbone = nn.Sequential(*list(backbone.children())[:-2])
        super().__init__(backbone, train_backbone, num_channels)


class Joiner(nn.Module):
    """
    连接骨干网络和位置编码
    """
    def __init__(self, backbone, position_embedding):
        super().__init__()
        self.body = backbone
        self.position_embedding = position_embedding

    def forward(self, tensor_list: NestedTensor):
        xs = self.body(tensor_list)
        out: List[NestedTensor] = []
        pos = []
        for name, x in xs.items():
            out.append(x)
            pos.append(self.position_embedding(x).to(x.tensors.dtype))
        return out, pos


def build_backbone(model_name: str = 'resnet18', train_backbone: bool = True, hidden_dim: int = 256):
    """
    构建骨干网络
    """
    backbone = Backbone(model_name, train_backbone)
    pos_enc = PositionEmbeddingSine(hidden_dim // 2, normalize=True)
    model = Joiner(backbone, pos_enc)
    model.num_channels = backbone.num_channels
    return model
