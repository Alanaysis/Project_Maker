"""
VQA 主模型

整合图像编码器、文本编码器、融合模块和答案预测器。
"""

import torch
import torch.nn as nn
from typing import Optional, Dict, Tuple

from .image_encoder import ImageEncoder
from .text_encoder import TextEncoder, TransformerTextEncoder
from .fusion import FusionModule
from .answer_predictor import AnswerPredictor


class VQAModel(nn.Module):
    """
    视觉问答模型

    整合图像编码、文本编码、多模态融合和答案预测。

    Args:
        vocab_size: 词汇表大小
        num_answers: 答案数量
        image_backbone: 图像骨干网络
        text_encoder_type: 文本编码器类型 ('lstm', 'gru', 'transformer')
        fusion_type: 融合类型 ('concat', 'bilinear', 'attention', 'co_attention')
        embed_dim: 词嵌入维度
        image_feature_dim: 图像特征维度
        text_feature_dim: 文本特征维度
        fusion_dim: 融合特征维度
        hidden_dim: 隐藏层维度
        dropout: Dropout 比率
        pretrained_image: 是否使用预训练图像编码器
    """

    def __init__(
        self,
        vocab_size: int = 10000,
        num_answers: int = 1000,
        image_backbone: str = 'resnet18',
        text_encoder_type: str = 'lstm',
        fusion_type: str = 'concat',
        embed_dim: int = 300,
        image_feature_dim: int = 512,
        text_feature_dim: int = 512,
        fusion_dim: int = 1024,
        hidden_dim: int = 512,
        dropout: float = 0.1,
        pretrained_image: bool = False,
        **kwargs,
    ):
        super().__init__()

        self.vocab_size = vocab_size
        self.num_answers = num_answers

        # 图像编码器
        self.image_encoder = ImageEncoder(
            backbone=image_backbone,
            pretrained=pretrained_image,
            feature_dim=image_feature_dim,
            freeze_backbone=pretrained_image,
        )

        # 文本编码器
        if text_encoder_type in ['lstm', 'gru']:
            self.text_encoder = TextEncoder(
                vocab_size=vocab_size,
                embed_dim=embed_dim,
                hidden_dim=text_feature_dim,
                feature_dim=text_feature_dim,
                rnn_type=text_encoder_type,
                dropout=dropout,
            )
        elif text_encoder_type == 'transformer':
            self.text_encoder = TransformerTextEncoder(
                vocab_size=vocab_size,
                embed_dim=embed_dim,
                feature_dim=text_feature_dim,
                dropout=dropout,
                **kwargs,
            )
        else:
            raise ValueError(f"不支持的文本编码器类型: {text_encoder_type}")

        # 融合模块
        self.fusion = FusionModule(
            fusion_type=fusion_type,
            image_dim=image_feature_dim,
            text_dim=text_feature_dim,
            output_dim=fusion_dim,
            dropout=dropout,
        )

        # 答案预测器
        self.predictor = AnswerPredictor(
            input_dim=fusion_dim,
            num_answers=num_answers,
            hidden_dim=hidden_dim,
            dropout=dropout,
        )

        self.text_encoder_type = text_encoder_type
        self.fusion_type = fusion_type

    def forward(
        self,
        images: Optional[torch.Tensor] = None,
        question_ids: Optional[torch.Tensor] = None,
        image_features: Optional[torch.Tensor] = None,
        targets: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        前向传播

        Args:
            images: 图像张量 [batch_size, channels, height, width]（可选）
            question_ids: 问题 token IDs [batch_size, seq_len]
            image_features: 预提取的图像特征 [batch_size, image_dim]（可选）
            targets: 目标答案 [batch_size]（可选）

        Returns:
            包含预测结果和损失的字典
        """
        # 编码图像
        if image_features is None:
            if images is None:
                raise ValueError("必须提供 images 或 image_features")
            image_features = self.image_encoder(images)

        # 编码文本
        text_features = self.text_encoder(question_ids)

        # 多模态融合
        fused_features = self.fusion(image_features, text_features)

        # 答案预测
        outputs = self.predictor(fused_features, targets)

        # 添加中间特征（用于分析）
        outputs['image_features'] = image_features
        outputs['text_features'] = text_features
        outputs['fused_features'] = fused_features

        return outputs

    def predict(
        self,
        images: Optional[torch.Tensor] = None,
        question_ids: Optional[torch.Tensor] = None,
        image_features: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        预测答案

        Args:
            images: 图像张量（可选）
            question_ids: 问题 token IDs
            image_features: 预提取的图像特征（可选）

        Returns:
            (预测类别, 置信度)
        """
        self.eval()
        with torch.no_grad():
            outputs = self.forward(
                images=images,
                question_ids=question_ids,
                image_features=image_features,
            )
            predictions, confidence = self.predictor.predict(outputs['fused_features'])
        return predictions, confidence

    def get_model_info(self) -> Dict[str, any]:
        """获取模型信息"""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)

        return {
            'vocab_size': self.vocab_size,
            'num_answers': self.num_answers,
            'text_encoder_type': self.text_encoder_type,
            'fusion_type': self.fusion_type,
            'total_params': total_params,
            'trainable_params': trainable_params,
            'image_feature_dim': self.image_encoder.get_output_dim(),
            'text_feature_dim': self.text_encoder.get_output_dim(),
        }

    @classmethod
    def from_config(cls, config: Dict) -> 'VQAModel':
        """
        从配置字典创建模型

        Args:
            config: 配置字典

        Returns:
            VQA 模型实例
        """
        return cls(**config)


def create_default_model(
    vocab_size: int = 10000,
    num_answers: int = 1000,
) -> VQAModel:
    """
    创建默认 VQA 模型

    Args:
        vocab_size: 词汇表大小
        num_answers: 答案数量

    Returns:
        VQA 模型实例
    """
    return VQAModel(
        vocab_size=vocab_size,
        num_answers=num_answers,
        image_backbone='resnet18',
        text_encoder_type='lstm',
        fusion_type='concat',
        embed_dim=300,
        image_feature_dim=512,
        text_feature_dim=512,
        fusion_dim=1024,
        hidden_dim=512,
        dropout=0.1,
        pretrained_image=False,
    )
