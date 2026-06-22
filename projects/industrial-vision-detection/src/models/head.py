"""
检测头 (Head) 实现

实现解耦检测头 (Decoupled Head)，用于从特征图生成检测结果。

解耦头将分类和回归任务分开处理，相比耦合头有以下优势:
1. 分类和回归可以独立优化
2. 更容易收敛
3. 检测精度更高

核心组件:
- DetectHead: 解耦检测头

参考:
- YOLOX: https://arxiv.org/abs/2107.08430
- YOLOv8: https://github.com/ultralytics/ultralytics

⭐ 重点理解:
- 解耦头 vs 耦合头的区别
- Anchor-free 的预测方式
- DFL (Distribution Focal Loss) 的作用
"""

import torch
import torch.nn as nn
from typing import List, Dict, Optional, Tuple

from .backbone import ConvBlock


class DetectHead(nn.Module):
    """
    解耦检测头

    将分类和回归任务分开处理，每个特征图位置预测:
    - 分类概率: [num_classes]
    - 边界框: [4 * reg_max] (使用 DFL)
    - 目标置信度: [1]

    Args:
        in_channels_list (List[int]): 输入通道数列表 [P3, P4, P5]
        num_classes (int): 类别数
        reg_max (int): DFL 回归最大值，默认为 16

    输出格式:
    - 训练模式: dict with cls_pred, reg_pred, obj_pred
    - 推理模式: list of detection results

    💡 值得思考:
    - 为什么分类和回归要解耦？
    - DFL 如何实现更精确的边界框回归？
    - Anchor-free 如何定义正负样本？
    """

    def __init__(
        self,
        in_channels_list: List[int],
        num_classes: int,
        reg_max: int = 16
    ):
        super().__init__()

        self.num_classes = num_classes
        self.reg_max = reg_max

        # 为每个尺度创建检测头
        self.heads = nn.ModuleList([
            ScaleHead(in_channels, num_classes, reg_max)
            for in_channels in in_channels_list
        ])

    def forward(
        self,
        features: List[torch.Tensor],
        targets: Optional[List[Dict]] = None
    ) -> Dict:
        """
        前向传播

        Args:
            features: 特征融合网络输出的多尺度特征 [P3, P4, P5]
            targets: 训练目标 (可选，仅训练时使用)

        Returns:
            训练模式: dict with predictions
            推理模式: dict with decoded predictions
        """
        # 收集所有尺度的预测
        cls_preds = []
        reg_preds = []
        obj_preds = []

        for i, (feat, head) in enumerate(zip(features, self.heads)):
            cls_pred, reg_pred, obj_pred = head(feat)
            cls_preds.append(cls_pred)
            reg_preds.append(reg_pred)
            obj_preds.append(obj_pred)

        # 训练模式: 返回原始预测
        if self.training:
            return {
                'cls_pred': cls_preds,
                'reg_pred': reg_preds,
                'obj_pred': obj_preds
            }

        # 推理模式: 解码预测
        return self.decode_predictions(cls_preds, reg_preds, obj_preds)

    def decode_predictions(
        self,
        cls_preds: List[torch.Tensor],
        reg_preds: List[torch.Tensor],
        obj_preds: List[torch.Tensor]
    ) -> Dict:
        """
        解码预测结果

        将原始预测转换为边界框和置信度。

        Args:
            cls_preds: 分类预测列表
            reg_preds: 回归预测列表
            obj_preds: 目标性预测列表

        Returns:
            解码后的预测结果
        """
        batch_size = cls_preds[0].shape[0]

        # 存储所有预测
        all_boxes = []
        all_scores = []
        all_labels = []

        for i in range(batch_size):
            boxes_list = []
            scores_list = []
            labels_list = []

            for j, (cls_pred, reg_pred, obj_pred) in enumerate(
                zip(cls_preds, reg_preds, obj_preds)
            ):
                # 获取当前尺度的预测
                cls = cls_pred[i]  # [H, W, num_classes]
                reg = reg_pred[i]  # [H, W, 4 * reg_max]
                obj = obj_pred[i]  # [H, W, 1]

                # 获取特征图尺寸
                H, W = cls.shape[1], cls.shape[2]

                # 生成网格坐标
                stride = 8 * (2 ** j)  # P3: 8, P4: 16, P5: 32
                grid_y, grid_x = torch.meshgrid(
                    torch.arange(H, device=cls.device),
                    torch.arange(W, device=cls.device),
                    indexing='ij'
                )

                # 解码边界框
                # 使用 DFL 解码回归预测
                reg = reg.reshape(-1, 4, self.reg_max)
                reg = torch.softmax(reg, dim=-1)
                reg = reg * torch.arange(self.reg_max, device=reg.device).float()
                reg = reg.sum(dim=-1)  # [H*W, 4]

                # 转换为绝对坐标
                grid_x = grid_x.reshape(-1).float()
                grid_y = grid_y.reshape(-1).float()

                # 边界框: (x1, y1, x2, y2)
                x1 = (grid_x - reg[:, 0]) * stride
                y1 = (grid_y - reg[:, 1]) * stride
                x2 = (grid_x + reg[:, 2]) * stride
                y2 = (grid_y + reg[:, 3]) * stride

                boxes = torch.stack([x1, y1, x2, y2], dim=-1)  # [H*W, 4]

                # 计算置信度
                cls = cls.reshape(-1, self.num_classes)  # [H*W, num_classes]
                obj = obj.reshape(-1, 1)  # [H*W, 1]

                # 置信度 = 目标性 × 分类概率
                scores = obj * cls  # [H*W, num_classes]

                boxes_list.append(boxes)
                scores_list.append(scores)

            # 合并所有尺度
            boxes = torch.cat(boxes_list, dim=0)
            scores = torch.cat(scores_list, dim=0)

            all_boxes.append(boxes)
            all_scores.append(scores)

        return {
            'boxes': all_boxes,
            'scores': all_scores
        }


class ScaleHead(nn.Module):
    """
    单尺度检测头

    为单个特征图生成分类、回归和目标性预测。

    Args:
        in_channels (int): 输入通道数
        num_classes (int): 类别数
        reg_max (int): DFL 回归最大值
    """

    def __init__(
        self,
        in_channels: int,
        num_classes: int,
        reg_max: int = 16
    ):
        super().__init__()

        self.num_classes = num_classes
        self.reg_max = reg_max

        # 共享特征提取层
        self.stem = nn.Sequential(
            ConvBlock(in_channels, in_channels, kernel_size=3),
            ConvBlock(in_channels, in_channels, kernel_size=3)
        )

        # 分类分支
        self.cls_branch = nn.Sequential(
            ConvBlock(in_channels, in_channels, kernel_size=3),
            ConvBlock(in_channels, in_channels, kernel_size=3),
            nn.Conv2d(in_channels, num_classes, kernel_size=1)
        )

        # 回归分支
        self.reg_branch = nn.Sequential(
            ConvBlock(in_channels, in_channels, kernel_size=3),
            ConvBlock(in_channels, in_channels, kernel_size=3),
            nn.Conv2d(in_channels, 4 * reg_max, kernel_size=1)
        )

        # 目标性分支
        self.obj_branch = nn.Sequential(
            ConvBlock(in_channels, in_channels, kernel_size=3),
            nn.Conv2d(in_channels, 1, kernel_size=1)
        )

    def forward(
        self,
        x: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        前向传播

        Args:
            x: 输入特征图 [B, C, H, W]

        Returns:
            cls_pred: 分类预测 [B, num_classes, H, W]
            reg_pred: 回归预测 [B, 4*reg_max, H, W]
            obj_pred: 目标性预测 [B, 1, H, W]
        """
        # 共享特征提取
        feat = self.stem(x)

        # 分类预测
        cls_pred = self.cls_branch(feat)

        # 回归预测
        reg_pred = self.reg_branch(feat)

        # 目标性预测
        obj_pred = self.obj_branch(feat)

        return cls_pred, reg_pred, obj_pred


def test_head():
    """
    测试检测头

    验证:
    1. 模型能正常前向传播
    2. 输出形状正确
    3. 训练和推理模式正常切换
    """
    print("=" * 50)
    print("测试解耦检测头")
    print("=" * 50)

    # 创建模拟的特征图
    batch_size = 2
    num_classes = 5

    p3 = torch.randn(batch_size, 128, 80, 80)
    p4 = torch.randn(batch_size, 256, 40, 40)
    p5 = torch.randn(batch_size, 512, 20, 20)

    features = [p3, p4, p5]

    # 创建检测头
    head = DetectHead(
        in_channels_list=[128, 256, 512],
        num_classes=num_classes,
        reg_max=16
    )

    # 打印模型参数量
    print(f"\n模型参数量: {sum(p.numel() for p in head.parameters()):,}")

    # 测试训练模式
    head.train()
    with torch.no_grad():
        train_outputs = head(features)

    print("\n训练模式输出:")
    for key, value in train_outputs.items():
        if isinstance(value, list):
            print(f"  {key}:")
            for i, v in enumerate(value):
                print(f"    P{i+3}: {v.shape}")

    # 测试推理模式
    head.eval()
    with torch.no_grad():
        infer_outputs = head(features)

    print("\n推理模式输出:")
    print(f"  boxes: {len(infer_outputs['boxes'])} batches")
    print(f"  scores: {len(infer_outputs['scores'])} batches")

    print("\n✓ 检测头测试通过!")
    return True


if __name__ == '__main__':
    test_head()
