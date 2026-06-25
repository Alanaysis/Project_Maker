"""
匈牙利匹配算法
用于将预测结果与真实标签进行最优匹配
"""

import torch
import torch.nn as nn
from scipy.optimize import linear_sum_assignment
from torch.autograd import Variable
from typing import List, Tuple


def box_cxcywh_to_xyxy(x):
    """
    将 (cx, cy, w, h) 格式转换为 (x1, y1, x2, y2) 格式
    """
    x_c, y_c, w, h = x.unbind(-1)
    b = [(x_c - 0.5 * w), (y_c - 0.5 * h),
         (x_c + 0.5 * w), (y_c + 0.5 * h)]
    return torch.stack(b, dim=-1)


def box_iou(boxes1, boxes2):
    """
    计算两组边界框的IoU
    """
    area1 = (boxes1[:, 2] - boxes1[:, 0]) * (boxes1[:, 3] - boxes1[:, 1])
    area2 = (boxes2[:, 2] - boxes2[:, 0]) * (boxes2[:, 3] - boxes2[:, 1])

    lt = torch.max(boxes1[:, None, :2], boxes2[:, :2])  # [N,M,2]
    rb = torch.min(boxes1[:, None, 2:], boxes2[:, 2:])  # [N,M,2]

    wh = (rb - lt).clamp(min=0)  # [N,M,2]
    inter = wh[:, :, 0] * wh[:, :, 1]  # [N,M]

    iou = inter / (area1[:, None] + area2 - inter)
    return iou, inter


def generalized_box_iou(boxes1, boxes2):
    """
    计算广义IoU (GIoU)
    """
    assert (boxes1[:, 2:] >= boxes1[:, :2]).all()
    assert (boxes2[:, 2:] >= boxes2[:, :2]).all()
    iou, union = box_iou(boxes1, boxes2)

    lt = torch.min(boxes1[:, None, :2], boxes2[:, :2])
    rb = torch.max(boxes1[:, None, 2:], boxes2[:, 2:])

    wh = (rb - lt).clamp(min=0)  # [N,M,2]
    area = wh[:, :, 0] * wh[:, :, 1]

    return iou - (area - union) / area


class HungarianMatcher(nn.Module):
    """
    匈牙利匹配器
    使用匈牙利算法进行二分图匹配

    匹配代价 = 分类代价 + 边界框L1代价 + GIoU代价
    """
    def __init__(self, cost_class: float = 1, cost_bbox: float = 1, cost_giou: float = 1):
        super().__init__()
        self.cost_class = cost_class
        self.cost_bbox = cost_bbox
        self.cost_giou = cost_giou
        assert cost_class != 0 or cost_bbox != 0 or cost_giou != 0, "所有代价不能都为0"

    @torch.no_grad()
    def forward(self, outputs, targets) -> List[Tuple[torch.Tensor, torch.Tensor]]:
        """
        执行匈牙利匹配

        Args:
            outputs: 模型输出
                - pred_logits: (batch_size, num_queries, num_classes)
                - pred_boxes: (batch_size, num_queries, 4) [cx, cy, w, h]
            targets: 真实标签列表
                - labels: (num_gt,) 类别标签
                - boxes: (num_gt, 4) 边界框 [cx, cy, w, h]

        Returns:
            List of (index_i, index_j) tuples:
                - index_i: 预测的索引
                - index_j: 对应的真实标签索引
        """
        bs, num_queries = outputs['pred_logits'].shape[:2]

        # 为每个batch分别计算代价
        indices = []
        for i in range(bs):
            out_prob_i = outputs['pred_logits'][i].softmax(-1)  # [num_queries, num_classes]
            out_bbox_i = outputs['pred_boxes'][i]  # [num_queries, 4]

            tgt_ids_i = targets[i]['labels']
            tgt_bbox_i = targets[i]['boxes']

            # 分类代价：使用负概率
            cost_class_i = -out_prob_i[:, tgt_ids_i]

            # 边界框L1代价
            cost_bbox_i = torch.cdist(out_bbox_i, tgt_bbox_i, p=1)

            # GIoU代价
            cost_giou_i = -generalized_box_iou(
                box_cxcywh_to_xyxy(out_bbox_i),
                box_cxcywh_to_xyxy(tgt_bbox_i)
            )

            # 总代价矩阵
            C_i = self.cost_bbox * cost_bbox_i + self.cost_class * cost_class_i + self.cost_giou * cost_giou_i
            C_i = C_i.cpu()

            # 匈牙利算法
            idx_i, idx_j = linear_sum_assignment(C_i)
            indices.append((torch.as_tensor(idx_i, dtype=torch.int64), torch.as_tensor(idx_j, dtype=torch.int64)))

        return indices


def build_matcher(cost_class=1, cost_bbox=1, cost_giou=1):
    """
    构建匈牙利匹配器
    """
    return HungarianMatcher(cost_class=cost_class, cost_bbox=cost_bbox, cost_giou=cost_giou)
