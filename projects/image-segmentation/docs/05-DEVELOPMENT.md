# 05 - 开发文档：图像分割

## 1. 环境搭建

### 1.1 系统要求

- Python 3.8+
- PyTorch 1.10+
- NumPy 1.20+

### 1.2 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install torch numpy pytest
```

### 1.3 验证安装

```bash
python -c "import torch; print(f'PyTorch {torch.__version__}')"
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## 2. 开发工作流

### 2.1 项目结构

```
image-segmentation/
├── src/              # 源代码
├── tests/            # 测试代码
├── docs/             # 文档
├── README.md         # 项目说明
└── LEARNING_NOTES.md # 学习笔记
```

### 2.2 开发步骤

1. **阅读文档**：先阅读 01-RESEARCH.md 了解背景知识
2. **理解设计**：阅读 02-DESIGN.md 了解架构设计
3. **实现代码**：按模块顺序实现 blocks -> encoder -> decoder -> unet
4. **编写测试**：每个模块完成后编写对应测试
5. **运行测试**：确保所有测试通过
6. **迭代优化**：根据测试结果优化代码

### 2.3 代码规范

- 使用类型注解（Type Hints）
- 编写详细的 docstring
- 遵循 PEP 8 规范
- 每个函数/类都要有文档

## 3. 调试指南

### 3.1 常见问题

**问题 1：形状不匹配**

```
RuntimeError: The size of tensor a (64) must match the size of tensor b (128)
```

**原因**：编码器和解码器的通道数不匹配

**解决**：检查 skip_channels 配置是否正确

**问题 2：尺寸不匹配**

```
RuntimeError: The size of tensor a (32) must match the size of tensor b (33)
```

**原因**：输入尺寸不是 2 的幂，导致上采样后尺寸不匹配

**解决**：使用 Up 块中的 padding 处理，或确保输入尺寸是 2 的幂

**问题 3：内存不足**

```
RuntimeError: CUDA out of memory
```

**原因**：图像太大或 batch_size 太大

**解决**：
- 减小 batch_size
- 减小 base_channels
- 减小 n_levels
- 使用梯度检查点

### 3.2 调试技巧

```python
# 打印中间形状
class Encoder(nn.Module):
    def forward(self, x):
        skips = [self.inc(x)]
        print(f"inc: {skips[-1].shape}")
        for i, down in enumerate(self.down_blocks):
            skips.append(down(skips[-1]))
            print(f"down_{i}: {skips[-1].shape}")
        bottleneck = skips.pop()
        print(f"bottleneck: {bottleneck.shape}")
        return skips, bottleneck

# 检查参数
model = UNet()
for name, param in model.named_parameters():
    print(f"{name}: {param.shape}")

# 检查梯度
loss.backward()
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad_mean={param.grad.mean():.6f}")
```

## 4. 性能优化

### 4.1 模型优化

- **减少参数量**：减小 base_channels 或 n_levels
- **使用深度可分离卷积**：减少计算量
- **使用梯度检查点**：减少内存使用
- **混合精度训练**：加速训练

### 4.2 训练优化

- **数据加载**：使用多进程数据加载
- **批大小**：根据 GPU 内存调整
- **学习率**：使用学习率预热和余弦退火
- **梯度累积**：模拟大 batch_size

### 4.3 推理优化

- **模型量化**：INT8 量化
- **模型剪枝**：移除冗余参数
- **ONNX 导出**：跨平台部署
- **TensorRT**：GPU 推理加速

## 5. 扩展开发

### 5.1 添加注意力机制

```python
class AttentionBlock(nn.Module):
    def __init__(self, F_g, F_l, F_int):
        self.W_g = nn.Conv2d(F_g, F_int, 1)
        self.W_x = nn.Conv2d(F_l, F_int, 1)
        self.psi = nn.Conv2d(F_int, 1, 1)

    def forward(self, g, x):
        g1 = self.W_g(g)
        x1 = self.W_x(x)
        psi = torch.relu(g1 + x1)
        psi = torch.sigmoid(self.psi(psi))
        return x * psi
```

### 5.2 添加残差连接

```python
class ResidualDoubleConv(nn.Module):
    def forward(self, x):
        residual = x
        out = self.double_conv(x)
        return out + residual
```

### 5.3 支持预训练编码器

```python
class ResNetEncoder(nn.Module):
    def __init__(self, backbone='resnet34'):
        resnet = torchvision.models.resnet34(pretrained=True)
        self.layer0 = nn.Sequential(resnet.conv1, resnet.bn1, resnet.relu)
        self.layer1 = resnet.layer1
        self.layer2 = resnet.layer2
        self.layer3 = resnet.layer3
        self.layer4 = resnet.layer4
```

## 6. 部署指南

### 6.1 模型导出

```python
# 保存模型
torch.save(model.state_dict(), 'unet.pth')

# 加载模型
model = UNet()
model.load_state_dict(torch.load('unet.pth'))
model.eval()

# ONNX 导出
dummy_input = torch.randn(1, 3, 256, 256)
torch.onnx.export(model, dummy_input, 'unet.onnx')
```

### 6.2 推理脚本

```python
import torch
from PIL import Image
from torchvision import transforms

def predict_image(model, image_path, device='cpu'):
    # 加载图像
    image = Image.open(image_path).convert('RGB')

    # 预处理
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
    ])
    input_tensor = transform(image).unsqueeze(0).to(device)

    # 推理
    model.eval()
    with torch.no_grad():
        output = model(input_tensor)
        mask = torch.sigmoid(output) > 0.5

    return mask.squeeze().cpu().numpy()
```

## 7. 参考资源

### 7.1 官方文档

- [PyTorch 文档](https://pytorch.org/docs/stable/)
- [PyTorch 教程](https://pytorch.org/tutorials/)

### 7.2 学习资源

- [U-Net 论文](https://arxiv.org/abs/1505.04597)
- [PyTorch Segmentation Tutorial](https://pytorch.org/tutorials/intermediate/torchvision_tutorial.html)
- [Segmentation Models PyTorch](https://github.com/qubvel/segmentation_models.pytorch)

### 7.3 数据集

- [Cityscapes](https://www.cityscapes-dataset.com/)
- [PASCAL VOC](http://host.robots.ox.ac.uk/pascal/VOC/)
- [COCO](https://cocodataset.org/)
- [Medical Segmentation Decathlon](http://medicaldecathlon.com/)
