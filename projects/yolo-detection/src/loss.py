"""
YOLO Loss Function.

Implements the YOLO v1 loss function which consists of:
1. Localization loss (x, y, w, h)
2. Confidence loss (object present)
3. Confidence loss (no object)
4. Classification loss

The loss is computed as:
L = λ_coord * Σ 1_obj^ij * [(x - x̂)² + (y - ŷ)²]
  + λ_coord * Σ 1_obj^ij * [(√w - √ŵ)² + (√h - √ĥ)²]
  + Σ 1_obj^ij * (C - Ĉ)²
  + λ_noobj * Σ 1_noobj^ij * (C - Ĉ)²
  + Σ 1_obj^i * Σ_c (p(c) - p̂(c))²

Where:
- 1_obj^ij = 1 if box j in cell i is responsible for detection
- 1_noobj^ij = 1 if no object in cell i
- λ_coord = 5.0 (weight for localization loss)
- λ_noobj = 0.5 (weight for no-object confidence loss)
"""

import torch
import torch.nn as nn
from typing import Tuple


class YOLOLoss(nn.Module):
    """
    YOLO v1 loss function.

    Args:
        grid_size: Number of grid cells (S). Default: 7
        num_boxes: Number of bounding boxes per cell (B). Default: 2
        num_classes: Number of object classes (C). Default: 20
        lambda_coord: Weight for localization loss. Default: 5.0
        lambda_noobj: Weight for no-object confidence loss. Default: 0.5
    """

    def __init__(
        self,
        grid_size: int = 7,
        num_boxes: int = 2,
        num_classes: int = 20,
        lambda_coord: float = 5.0,
        lambda_noobj: float = 0.5,
    ):
        super().__init__()
        self.grid_size = grid_size
        self.num_boxes = num_boxes
        self.num_classes = num_classes
        self.lambda_coord = lambda_coord
        self.lambda_noobj = lambda_noobj

    def forward(
        self, predictions: torch.Tensor, targets: torch.Tensor
    ) -> Tuple[torch.Tensor, dict]:
        """
        Compute YOLO loss.

        Args:
            predictions: Raw network output, shape (batch, S*S*(B*5+C))
            targets: Ground truth tensor, shape (batch, S, S, B*5+C)
                For each cell: [x, y, w, h, confidence, ...] for each box
                Then class probabilities

        Returns:
            total_loss: Scalar loss value
            loss_dict: Dictionary with individual loss components
        """
        batch_size = predictions.shape[0]
        S = self.grid_size
        B = self.num_boxes
        C = self.num_classes

        # Reshape predictions to (batch, S, S, B*5+C)
        predictions = predictions.view(batch_size, S, S, B * 5 + C)

        # Extract prediction components
        # For each box: [x, y, w, h, confidence]
        pred_boxes = []
        pred_confs = []
        for b in range(B):
            idx = b * 5
            pred_boxes.append(predictions[..., idx : idx + 4])  # x, y, w, h
            pred_confs.append(predictions[..., idx + 4])  # confidence

        # Class predictions (same for all boxes in a cell)
        pred_classes = predictions[..., B * 5 : B * 5 + C]

        # Extract target components
        target_boxes = []
        target_confs = []
        for b in range(B):
            idx = b * 5
            target_boxes.append(targets[..., idx : idx + 4])
            target_confs.append(targets[..., idx + 4])

        target_classes = targets[..., B * 5 : B * 5 + C]

        # Object mask: 1 if object present in cell, 0 otherwise
        # Use the first box's confidence as indicator
        obj_mask = target_confs[0]  # (batch, S, S)
        noobj_mask = 1.0 - obj_mask

        # =============================================
        # 1. Localization Loss (x, y)
        # =============================================
        loc_loss_xy = torch.tensor(0.0, device=predictions.device)
        for b in range(B):
            # Only compute for cells with objects
            pred_xy = pred_boxes[b][..., :2]  # x, y
            target_xy = target_boxes[b][..., :2]
            loc_loss_xy += torch.sum(
                obj_mask.unsqueeze(-1) * (pred_xy - target_xy) ** 2
            )

        # =============================================
        # 2. Localization Loss (w, h) - sqrt version
        # =============================================
        loc_loss_wh = torch.tensor(0.0, device=predictions.device)
        for b in range(B):
            pred_wh = pred_boxes[b][..., 2:4]  # w, h
            target_wh = target_boxes[b][..., 2:4]
            # Use sqrt to weight small boxes more
            pred_wh_sqrt = torch.sign(pred_wh) * torch.sqrt(torch.abs(pred_wh) + 1e-6)
            target_wh_sqrt = torch.sqrt(target_wh + 1e-6)
            loc_loss_wh += torch.sum(
                obj_mask.unsqueeze(-1) * (pred_wh_sqrt - target_wh_sqrt) ** 2
            )

        # =============================================
        # 3. Confidence Loss (object present)
        # =============================================
        conf_loss_obj = torch.tensor(0.0, device=predictions.device)
        for b in range(B):
            pred_conf = pred_confs[b]
            # Use IoU as target confidence
            # For simplicity, use the target confidence directly
            target_conf = target_confs[b]
            conf_loss_obj += torch.sum(obj_mask * (pred_conf - target_conf) ** 2)

        # =============================================
        # 4. Confidence Loss (no object)
        # =============================================
        conf_loss_noobj = torch.tensor(0.0, device=predictions.device)
        for b in range(B):
            pred_conf = pred_confs[b]
            conf_loss_noobj += torch.sum(noobj_mask * pred_conf ** 2)

        # =============================================
        # 5. Classification Loss
        # =============================================
        class_loss = torch.sum(
            obj_mask.unsqueeze(-1) * (pred_classes - target_classes) ** 2
        )

        # =============================================
        # Total Loss
        # =============================================
        total_loss = (
            self.lambda_coord * (loc_loss_xy + loc_loss_wh)
            + conf_loss_obj
            + self.lambda_noobj * conf_loss_noobj
            + class_loss
        )

        # Normalize by batch size
        total_loss = total_loss / batch_size

        loss_dict = {
            "total": total_loss.item(),
            "loc_xy": loc_loss_xy.item() / batch_size,
            "loc_wh": loc_loss_wh.item() / batch_size,
            "conf_obj": conf_loss_obj.item() / batch_size,
            "conf_noobj": conf_loss_noobj.item() / batch_size,
            "class": class_loss.item() / batch_size,
        }

        return total_loss, loss_dict


def create_target_tensor(
    boxes: list,
    labels: list,
    grid_size: int = 7,
    num_boxes: int = 2,
    num_classes: int = 20,
    image_size: int = 448,
) -> torch.Tensor:
    """
    Create target tensor from ground truth annotations.

    Args:
        boxes: List of bounding boxes, each as [x_center, y_center, width, height]
               in absolute pixel coordinates
        labels: List of class indices
        grid_size: Grid size S
        num_boxes: Number of boxes per cell B
        num_classes: Number of classes C
        image_size: Input image size

    Returns:
        Target tensor of shape (S, S, B*5+C)
    """
    target = torch.zeros(grid_size, grid_size, num_boxes * 5 + num_classes)

    cell_size = image_size / grid_size

    for box, label in zip(boxes, labels):
        x, y, w, h = box

        # Determine which cell this box belongs to
        cell_x = int(x / cell_size)
        cell_y = int(y / cell_size)

        # Clamp to grid bounds
        cell_x = min(cell_x, grid_size - 1)
        cell_y = min(cell_y, grid_size - 1)

        # Compute cell-relative coordinates
        x_rel = (x / cell_size) - cell_x
        y_rel = (y / cell_size) - cell_y
        w_rel = w / image_size
        h_rel = h / image_size

        # Find an empty box slot
        placed = False
        for b in range(num_boxes):
            idx = b * 5
            if target[cell_y, cell_x, idx + 4] == 0:  # No box here yet
                target[cell_y, cell_x, idx] = x_rel
                target[cell_y, cell_x, idx + 1] = y_rel
                target[cell_y, cell_x, idx + 2] = w_rel
                target[cell_y, cell_x, idx + 3] = h_rel
                target[cell_y, cell_x, idx + 4] = 1.0  # Confidence
                target[cell_y, cell_x, num_boxes * 5 + label] = 1.0
                placed = True
                break

        # If no empty slot, replace the first box
        if not placed:
            idx = 0
            target[cell_y, cell_x, idx] = x_rel
            target[cell_y, cell_x, idx + 1] = y_rel
            target[cell_y, cell_x, idx + 2] = w_rel
            target[cell_y, cell_x, idx + 3] = h_rel
            target[cell_y, cell_x, idx + 4] = 1.0
            target[cell_y, cell_x, num_boxes * 5 + label] = 1.0

    return target
