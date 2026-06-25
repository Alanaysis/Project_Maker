# DETR 目标检测

## 项目简介

实现 DETR（DEtection TRansformer），理解 Transformer 目标检测的核心原理。

**一句话描述**：基于 Transformer 的端到端目标检测模型。

## 学习目标

- 理解 DETR 架构
- 掌握匈牙利匹配
- 学会集合预测

## 核心循环

```
图像 → CNN 骨干 → Transformer 编码器 → 解码器 → 匈牙利匹配 → 检测结果
```

## 技术栈

- **主语言**：Python
- **框架**：PyTorch
- **其他**：scipy（匈牙利算法）

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
python -m pytest tests/ -v
```

### 训练模型

```bash
python examples/train.py
```

### 推理示例

```bash
python examples/inference.py
```

## 项目结构

```
detr/
├── src/
│   ├── __init__.py          # 模块初始化
│   ├── backbone.py          # CNN骨干网络
│   ├── transformer.py       # Transformer
│   ├── matcher.py           # 匈牙利匹配
│   ├── loss.py              # 损失函数
│   ├── detr.py              # DETR主模型
│   ├── dataset.py           # 数据集
│   └── utils.py             # 工具函数
├── tests/                   # 测试文件
├── examples/                # 示例代码
├── docs/                    # 文档
├── README.md
└── requirements.txt
```

## 核心组件

### 1. CNN 骨干网络

使用 ResNet 提取图像特征：

```python
from src.backbone import build_backbone

backbone = build_backbone('resnet18', train_backbone=True)
```

### 2. Transformer

编码器-解码器架构：

```python
from src.transformer import build_transformer

transformer = build_transformer(hidden_dim=256, nhead=8, num_encoder_layers=6, num_decoder_layers=6)
```

### 3. 匈牙利匹配

将预测与真实标签进行最优匹配：

```python
from src.matcher import build_matcher

matcher = build_matcher(cost_class=1, cost_bbox=5, cost_giou=2)
```

### 4. 集合预测损失

端到端训练损失：

```python
from src.loss import SetCriterion

criterion = SetCriterion(num_classes, matcher, weight_dict, eos_coef=0.1, losses=['labels', 'boxes'])
```

### 5. DETR 模型

完整的 DETR 模型：

```python
from src.detr import build_detr

model = build_detr(num_classes=91, num_queries=100)
```

## 关键概念

### 1. 集合预测

DETR 将目标检测视为集合预测问题：
- 输入：图像
- 输出：一组检测结果（类别 + 边界框）
- 无需锚框和 NMS

### 2. 匈牙利匹配

使用匈牙利算法进行二分图匹配：
- 计算预测与真实标签的匹配代价
- 找到最优的一对一匹配
- 用于训练时的损失计算

### 3. Object Queries

可学习的查询向量：
- 数量固定（如 100 个）
- 每个查询负责检测一个对象
- 通过交叉注意力关注图像特征

## 文档

- [研究文档](docs/01-RESEARCH.md) - DETR 背景和原理
- [设计文档](docs/02-DESIGN.md) - 系统架构设计
- [实现文档](docs/03-IMPLEMENTATION.md) - 代码实现细节
- [测试文档](docs/04-TESTING.md) - 测试策略和用例
- [开发文档](docs/05-DEVELOPMENT.md) - 开发环境和流程
- [学习笔记](LEARNING_NOTES.md) - 学习心得和总结

## 参考资料

### 论文

- [End-to-End Object Detection with Transformers](https://arxiv.org/abs/2005.12872)
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)

### 代码

- [官方实现](https://github.com/facebookresearch/detr)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/model_doc/detr)

### 教程

- [DETR 详解](https://arxiv.org/abs/2005.12872)
- [PyTorch DETR Tutorial](https://pytorch.org/tutorials/intermediate/detr_tutorial.html)

## 许可证

本项目仅供学习使用。
