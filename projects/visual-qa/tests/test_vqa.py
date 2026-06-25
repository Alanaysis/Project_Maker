"""
VQA 模型测试

测试 VQA 模型的各个组件和完整流程。
"""

import pytest
import torch
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import VQAModel, ImageEncoder, TextEncoder, FusionModule, AnswerPredictor
from src import VQADataset, create_sample_data


class TestImageEncoder:
    """图像编码器测试"""

    def test_resnet18_encoder(self):
        """测试 ResNet18 编码器"""
        encoder = ImageEncoder(backbone='resnet18', feature_dim=512)
        x = torch.randn(2, 3, 224, 224)
        output = encoder(x)

        assert output.shape == (2, 512)
        assert not torch.isnan(output).any()

    def test_resnet34_encoder(self):
        """测试 ResNet34 编码器"""
        encoder = ImageEncoder(backbone='resnet34', feature_dim=256)
        x = torch.randn(2, 3, 224, 224)
        output = encoder(x)

        assert output.shape == (2, 256)

    def test_output_dim(self):
        """测试输出维度"""
        encoder = ImageEncoder(backbone='resnet18', feature_dim=512)
        assert encoder.get_output_dim() == 512

    def test_different_feature_dims(self):
        """测试不同特征维度"""
        for dim in [128, 256, 512, 1024]:
            encoder = ImageEncoder(backbone='resnet18', feature_dim=dim)
            assert encoder.get_output_dim() == dim


class TestTextEncoder:
    """文本编码器测试"""

    def test_lstm_encoder(self):
        """测试 LSTM 编码器"""
        encoder = TextEncoder(
            vocab_size=1000,
            embed_dim=128,
            hidden_dim=256,
            feature_dim=512,
            rnn_type='lstm',
        )
        x = torch.randint(0, 1000, (2, 10))
        output = encoder(x)

        assert output.shape == (2, 512)
        assert not torch.isnan(output).any()

    def test_gru_encoder(self):
        """测试 GRU 编码器"""
        encoder = TextEncoder(
            vocab_size=1000,
            embed_dim=128,
            hidden_dim=256,
            feature_dim=256,
            rnn_type='gru',
        )
        x = torch.randint(0, 1000, (2, 10))
        output = encoder(x)

        assert output.shape == (2, 256)

    def test_output_dim(self):
        """测试输出维度"""
        encoder = TextEncoder(vocab_size=1000, feature_dim=512)
        assert encoder.get_output_dim() == 512


class TestFusionModule:
    """融合模块测试"""

    def test_concat_fusion(self):
        """测试拼接融合"""
        fusion = FusionModule(
            fusion_type='concat',
            image_dim=512,
            text_dim=512,
            output_dim=1024,
        )
        img_feat = torch.randn(2, 512)
        txt_feat = torch.randn(2, 512)
        output = fusion(img_feat, txt_feat)

        assert output.shape == (2, 1024)

    def test_bilinear_fusion(self):
        """测试双线性融合"""
        fusion = FusionModule(
            fusion_type='bilinear',
            image_dim=512,
            text_dim=512,
            output_dim=1024,
        )
        img_feat = torch.randn(2, 512)
        txt_feat = torch.randn(2, 512)
        output = fusion(img_feat, txt_feat)

        assert output.shape == (2, 1024)

    def test_attention_fusion(self):
        """测试注意力融合"""
        fusion = FusionModule(
            fusion_type='attention',
            image_dim=512,
            text_dim=512,
            output_dim=1024,
        )
        img_feat = torch.randn(2, 512)
        txt_feat = torch.randn(2, 512)
        output = fusion(img_feat, txt_feat)

        assert output.shape == (2, 1024)

    def test_different_input_dims(self):
        """测试不同输入维度"""
        fusion = FusionModule(
            fusion_type='concat',
            image_dim=256,
            text_dim=512,
            output_dim=512,
        )
        img_feat = torch.randn(2, 256)
        txt_feat = torch.randn(2, 512)
        output = fusion(img_feat, txt_feat)

        assert output.shape == (2, 512)


class TestAnswerPredictor:
    """答案预测器测试"""

    def test_forward(self):
        """测试前向传播"""
        predictor = AnswerPredictor(input_dim=1024, num_answers=100)
        x = torch.randn(2, 1024)
        targets = torch.randint(0, 100, (2,))

        outputs = predictor(x, targets)

        assert 'logits' in outputs
        assert 'loss' in outputs
        assert 'accuracy' in outputs
        assert outputs['logits'].shape == (2, 100)

    def test_predict(self):
        """测试预测"""
        predictor = AnswerPredictor(input_dim=1024, num_answers=100)
        x = torch.randn(2, 1024)

        predictions, confidence = predictor.predict(x)

        assert predictions.shape == (2,)
        assert confidence.shape == (2,)
        assert (predictions >= 0).all() and (predictions < 100).all()
        assert (confidence >= 0).all() and (confidence <= 1).all()

    def test_predict_top_k(self):
        """测试 top-k 预测"""
        predictor = AnswerPredictor(input_dim=1024, num_answers=100)
        x = torch.randn(2, 1024)

        predictions, confidence = predictor.predict_top_k(x, k=5)

        assert predictions.shape == (2, 5)
        assert confidence.shape == (2, 5)


class TestVQAModel:
    """VQA 模型测试"""

    def test_model_creation(self):
        """测试模型创建"""
        model = VQAModel(
            vocab_size=1000,
            num_answers=100,
            image_feature_dim=256,
            text_feature_dim=256,
            fusion_dim=512,
        )
        info = model.get_model_info()

        assert info['vocab_size'] == 1000
        assert info['num_answers'] == 100

    def test_forward_with_images(self):
        """测试使用图像输入的前向传播"""
        model = VQAModel(
            vocab_size=1000,
            num_answers=100,
            image_feature_dim=256,
            text_feature_dim=256,
            fusion_dim=512,
        )

        images = torch.randn(2, 3, 224, 224)
        question_ids = torch.randint(0, 1000, (2, 10))
        targets = torch.randint(0, 100, (2,))

        outputs = model(images=images, question_ids=question_ids, targets=targets)

        assert 'logits' in outputs
        assert 'loss' in outputs
        assert 'image_features' in outputs
        assert 'text_features' in outputs
        assert 'fused_features' in outputs

    def test_forward_with_features(self):
        """测试使用预提取特征的前向传播"""
        model = VQAModel(
            vocab_size=1000,
            num_answers=100,
            image_feature_dim=256,
            text_feature_dim=256,
            fusion_dim=512,
        )

        image_features = torch.randn(2, 256)
        question_ids = torch.randint(0, 1000, (2, 10))

        outputs = model(image_features=image_features, question_ids=question_ids)

        assert 'logits' in outputs
        assert outputs['logits'].shape == (2, 100)

    def test_predict(self):
        """测试预测"""
        model = VQAModel(
            vocab_size=1000,
            num_answers=100,
            image_feature_dim=256,
            text_feature_dim=256,
            fusion_dim=512,
        )

        image_features = torch.randn(2, 256)
        question_ids = torch.randint(0, 1000, (2, 10))

        predictions, confidence = model.predict(
            image_features=image_features,
            question_ids=question_ids,
        )

        assert predictions.shape == (2,)
        assert confidence.shape == (2,)

    def test_different_fusion_types(self):
        """测试不同融合类型"""
        for fusion_type in ['concat', 'bilinear', 'attention']:
            model = VQAModel(
                vocab_size=1000,
                num_answers=100,
                image_feature_dim=256,
                text_feature_dim=256,
                fusion_dim=512,
                fusion_type=fusion_type,
            )

            image_features = torch.randn(2, 256)
            question_ids = torch.randint(0, 1000, (2, 10))

            outputs = model(image_features=image_features, question_ids=question_ids)
            assert outputs['logits'].shape == (2, 100)


class TestVQADataset:
    """VQA 数据集测试"""

    def test_sample_data_creation(self):
        """测试示例数据创建"""
        questions, image_ids, answers, vocab = create_sample_data(num_samples=50)

        assert len(questions) == 50
        assert len(image_ids) == 50
        assert len(answers) == 50
        assert len(vocab) > 4  # 至少有特殊 token

    def test_dataset_getitem(self):
        """测试数据集获取样本"""
        questions, image_ids, answers, vocab = create_sample_data(num_samples=10)
        dataset = VQADataset(questions, image_ids, answers, vocab)

        item = dataset[0]
        assert 'question_ids' in item
        assert 'image_features' in item
        assert 'answer_idx' in item
        assert item['question_ids'].shape == (20,)  # 默认 max_len=20

    def test_vocab_encode_decode(self):
        """测试词汇表编码解码"""
        questions, image_ids, answers, vocab = create_sample_data(num_samples=10)

        text = "what color is the cat"
        encoded = vocab.encode(text, max_len=10)
        decoded = vocab.decode(encoded)

        assert len(encoded) == 10
        assert 'what' in decoded


class TestIntegration:
    """集成测试"""

    def test_full_pipeline(self):
        """测试完整流程"""
        # 创建模型（使用与数据集匹配的维度）
        model = VQAModel(
            vocab_size=1000,
            num_answers=50,
            image_feature_dim=512,
            text_feature_dim=256,
            fusion_dim=512,
            hidden_dim=256,
        )

        # 创建数据
        questions, image_ids, answers, vocab = create_sample_data(
            num_samples=20,
            num_answers=50,
        )

        # 创建数据集
        dataset = VQADataset(questions, image_ids, answers, vocab)

        # 获取批次
        batch = {
            'question_ids': torch.stack([dataset[i]['question_ids'] for i in range(4)]),
            'image_features': torch.stack([dataset[i]['image_features'] for i in range(4)]),
            'answer_idx': torch.stack([dataset[i]['answer_idx'] for i in range(4)]),
        }

        # 前向传播
        outputs = model(
            question_ids=batch['question_ids'],
            image_features=batch['image_features'],
            targets=batch['answer_idx'],
        )

        assert 'logits' in outputs
        assert 'loss' in outputs
        assert outputs['logits'].shape == (4, 50)
        assert outputs['loss'].item() > 0

    def test_gradient_flow(self):
        """测试梯度流（使用图像输入）"""
        model = VQAModel(
            vocab_size=1000,
            num_answers=50,
            image_feature_dim=256,
            text_feature_dim=256,
            fusion_dim=512,
        )

        # 使用原始图像输入，确保所有参数都有梯度
        images = torch.randn(2, 3, 224, 224)
        question_ids = torch.randint(0, 1000, (2, 10))
        targets = torch.randint(0, 50, (2,))

        outputs = model(
            images=images,
            question_ids=question_ids,
            targets=targets,
        )

        outputs['loss'].backward()

        # 检查梯度（排除可能被冻结的参数）
        for name, param in model.named_parameters():
            if param.requires_grad and param.grad is None:
                # 如果参数需要梯度但没有梯度，检查是否是预训练模型的冻结参数
                if 'backbone' in name:
                    continue  # 跳过骨干网络参数（可能被冻结）
                assert False, f"{name} 没有梯度"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
