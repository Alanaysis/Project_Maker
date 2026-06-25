# 01 - 市场调研

## 图像描述技术概述

### 定义
图像描述（Image Captioning）是让计算机自动为图像生成自然语言描述的技术。它是计算机视觉（CV）和自然语言处理（NLP）的交叉领域。

### 发展历程

| 时期 | 方法 | 特点 |
|------|------|------|
| 早期 | 模板匹配 | 固定模板填充关键词 |
| 2015 | Show and Tell | 首次使用 CNN + RNN 架构 |
| 2015 | Show, Attend and Tell | 引入注意力机制 |
| 2017+ | Transformer | 自注意力机制，更长距离依赖 |
| 2021+ | CLIP + GPT | 大规模预训练模型 |

### 核心技术

#### 1. 编码器-解码器架构
```
图像 -> CNN编码器 -> 特征向量 -> RNN解码器 -> 文字序列
```
- **编码器**：使用 CNN（如 ResNet、VGG）提取图像特征
- **解码器**：使用 RNN（如 LSTM、GRU）生成文字序列

#### 2. 注意力机制
让解码器在生成每个词时关注图像的不同区域：
- **硬注意力**：选择单一区域（不可微）
- **软注意力**：加权平均所有区域（可微）

#### 3. 训练策略
- **Teacher Forcing**：训练时使用真实词作为下一步输入
- **Scheduled Sampling**：逐步从 Teacher Forcing 过渡到自由生成
- **强化学习**：直接优化评估指标（如 CIDEr）

### 评估指标

| 指标 | 全称 | 说明 |
|------|------|------|
| BLEU | Bilingual Evaluation Understudy | n-gram 精度 |
| METEOR | Metric for Evaluation of Translation with Explicit ORdering | 同义词匹配 |
| CIDEr | Consensus-based Image Description Evaluation | TF-IDF 加权 |
| ROUGE | Recall-Oriented Understudy for Gisting Evaluation | 召回率导向 |
| SPICE | Semantic Propositional Image Caption Evaluation | 语义命题匹配 |

### 典型数据集

| 数据集 | 规模 | 特点 |
|--------|------|------|
| Flickr8k | 8,000 图像 | 入门级，每图 5 个描述 |
| Flickr30k | 30,000 图像 | 中等规模 |
| MS COCO | 120,000 图像 | 大规模，最常用 |
| Visual Genome | 108,000 图像 | 密集描述 |

### 应用场景
1. **无障碍访问**：帮助视障人士理解图像
2. **图像检索**：基于文字搜索图像
3. **社交媒体**：自动为图片生成描述
4. **安防监控**：自动描述监控画面
5. **教育**：辅助图像理解

### 当前挑战
1. **长尾分布**：罕见物体和场景描述困难
2. **细粒度描述**：难以描述细节和关系
3. **幻觉问题**：生成图像中不存在的内容
4. **评估指标**：自动指标与人类判断不完全一致

### 参考文献
1. Vinyals et al., "Show and Tell: A Neural Image Caption Generator", 2015
2. Xu et al., "Show, Attend and Tell: Neural Image Caption Generation with Visual Attention", 2015
3. Anderson et al., "Bottom-Up and Top-Down Attention for Image Captioning", 2018
