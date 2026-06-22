"""
CNN Classification - 图像分类卷积神经网络

实现经典CNN架构：LeNet-5、AlexNet、VGG
用于MNIST图像分类任务
"""

from .layers import Conv2D, MaxPool2D, Flatten
from .lenet import LeNet5, LeNet5Custom, lenet5
from .alexnet import AlexNet, AlexNetCIFAR, alexnet, alexnet_cifar
from .vgg import VGG, VGGCIFAR, vgg11, vgg13, vgg16, vgg19, vgg_cifar
from .trainer import Trainer
from .dataset import get_mnist_dataloaders, get_cifar10_dataloaders

__all__ = [
    'Conv2D', 'MaxPool2D', 'Flatten',
    'LeNet5', 'LeNet5Custom', 'lenet5',
    'AlexNet', 'AlexNetCIFAR', 'alexnet', 'alexnet_cifar',
    'VGG', 'VGGCIFAR', 'vgg11', 'vgg13', 'vgg16', 'vgg19', 'vgg_cifar',
    'Trainer',
    'get_mnist_dataloaders', 'get_cifar10_dataloaders'
]
