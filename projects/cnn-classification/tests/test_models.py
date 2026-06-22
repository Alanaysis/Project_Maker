"""
CNN模型测试

测试LeNet-5、AlexNet、VGG模型的正确性
"""

import pytest
import torch
import sys
sys.path.insert(0, '.')

from src.lenet import LeNet5, LeNet5Custom, lenet5
from src.alexnet import AlexNet, AlexNetCIFAR, alexnet, alexnet_cifar
from src.vgg import VGG, VGGCIFAR, vgg11, vgg13, vgg16, vgg19, vgg_cifar


class TestLeNet5:
    """测试LeNet-5模型"""

    def test_lenet5_output_shape(self):
        """测试LeNet-5输出形状"""
        batch_size = 4
        num_classes = 10
        in_channels = 1
        height, width = 32, 32

        model = LeNet5(num_classes, in_channels)
        x = torch.randn(batch_size, in_channels, height, width)

        output = model(x)

        assert output.shape == (batch_size, num_classes)

    def test_lenet5_custom_output_shape(self):
        """测试自定义LeNet-5输出形状"""
        batch_size = 4
        num_classes = 10
        in_channels = 1
        height, width = 32, 32

        model = LeNet5Custom(num_classes, in_channels)
        x = torch.randn(batch_size, in_channels, height, width)

        output = model(x)

        assert output.shape == (batch_size, num_classes)

    def test_lenet5_factory(self):
        """测试LeNet-5工厂函数"""
        model = lenet5(num_classes=10)

        assert isinstance(model, LeNet5)
        assert model.fc3.out_features == 10

    def test_lenet5_gradient_flow(self):
        """测试LeNet-5梯度流"""
        model = LeNet5(10, 1)
        x = torch.randn(2, 1, 32, 32, requires_grad=True)

        output = model(x)
        loss = output.sum()
        loss.backward()

        # 检查所有参数都有梯度
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"No gradient for {name}"

    def test_lenet5_feature_maps(self):
        """测试LeNet-5特征图提取"""
        model = LeNet5(10, 1)
        x = torch.randn(2, 1, 32, 32)

        features = model.get_feature_maps(x)

        assert 'conv1' in features
        assert 'pool1' in features
        assert 'conv2' in features
        assert 'pool2' in features

        assert features['conv1'].shape == (2, 6, 28, 28)
        assert features['pool1'].shape == (2, 6, 14, 14)
        assert features['conv2'].shape == (2, 16, 10, 10)
        assert features['pool2'].shape == (2, 16, 5, 5)


class TestAlexNet:
    """测试AlexNet模型"""

    def test_alexnet_output_shape(self):
        """测试AlexNet输出形状"""
        batch_size = 4
        num_classes = 1000
        in_channels = 3
        height, width = 227, 227

        model = AlexNet(num_classes, in_channels)
        x = torch.randn(batch_size, in_channels, height, width)

        output = model(x)

        assert output.shape == (batch_size, num_classes)

    def test_alexnet_cifar_output_shape(self):
        """测试CIFAR版AlexNet输出形状"""
        batch_size = 4
        num_classes = 10
        in_channels = 3
        height, width = 32, 32

        model = AlexNetCIFAR(num_classes, in_channels)
        x = torch.randn(batch_size, in_channels, height, width)

        output = model(x)

        assert output.shape == (batch_size, num_classes)

    def test_alexnet_factory(self):
        """测试AlexNet工厂函数"""
        model = alexnet(num_classes=1000)

        assert isinstance(model, AlexNet)
        assert model.classifier[-1].out_features == 1000

    def test_alexnet_cifar_factory(self):
        """测试CIFAR版AlexNet工厂函数"""
        model = alexnet_cifar(num_classes=10)

        assert isinstance(model, AlexNetCIFAR)
        assert model.classifier[-1].out_features == 10

    def test_alexnet_gradient_flow(self):
        """测试AlexNet梯度流"""
        model = AlexNetCIFAR(10, 3)
        x = torch.randn(2, 3, 32, 32, requires_grad=True)

        output = model(x)
        loss = output.sum()
        loss.backward()

        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"No gradient for {name}"


class TestVGG:
    """测试VGG模型"""

    def test_vgg11_output_shape(self):
        """测试VGG-11输出形状"""
        batch_size = 4
        num_classes = 1000
        in_channels = 3
        height, width = 224, 224

        model = vgg11(num_classes, in_channels)
        x = torch.randn(batch_size, in_channels, height, width)

        output = model(x)

        assert output.shape == (batch_size, num_classes)

    def test_vgg16_output_shape(self):
        """测试VGG-16输出形状"""
        batch_size = 4
        num_classes = 1000
        in_channels = 3
        height, width = 224, 224

        model = vgg16(num_classes, in_channels)
        x = torch.randn(batch_size, in_channels, height, width)

        output = model(x)

        assert output.shape == (batch_size, num_classes)

    def test_vgg_cifar_output_shape(self):
        """测试CIFAR版VGG输出形状"""
        batch_size = 4
        num_classes = 10
        in_channels = 3
        height, width = 32, 32

        model = vgg_cifar('vgg16', num_classes, in_channels)
        x = torch.randn(batch_size, in_channels, height, width)

        output = model(x)

        assert output.shape == (batch_size, num_classes)

    def test_vgg_factory_functions(self):
        """测试VGG工厂函数"""
        model11 = vgg11()
        model13 = vgg13()
        model16 = vgg16()
        model19 = vgg19()

        assert isinstance(model11, VGG)
        assert isinstance(model13, VGG)
        assert isinstance(model16, VGG)
        assert isinstance(model19, VGG)

    def test_vgg_with_batch_norm(self):
        """测试带批归一化的VGG"""
        model = vgg16(batch_norm=True)

        # 检查是否有BatchNorm层
        has_batchnorm = any(isinstance(m, torch.nn.BatchNorm2d) for m in model.modules())
        assert has_batchnorm

    def test_vgg_gradient_flow(self):
        """测试VGG梯度流"""
        model = vgg_cifar('vgg11', 10, 3)
        x = torch.randn(2, 3, 32, 32, requires_grad=True)

        output = model(x)
        loss = output.sum()
        loss.backward()

        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"No gradient for {name}"


class TestModelIntegration:
    """集成测试"""

    def test_models_train_mode(self):
        """测试模型训练模式切换"""
        models = [
            LeNet5(10, 1),
            AlexNetCIFAR(10, 3),
            vgg_cifar('vgg11', 10, 3)
        ]

        for model in models:
            model.train()
            assert model.training

            model.eval()
            assert not model.training

    def test_models_parameter_count(self):
        """测试模型参数数量"""
        lenet = LeNet5(10, 1)
        alexnet_model = AlexNetCIFAR(10, 3)
        vgg_model = vgg_cifar('vgg11', 10, 3)

        # LeNet应该最少参数
        lenet_params = sum(p.numel() for p in lenet.parameters())
        alexnet_params = sum(p.numel() for p in alexnet_model.parameters())
        vgg_params = sum(p.numel() for p in vgg_model.parameters())

        assert lenet_params < alexnet_params < vgg_params

    def test_models_to_device(self):
        """测试模型设备迁移"""
        device = torch.device('cpu')
        model = LeNet5(10, 1).to(device)

        x = torch.randn(2, 1, 32, 32).to(device)
        output = model(x)

        assert output.device == device


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
