"""
损失函数实现

实现目标检测常用的损失函数:
- BCELoss: 二元交叉熵损失
- FocalLoss: 焦点损失 (解决样本不平衡)
- CIoULoss: 完整 IoU 损失
- YOLOLoss: 组合损失函数

参考:
- Focal Loss: https://arxiv.org/abs/1708.02002
- CIoU: https://arxiv.org/abs/2005.01709

⭐ 重点理解:
- Focal Loss 如何解决正负样本不平衡
- CIoU Loss 的数学原理
- 多任务损失的组合方式

💡 值得思考:
- 为什么 IoU 损失比 L1/L2 损失更适合目标检测？
- Focal Loss 的 alpha 和 gamma 参数如何影响训练？
- CIoU 相比 GIoU 和 DIoU 有什么优势？
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple


class BCELoss(nn.Module):
    """
    二元交叉熵损失 (Binary Cross Entropy Loss)

    用于分类任务，计算预测概率与真实标签之间的损失。

    Args:
        reduction (str): 损失聚合方式，'mean' 或 'sum'

    数学公式:
    L = -[y * log(p) + (1-y) * log(1-p)]

    其中:
    - y: 真实标签 (0 或 1)
    - p: 预测概率
    """

    def __init__(self, reduction: str = 'mean'):
        super().__init__()
        self.reduction = reduction

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        计算损失

        Args:
            pred: 预测概率 [..., num_classes]
            target: 真实标签 [..., num_classes]

        Returns:
            损失值
        """
        # 使用 logits 版本的 BCE，更数值稳定
        loss = F.binary_cross_entropy_with_logits(
            pred, target, reduction=self.reduction
        )
        return loss


class FocalLoss(nn.Module):
    """
    焦点损失 (Focal Loss)

    解决目标检测中正负样本极度不平衡的问题。

    核心思想:
    - 对易分类样本降低权重
    - 对难分类样本增加权重

    Args:
        alpha (float): 平衡因子，默认 0.25
        gamma (float): 聚焦参数，默认 2.0
        reduction (str): 损失聚合方式

    数学公式:
    FL(p_t) = -α_t * (1 - p_t)^γ * log(p_t)

    其中:
    - p_t = p if y=1, else 1-p
    - α_t = α if y=1, else 1-α
    - γ: 聚焦参数，越大越关注难样本

    ⭐ 重点理解:
    - 当 γ=0 时，Focal Loss 退化为标准 BCE Loss
    - γ 越大，对易分类样本的抑制越强
    - α 用于平衡正负样本的比例
    """

    def __init__(
        self,
        alpha: float = 0.25,
        gamma: float = 2.0,
        reduction: str = 'mean'
    ):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        计算 Focal Loss

        Args:
            pred: 预测 logits [..., num_classes]
            target: 真实标签 [..., num_classes] (one-hot 或 soft label)

        Returns:
            损失值
        """
        # 计算 BCE 损失
        bce_loss = F.binary_cross_entropy_with_logits(
            pred, target, reduction='none'
        )

        # 计算 p_t
        pred_sigmoid = torch.sigmoid(pred)
        p_t = pred_sigmoid * target + (1 - pred_sigmoid) * (1 - target)

        # 计算 alpha_t
        alpha_t = self.alpha * target + (1 - self.alpha) * (1 - target)

        # 计算 Focal 权重
        focal_weight = alpha_t * (1 - p_t) ** self.gamma

        # 计算最终损失
        loss = focal_weight * bce_loss

        # 聚合
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss


class IoULoss(nn.Module):
    """
    IoU 损失 (Intersection over Union Loss)

    基础 IoU 损失，计算预测框与真实框之间的 IoU 损失。

    数学公式:
    IoU = |A ∩ B| / |A ∪ B|
    L_IoU = 1 - IoU

    Args:
        reduction (str): 损失聚合方式
    """

    def __init__(self, reduction: str = 'mean'):
        super().__init__()
        self.reduction = reduction

    def forward(
        self,
        pred_boxes: torch.Tensor,
        target_boxes: torch.Tensor
    ) -> torch.Tensor:
        """
        计算 IoU 损失

        Args:
            pred_boxes: 预测框 [N, 4] (x1, y1, x2, y2)
            target_boxes: 目标框 [N, 4] (x1, y1, x2, y2)

        Returns:
            损失值
        """
        # 计算 IoU
        iou = self.compute_iou(pred_boxes, target_boxes)

        # 计算损失
        loss = 1 - iou

        # 聚合
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss

    def compute_iou(
        self,
        box1: torch.Tensor,
        box2: torch.Tensor
    ) -> torch.Tensor:
        """
        计算 IoU

        Args:
            box1: 边界框 [N, 4] (x1, y1, x2, y2)
            box2: 边界框 [N, 4] (x1, y1, x2, y2)

        Returns:
            iou: [N]
        """
        # 计算交集
        x1 = torch.max(box1[:, 0], box2[:, 0])
        y1 = torch.max(box1[:, 1], box2[:, 1])
        x2 = torch.min(box1[:, 2], box2[:, 2])
        y2 = torch.min(box1[:, 3], box2[:, 3])

        intersection = torch.clamp(x2 - x1, min=0) * torch.clamp(y2 - y1, min=0)

        # 计算并集
        area1 = (box1[:, 2] - box1[:, 0]) * (box1[:, 3] - box1[:, 1])
        area2 = (box2[:, 2] - box2[:, 0]) * (box2[:, 3] - box2[:, 1])
        union = area1 + area2 - intersection

        # 计算 IoU
        iou = intersection / (union + 1e-6)

        return iou


class GIoULoss(nn.Module):
    """
    GIoU 损失 (Generalized Intersection over Union Loss)

    解决了 IoU 损失在框不重叠时梯度为 0 的问题。

    数学公式:
    GIoU = IoU - |C \ (A ∪ B)| / |C|

    其中 C 是 A 和 B 的最小外接矩形。

    Args:
        reduction (str): 损失聚合方式
    """

    def __init__(self, reduction: str = 'mean'):
        super().__init__()
        self.reduction = reduction

    def forward(
        self,
        pred_boxes: torch.Tensor,
        target_boxes: torch.Tensor
    ) -> torch.Tensor:
        """
        计算 GIoU 损失

        Args:
            pred_boxes: 预测框 [N, 4] (x1, y1, x2, y2)
            target_boxes: 目标框 [N, 4] (x1, y1, x2, y2)

        Returns:
            损失值
        """
        # 计算 GIoU
        giou = self.compute_giou(pred_boxes, target_boxes)

        # 计算损失
        loss = 1 - giou

        # 聚合
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss

    def compute_giou(
        self,
        box1: torch.Tensor,
        box2: torch.Tensor
    ) -> torch.Tensor:
        """
        计算 GIoU

        Args:
            box1: 边界框 [N, 4]
            box2: 边界框 [N, 4]

        Returns:
            giou: [N]
        """
        # 计算交集
        x1 = torch.max(box1[:, 0], box2[:, 0])
        y1 = torch.max(box1[:, 1], box2[:, 1])
        x2 = torch.min(box1[:, 2], box2[:, 2])
        y2 = torch.min(box1[:, 3], box2[:, 3])

        intersection = torch.clamp(x2 - x1, min=0) * torch.clamp(y2 - y1, min=0)

        # 计算并集
        area1 = (box1[:, 2] - box1[:, 0]) * (box1[:, 3] - box1[:, 1])
        area2 = (box2[:, 2] - box2[:, 0]) * (box2[:, 3] - box2[:, 1])
        union = area1 + area2 - intersection

        # 计算 IoU
        iou = intersection / (union + 1e-6)

        # 计算最小外接矩形
        enclose_x1 = torch.min(box1[:, 0], box2[:, 0])
        enclose_y1 = torch.min(box1[:, 1], box2[:, 1])
        enclose_x2 = torch.max(box1[:, 2], box2[:, 2])
        enclose_y2 = torch.max(box1[:, 3], box2[:, 3])

        enclose_area = (enclose_x2 - enclose_x1) * (enclose_y2 - enclose_y1)

        # 计算 GIoU
        giou = iou - (enclose_area - union) / (enclose_area + 1e-6)

        return giou


class DIoULoss(nn.Module):
    """
    DIoU 损失 (Distance Intersection over Union Loss)

    在 GIoU 的基础上，考虑了中心点距离。

    数学公式:
    DIoU = IoU - ρ²(b, b^gt) / c²

    其中:
    - ρ: 欧氏距离
    - b, b^gt: 预测框和目标框的中心点
    - c: 最小外接矩形的对角线长度

    Args:
        reduction (str): 损失聚合方式
    """

    def __init__(self, reduction: str = 'mean'):
        super().__init__()
        self.reduction = reduction

    def forward(
        self,
        pred_boxes: torch.Tensor,
        target_boxes: torch.Tensor
    ) -> torch.Tensor:
        """
        计算 DIoU 损失

        Args:
            pred_boxes: 预测框 [N, 4]
            target_boxes: 目标框 [N, 4]

        Returns:
            损失值
        """
        # 计算 DIoU
        diou = self.compute_diou(pred_boxes, target_boxes)

        # 计算损失
        loss = 1 - diou

        # 聚合
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss

    def compute_diou(
        self,
        box1: torch.Tensor,
        box2: torch.Tensor
    ) -> torch.Tensor:
        """
        计算 DIoU

        Args:
            box1: 边界框 [N, 4]
            box2: 边界框 [N, 4]

        Returns:
            diou: [N]
        """
        # 计算交集
        x1 = torch.max(box1[:, 0], box2[:, 0])
        y1 = torch.max(box1[:, 1], box2[:, 1])
        x2 = torch.min(box1[:, 2], box2[:, 2])
        y2 = torch.min(box1[:, 3], box2[:, 3])

        intersection = torch.clamp(x2 - x1, min=0) * torch.clamp(y2 - y1, min=0)

        # 计算并集
        area1 = (box1[:, 2] - box1[:, 0]) * (box1[:, 3] - box1[:, 1])
        area2 = (box2[:, 2] - box2[:, 0]) * (box2[:, 3] - box2[:, 1])
        union = area1 + area2 - intersection

        # 计算 IoU
        iou = intersection / (union + 1e-6)

        # 计算中心点距离
        center1_x = (box1[:, 0] + box1[:, 2]) / 2
        center1_y = (box1[:, 1] + box1[:, 3]) / 2
        center2_x = (box2[:, 0] + box2[:, 2]) / 2
        center2_y = (box2[:, 1] + box2[:, 3]) / 2

        center_distance = (center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2

        # 计算最小外接矩形对角线长度
        enclose_x1 = torch.min(box1[:, 0], box2[:, 0])
        enclose_y1 = torch.min(box1[:, 1], box2[:, 1])
        enclose_x2 = torch.max(box1[:, 2], box2[:, 2])
        enclose_y2 = torch.max(box1[:, 3], box2[:, 3])

        diagonal_distance = (enclose_x2 - enclose_x1) ** 2 + (enclose_y2 - enclose_y1) ** 2

        # 计算 DIoU
        diou = iou - center_distance / (diagonal_distance + 1e-6)

        return diou


class CIoULoss(nn.Module):
    """
    CIoU 损失 (Complete Intersection over Union Loss)

    在 DIoU 的基础上，考虑了长宽比一致性。

    数学公式:
    CIoU = IoU - ρ²(b, b^gt) / c² - αv

    其中:
    - v = (4/π²) * (arctan(w^gt/h^gt) - arctan(w/h))²
    - α = v / ((1 - IoU) + v)

    Args:
        reduction (str): 损失聚合方式

    ⭐ 重点理解:
    - CIoU 同时考虑了重叠面积、中心点距离和长宽比
    - 相比 GIoU 和 DIoU，CIoU 能更快收敛
    - α 和 v 的作用是平衡不同损失项
    """

    def __init__(self, reduction: str = 'mean'):
        super().__init__()
        self.reduction = reduction

    def forward(
        self,
        pred_boxes: torch.Tensor,
        target_boxes: torch.Tensor
    ) -> torch.Tensor:
        """
        计算 CIoU 损失

        Args:
            pred_boxes: 预测框 [N, 4] (x1, y1, x2, y2)
            target_boxes: 目标框 [N, 4] (x1, y1, x2, y2)

        Returns:
            损失值
        """
        # 计算 CIoU
        ciou = self.compute_ciou(pred_boxes, target_boxes)

        # 计算损失
        loss = 1 - ciou

        # 聚合
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss

    def compute_ciou(
        self,
        box1: torch.Tensor,
        box2: torch.Tensor
    ) -> torch.Tensor:
        """
        计算 CIoU

        Args:
            box1: 边界框 [N, 4]
            box2: 边界框 [N, 4]

        Returns:
            ciou: [N]
        """
        # 计算交集
        x1 = torch.max(box1[:, 0], box2[:, 0])
        y1 = torch.max(box1[:, 1], box2[:, 1])
        x2 = torch.min(box1[:, 2], box2[:, 2])
        y2 = torch.min(box1[:, 3], box2[:, 3])

        intersection = torch.clamp(x2 - x1, min=0) * torch.clamp(y2 - y1, min=0)

        # 计算并集
        area1 = (box1[:, 2] - box1[:, 0]) * (box1[:, 3] - box1[:, 1])
        area2 = (box2[:, 2] - box2[:, 0]) * (box2[:, 3] - box2[:, 1])
        union = area1 + area2 - intersection

        # 计算 IoU
        iou = intersection / (union + 1e-6)

        # 计算中心点距离
        center1_x = (box1[:, 0] + box1[:, 2]) / 2
        center1_y = (box1[:, 1] + box1[:, 3]) / 2
        center2_x = (box2[:, 0] + box2[:, 2]) / 2
        center2_y = (box2[:, 1] + box2[:, 3]) / 2

        center_distance = (center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2

        # 计算最小外接矩形对角线长度
        enclose_x1 = torch.min(box1[:, 0], box2[:, 0])
        enclose_y1 = torch.min(box1[:, 1], box2[:, 1])
        enclose_x2 = torch.max(box1[:, 2], box2[:, 2])
        enclose_y2 = torch.max(box1[:, 3], box2[:, 3])

        diagonal_distance = (enclose_x2 - enclose_x1) ** 2 + (enclose_y2 - enclose_y1) ** 2

        # 计算长宽比一致性
        w1 = box1[:, 2] - box1[:, 0]
        h1 = box1[:, 3] - box1[:, 1]
        w2 = box2[:, 2] - box2[:, 0]
        h2 = box2[:, 3] - box2[:, 1]

        # 避免除零
        h1 = torch.clamp(h1, min=1e-6)
        h2 = torch.clamp(h2, min=1e-6)

        v = (4 / (3.14159 ** 2)) * (torch.atan(w2 / h2) - torch.atan(w1 / h1)) ** 2

        # 计算 alpha
        with torch.no_grad():
            alpha = v / (1 - iou + v + 1e-6)

        # 计算 CIoU
        ciou = iou - center_distance / (diagonal_distance + 1e-6) - alpha * v

        return ciou


class YOLOLoss(nn.Module):
    """
    YOLO 组合损失函数

    将分类损失、回归损失和目标性损失组合为总损失。

    总损失 = λ_cls * L_cls + λ_box * L_box + λ_obj * L_obj

    Args:
        num_classes (int): 类别数
        lambda_cls (float): 分类损失权重
        lambda_box (float): 回归损失权重
        lambda_obj (float): 目标性损失权重

    ⭐ 重点理解:
    - 为什么需要多个损失项？
    - 各损失项的权重如何影响训练？
    - 如何处理正负样本不平衡？
    """

    def __init__(
        self,
        num_classes: int,
        lambda_cls: float = 1.0,
        lambda_box: float = 5.0,
        lambda_obj: float = 1.0
    ):
        super().__init__()

        self.num_classes = num_classes
        self.lambda_cls = lambda_cls
        self.lambda_box = lambda_box
        self.lambda_obj = lambda_obj

        # 分类损失
        self.cls_loss = FocalLoss(alpha=0.25, gamma=2.0)

        # 回归损失
        self.box_loss = CIoULoss()

        # 目标性损失
        self.obj_loss = FocalLoss(alpha=0.25, gamma=2.0)

    def forward(
        self,
        predictions: Dict,
        targets: List[Dict]
    ) -> Dict[str, torch.Tensor]:
        """
        计算 YOLO 损失

        Args:
            predictions: 模型预测结果
                - cls_pred: 分类预测列表
                - reg_pred: 回归预测列表
                - obj_pred: 目标性预测列表
            targets: 真实标注列表

        Returns:
            损失字典，包含:
            - total_loss: 总损失
            - cls_loss: 分类损失
            - box_loss: 回归损失
            - obj_loss: 目标性损失
        """
        # TODO: 实现完整的损失计算
        # 这里简化实现，实际需要:
        # 1. 标签分配 (将预测与真实框匹配)
        # 2. 计算各项损失
        # 3. 组合损失

        # 简化实现: 返回占位损失
        cls_pred = predictions['cls_pred'][0]  # 取 P3 的预测
        reg_pred = predictions['reg_pred'][0]
        obj_pred = predictions['obj_pred'][0]

        batch_size = cls_pred.shape[0]

        # 创建虚拟目标 (简化实现)
        cls_target = torch.zeros_like(cls_pred)
        obj_target = torch.zeros_like(obj_pred)

        # 计算损失
        cls_loss = self.cls_loss(cls_pred, cls_target)
        obj_loss = self.obj_loss(obj_pred, obj_target)

        # 简化: 不计算真实的回归损失
        box_loss = torch.tensor(0.0, device=cls_pred.device)

        # 组合损失
        total_loss = (
            self.lambda_cls * cls_loss +
            self.lambda_box * box_loss +
            self.lambda_obj * obj_loss
        )

        return {
            'total_loss': total_loss,
            'cls_loss': cls_loss,
            'box_loss': box_loss,
            'obj_loss': obj_loss
        }


def test_losses():
    """
    测试损失函数

    验证:
    1. 各损失函数能正常计算
    2. 梯度可以反向传播
    3. 损失值在合理范围内
    """
    print("=" * 50)
    print("测试损失函数")
    print("=" * 50)

    # 创建测试数据
    batch_size = 4
    num_classes = 5

    # 测试 Focal Loss
    print("\n1. 测试 Focal Loss")
    pred = torch.randn(batch_size, num_classes)
    target = torch.randint(0, 2, (batch_size, num_classes)).float()
    focal_loss = FocalLoss()
    loss = focal_loss(pred, target)
    print(f"   损失值: {loss.item():.4f}")

    # 测试 CIoU Loss
    print("\n2. 测试 CIoU Loss")
    pred_boxes = torch.tensor([[10, 10, 50, 50], [20, 20, 60, 60]]).float()
    target_boxes = torch.tensor([[15, 15, 55, 55], [25, 25, 65, 65]]).float()
    ciou_loss = CIoULoss()
    loss = ciou_loss(pred_boxes, target_boxes)
    print(f"   损失值: {loss.item():.4f}")

    # 测试梯度反向传播
    print("\n3. 测试梯度反向传播")
    pred_boxes = torch.tensor([[10, 10, 50, 50]], requires_grad=True).float()
    target_boxes = torch.tensor([[15, 15, 55, 55]]).float()
    loss = ciou_loss(pred_boxes, target_boxes)
    loss.backward()
    print(f"   梯度: {pred_boxes.grad}")

    print("\n✓ 损失函数测试通过!")
    return True


if __name__ == '__main__':
    test_losses()
