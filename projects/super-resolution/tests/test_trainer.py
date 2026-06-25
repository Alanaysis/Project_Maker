"""
超分辨率训练器测试

测试训练器的功能
"""

import pytest
import torch
import os
import sys
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.trainer import SRTrainer
from src.dataset import create_synthetic_dataset


class TestSRTrainer:
    """SRTrainer 测试"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建训练数据
            train_dir = os.path.join(tmpdir, 'train')
            create_synthetic_dataset(train_dir, num_images=10, image_size=64)

            # 创建验证数据
            val_dir = os.path.join(tmpdir, 'val')
            create_synthetic_dataset(val_dir, num_images=5, image_size=64)

            # 创建检查点目录
            checkpoint_dir = os.path.join(tmpdir, 'checkpoints')
            os.makedirs(checkpoint_dir)

            yield tmpdir, train_dir, val_dir, checkpoint_dir

    def test_init_srcnn(self, temp_dir):
        """测试 SRCNN 训练器初始化"""
        _, _, _, checkpoint_dir = temp_dir

        trainer = SRTrainer(
            model_name='srcnn',
            scale_factor=2,
            checkpoint_dir=checkpoint_dir
        )

        assert trainer.model_name == 'srcnn'
        assert trainer.scale_factor == 2

    def test_init_espcn(self, temp_dir):
        """测试 ESPCN 训练器初始化"""
        _, _, _, checkpoint_dir = temp_dir

        trainer = SRTrainer(
            model_name='espcn',
            scale_factor=2,
            checkpoint_dir=checkpoint_dir
        )

        assert trainer.model_name == 'espcn'
        assert trainer.scale_factor == 2

    def test_get_model_summary(self, temp_dir):
        """测试获取模型摘要"""
        _, _, _, checkpoint_dir = temp_dir

        trainer = SRTrainer(
            model_name='srcnn',
            scale_factor=2,
            checkpoint_dir=checkpoint_dir
        )

        summary = trainer.get_model_summary()

        assert 'Model: srcnn' in summary
        assert 'Scale Factor: 2x' in summary
        assert 'Total Parameters' in summary
        assert 'Trainable Parameters' in summary

    def test_train_srcnn(self, temp_dir):
        """测试训练 SRCNN 模型"""
        _, train_dir, val_dir, checkpoint_dir = temp_dir

        trainer = SRTrainer(
            model_name='srcnn',
            scale_factor=2,
            checkpoint_dir=checkpoint_dir
        )

        # 训练 2 个 epoch
        history = trainer.train(
            train_dir=train_dir,
            val_dir=val_dir,
            epochs=2,
            batch_size=2,
            patch_size=32,
            num_workers=0
        )

        # 检查训练历史
        assert 'train_loss' in history
        assert 'val_loss' in history
        assert 'learning_rate' in history
        assert len(history['train_loss']) == 2
        assert len(history['val_loss']) == 2

    def test_train_espcn(self, temp_dir):
        """测试训练 ESPCN 模型"""
        _, train_dir, val_dir, checkpoint_dir = temp_dir

        trainer = SRTrainer(
            model_name='espcn',
            scale_factor=2,
            checkpoint_dir=checkpoint_dir
        )

        # 训练 2 个 epoch
        history = trainer.train(
            train_dir=train_dir,
            val_dir=val_dir,
            epochs=2,
            batch_size=2,
            patch_size=32,
            num_workers=0
        )

        # 检查训练历史
        assert len(history['train_loss']) == 2

    def test_save_checkpoint(self, temp_dir):
        """测试保存检查点"""
        _, train_dir, _, checkpoint_dir = temp_dir

        trainer = SRTrainer(
            model_name='srcnn',
            scale_factor=2,
            checkpoint_dir=checkpoint_dir
        )

        # 训练 1 个 epoch
        trainer.train(
            train_dir=train_dir,
            epochs=1,
            batch_size=2,
            patch_size=32,
            num_workers=0
        )

        # 检查检查点文件
        assert os.path.exists(os.path.join(checkpoint_dir, 'latest.pth'))

    def test_load_checkpoint(self, temp_dir):
        """测试加载检查点"""
        _, train_dir, _, checkpoint_dir = temp_dir

        # 创建并训练模型
        trainer1 = SRTrainer(
            model_name='srcnn',
            scale_factor=2,
            checkpoint_dir=checkpoint_dir
        )

        trainer1.train(
            train_dir=train_dir,
            epochs=1,
            batch_size=2,
            patch_size=32,
            num_workers=0
        )

        # 创建新训练器并加载检查点
        trainer2 = SRTrainer(
            model_name='srcnn',
            scale_factor=2,
            checkpoint_dir=checkpoint_dir
        )

        checkpoint_path = os.path.join(checkpoint_dir, 'latest.pth')
        trainer2.load_checkpoint(checkpoint_path)

        # 检查模型参数是否相同
        for p1, p2 in zip(trainer1.model.parameters(), trainer2.model.parameters()):
            assert torch.allclose(p1, p2)

    def test_device_selection(self, temp_dir):
        """测试设备选择"""
        _, _, _, checkpoint_dir = temp_dir

        # 自动选择设备
        trainer_auto = SRTrainer(
            model_name='srcnn',
            checkpoint_dir=checkpoint_dir
        )

        # 手动选择 CPU
        trainer_cpu = SRTrainer(
            model_name='srcnn',
            device='cpu',
            checkpoint_dir=checkpoint_dir
        )

        assert trainer_auto.device in ['cuda', 'cpu']
        assert trainer_cpu.device == 'cpu'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
