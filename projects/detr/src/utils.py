"""
工具函数：张量操作、嵌套张量等
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, List


class NestedTensor:
    """
    嵌套张量：处理不同尺寸的图像
    包含张量和掩码
    """
    def __init__(self, tensors, mask: Optional[torch.Tensor]):
        self.tensors = tensors
        self.mask = mask

    def to(self, device):
        cast_tensor = self.tensors.to(device)
        mask = self.mask
        if mask is not None:
            cast_mask = mask.to(device)
        else:
            cast_mask = None
        return NestedTensor(cast_tensor, cast_mask)

    def decompose(self):
        return self.tensors, self.mask

    def __repr__(self):
        return str(self.tensors)


def nested_tensor_from_tensor_list(tensor_list):
    """
    从张量列表创建嵌套张量
    处理不同尺寸的图像，进行填充和创建掩码
    """
    # 如果输入是4D tensor，转换为3D tensor列表
    if isinstance(tensor_list, torch.Tensor):
        if tensor_list.ndim == 4:
            tensor_list = list(tensor_list.unbind(0))
        else:
            raise ValueError(f'不支持的输入维度: {tensor_list.ndim}')

    if not isinstance(tensor_list, list):
        tensor_list = list(tensor_list)

    if len(tensor_list) == 0:
        raise ValueError('输入列表不能为空')

    if tensor_list[0].ndim == 3:
        max_size = torch.stack([torch.tensor(img.shape) for img in tensor_list]).max(0)[0]
        batch_shape = [len(tensor_list)] + list(max_size)
        b, c, h, w = batch_shape
        dtype = tensor_list[0].dtype
        device = tensor_list[0].device
        tensor = torch.zeros(batch_shape, dtype=dtype, device=device)
        mask = torch.ones((b, h, w), dtype=torch.bool, device=device)
        for i, img in enumerate(tensor_list):
            tensor[i, :img.shape[0], :img.shape[1], :img.shape[2]] = img
            mask[i, :img.shape[1], :img.shape[2]] = False
    else:
        raise ValueError(f'不支持的输入维度: {tensor_list[0].ndim}')
    return NestedTensor(tensor, mask)


class PositionEmbeddingSine(nn.Module):
    """
    正弦位置编码
    用于为图像特征添加位置信息
    """
    def __init__(self, num_pos_feats=64, temperature=10000, normalize=False, scale=None):
        super().__init__()
        self.num_pos_feats = num_pos_feats
        self.temperature = temperature
        self.normalize = normalize
        if scale is not None and normalize is False:
            raise ValueError("normalize should be True if scale is passed")
        if scale is None:
            scale = 2 * 3.141592653589793
        self.scale = scale

    def forward(self, tensor_list: NestedTensor):
        x = tensor_list.tensors
        mask = tensor_list.mask
        assert mask is not None
        not_mask = ~mask
        y_embed = not_mask.cumsum(1, dtype=torch.float32)
        x_embed = not_mask.cumsum(2, dtype=torch.float32)
        if self.normalize:
            eps = 1e-6
            y_embed = y_embed / (y_embed[:, -1:, :] + eps) * self.scale
            x_embed = x_embed / (x_embed[:, :, -1:] + eps) * self.scale

        dim_t = torch.arange(self.num_pos_feats, dtype=torch.float32, device=x.device)
        dim_t = self.temperature ** (2 * (dim_t // 2) / self.num_pos_feats)

        pos_x = x_embed[:, :, :, None] / dim_t
        pos_y = y_embed[:, :, :, None] / dim_t
        pos_x = torch.stack((pos_x[:, :, :, 0::2].sin(), pos_x[:, :, :, 1::2].cos()), dim=4).flatten(3)
        pos_y = torch.stack((pos_y[:, :, :, 0::2].sin(), pos_y[:, :, :, 1::2].cos()), dim=4).flatten(3)
        pos = torch.cat((pos_y, pos_x), dim=3).permute(0, 3, 1, 2)
        return pos


class MLP(nn.Module):
    """
    多层感知机
    简单的全连接网络，用于预测边界框和类别
    """
    def __init__(self, input_dim, hidden_dim, output_dim, num_layers):
        super().__init__()
        self.num_layers = num_layers
        h = [hidden_dim] * (num_layers - 1)
        self.layers = nn.ModuleList(
            nn.Linear(n, k) for n, k in zip([input_dim] + h, h + [output_dim])
        )

    def forward(self, x):
        for i, layer in enumerate(self.layers):
            x = F.relu(layer(x)) if i < self.num_layers - 1 else layer(x)
        return x
