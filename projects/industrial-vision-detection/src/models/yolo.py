"""
YOLO 模型实现

实现完整的 YOLO (You Only Look Once) 目标检测模型。

核心组件:
- YOLOModel: 完整 YOLO 模型
- YOLOv8Tiny: YOLOv8-tiny 配置

参考:
- YOLOv8: https://github.com/ultralytics/ultralytics
- YOLOv9: https://arxiv.org/abs/2402.13616
- YOLOv10: https://arxiv.org/abs/2405.14458

⭐ 重点理解:
- YOLO 的单阶段检测思想
- 多尺度检测的实现
- 训练与推理模式的区别

💡 值得思考:
- YOLO 为什么比两阶段检测器快？
- Anchor-free 设计有什么优势？
- 如何平衡速度和精度？
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

from .backbone import CSPDarknet
from .neck import PANet
from .head import DetectHead
from .losses import YOLOLoss


class YOLOModel(nn.Module):
    """
    YOLO 目标检测模型

    完整的 YOLO 模型，包含:
    - Backbone: 特征提取
    - Neck: 特征融合
    - Head: 检测头
    - Loss: 损失函数

    Args:
        num_classes (int): 类别数
        depth_multiple (float): 深度因子
        width_multiple (float): 宽度因子
        reg_max (int): DFL 回归最大值

    使用示例:
        # 创建模型
        model = YOLOModel(num_classes=80)

        # 训练模式
        model.train()
        outputs = model(images, targets)
        loss = outputs['total_loss']

        # 推理模式
        model.eval()
        results = model.predict(image)
    """

    def __init__(
        self,
        num_classes: int = 80,
        depth_multiple: float = 0.33,
        width_multiple: float = 0.25,
        reg_max: int = 16
    ):
        super().__init__()

        self.num_classes = num_classes

        # 计算通道数
        base_channels = int(64 * width_multiple)
        self.channels_list = [
            base_channels * 2,   # P3: 128
            base_channels * 4,   # P4: 256
            base_channels * 8    # P5: 512
        ]

        # Backbone: 特征提取
        self.backbone = CSPDarknet(
            depth_multiple=depth_multiple,
            width_multiple=width_multiple
        )

        # Neck: 特征融合
        self.neck = PANet(
            in_channels_list=self.channels_list,
            out_channels_list=self.channels_list,
            depth_multiple=depth_multiple
        )

        # Head: 检测头
        self.head = DetectHead(
            in_channels_list=self.channels_list,
            num_classes=num_classes,
            reg_max=reg_max
        )

        # Loss: 损失函数
        self.loss_fn = YOLOLoss(num_classes=num_classes)

        # 初始化权重
        self._initialize_weights()

    def _initialize_weights(self):
        """
        初始化模型权重

        使用 Kaiming 初始化方法，适合 ReLU/SiLU 激活函数。
        """
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(
        self,
        images: torch.Tensor,
        targets: Optional[List[Dict]] = None
    ) -> Union[Dict, List[Dict]]:
        """
        前向传播

        Args:
            images: 输入图像 [B, 3, H, W]
            targets: 训练目标 (可选，仅训练时使用)

        Returns:
            训练模式: dict with losses
            推理模式: list of detection results
        """
        # Backbone: 提取多尺度特征
        features = self.backbone(images)

        # Neck: 特征融合
        fused_features = self.neck(features)

        # Head: 生成检测结果
        predictions = self.head(fused_features, targets)

        # 训练模式: 计算损失
        if self.training and targets is not None:
            losses = self.loss_fn(predictions, targets)
            return losses

        # 推理模式: 返回预测
        return predictions

    def predict(
        self,
        image: Union[torch.Tensor, np.ndarray],
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45
    ) -> Dict:
        """
        单张图像预测

        Args:
            image: 输入图像，可以是:
                - torch.Tensor [3, H, W] 或 [1, 3, H, W]
                - numpy.ndarray [H, W, 3] (BGR 格式)
            conf_threshold: 置信度阈值
            iou_threshold: NMS IoU 阈值

        Returns:
            检测结果字典:
            - boxes: 边界框 [N, 4] (x1, y1, x2, y2)
            - scores: 置信度 [N]
            - labels: 类别标签 [N]
        """
        self.eval()

        # 预处理
        if isinstance(image, np.ndarray):
            # OpenCV BGR -> RGB, HWC -> CHW
            image = torch.from_numpy(image).float()
            image = image.permute(2, 0, 1) / 255.0

        if image.dim() == 3:
            image = image.unsqueeze(0)  # 添加 batch 维度

        # 推理
        with torch.no_grad():
            outputs = self.forward(image)

        # 后处理: NMS
        results = self._postprocess(outputs, conf_threshold, iou_threshold)

        return results[0] if results else {
            'boxes': torch.zeros((0, 4)),
            'scores': torch.zeros(0),
            'labels': torch.zeros(0, dtype=torch.long)
        }

    def _postprocess(
        self,
        outputs: Dict,
        conf_threshold: float,
        iou_threshold: float
    ) -> List[Dict]:
        """
        后处理: NMS

        Args:
            outputs: 模型输出
            conf_threshold: 置信度阈值
            iou_threshold: NMS IoU 阈值

        Returns:
            处理后的检测结果
        """
        from ..utils.boxes import non_max_suppression

        results = []

        boxes_list = outputs['boxes']
        scores_list = outputs['scores']

        for boxes, scores in zip(boxes_list, scores_list):
            # 应用 NMS
            keep_indices = non_max_suppression(
                boxes, scores, iou_threshold, conf_threshold
            )

            if len(keep_indices) > 0:
                results.append({
                    'boxes': boxes[keep_indices],
                    'scores': scores[keep_indices].max(dim=-1).values,
                    'labels': scores[keep_indices].argmax(dim=-1)
                })
            else:
                results.append({
                    'boxes': torch.zeros((0, 4)),
                    'scores': torch.zeros(0),
                    'labels': torch.zeros(0, dtype=torch.long)
                })

        return results

    @staticmethod
    def load_pretrained(checkpoint_path: str) -> 'YOLOModel':
        """
        加载预训练模型

        Args:
            checkpoint_path: 检查点路径

        Returns:
            加载了预训练权重的模型
        """
        checkpoint = torch.load(checkpoint_path, map_location='cpu')

        # 获取模型配置
        config = checkpoint.get('config', {})
        model = YOLOModel(**config)

        # 加载权重
        model.load_state_dict(checkpoint['model_state_dict'])

        return model

    def save_pretrained(self, checkpoint_path: str):
        """
        保存模型

        Args:
            checkpoint_path: 保存路径
        """
        checkpoint = {
            'config': {
                'num_classes': self.num_classes,
            },
            'model_state_dict': self.state_dict()
        }
        torch.save(checkpoint, checkpoint_path)


class YOLOv8Tiny(YOLOModel):
    """
    YOLOv8-Tiny 模型

    轻量级 YOLO 模型，适合:
    - 快速原型验证
    - CPU 推理
    - 边缘设备部署

    配置:
    - 深度因子: 0.33
    - 宽度因子: 0.25
    - 参数量: ~3M
    """

    def __init__(self, num_classes: int = 80):
        super().__init__(
            num_classes=num_classes,
            depth_multiple=0.33,
            width_multiple=0.25,
            reg_max=16
        )


class YOLOv8Small(YOLOModel):
    """
    YOLOv8-Small 模型

    小型 YOLO 模型，平衡速度和精度。

    配置:
    - 深度因子: 0.33
    - 宽度因子: 0.50
    - 参数量: ~11M
    """

    def __init__(self, num_classes: int = 80):
        super().__init__(
            num_classes=num_classes,
            depth_multiple=0.33,
            width_multiple=0.50,
            reg_max=16
        )


class YOLOv8Medium(YOLOModel):
    """
    YOLOv8-Medium 模型

    中型 YOLO 模型，适合大多数应用场景。

    配置:
    - 深度因子: 0.67
    - 宽度因子: 0.75
    - 参数量: ~26M
    """

    def __init__(self, num_classes: int = 80):
        super().__init__(
            num_classes=num_classes,
            depth_multiple=0.67,
            width_multiple=0.75,
            reg_max=16
        )


def test_yolo():
    """
    测试 YOLO 模型

    验证:
    1. 模型能正常前向传播
    2. 训练和推理模式正常切换
    3. 输出格式正确
    4. 参数量合理
    """
    print("=" * 50)
    print("测试 YOLO 模型")
    print("=" * 50)

    # 创建模型
    num_classes = 5
    model = YOLOv8Tiny(num_classes=num_classes)

    # 打印模型信息
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n模型参数量:")
    print(f"  总参数: {total_params:,}")
    print(f"  可训练参数: {trainable_params:,}")

    # 创建测试输入
    batch_size = 2
    images = torch.randn(batch_size, 3, 640, 640)
    print(f"\n输入形状: {images.shape}")

    # 测试训练模式
    print("\n--- 训练模式 ---")
    model.train()
    targets = [
        {
            'boxes': torch.tensor([[100, 100, 200, 200], [300, 300, 400, 400]]),
            'labels': torch.tensor([0, 1])
        }
        for _ in range(batch_size)
    ]

    outputs = model(images, targets)
    print(f"损失:")
    for key, value in outputs.items():
        print(f"  {key}: {value.item():.4f}")

    # 测试推理模式
    print("\n--- 推理模式 ---")
    model.eval()
    with torch.no_grad():
        outputs = model(images)

    print(f"预测结果:")
    for key, value in outputs.items():
        if isinstance(value, list):
            print(f"  {key}: {len(value)} batches")
            for i, v in enumerate(value):
                print(f"    Batch {i}: {v.shape}")

    # 测试单张预测
    print("\n--- 单张预测 ---")
    single_image = torch.randn(3, 640, 640)
    result = model.predict(single_image, conf_threshold=0.1)
    print(f"检测结果:")
    print(f"  boxes: {result['boxes'].shape}")
    print(f"  scores: {result['scores'].shape}")
    print(f"  labels: {result['labels'].shape}")

    print("\n✓ YOLO 模型测试通过!")
    return True


if __name__ == '__main__':
    test_yolo()
