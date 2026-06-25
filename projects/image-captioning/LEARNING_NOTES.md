# 学习笔记 - 图像描述生成

## 1. 核心概念

### 什么是图像描述？
图像描述（Image Captioning）是计算机视觉和自然语言处理的交叉任务，目标是自动为图像生成一段自然语言描述。它结合了：
- **图像理解**：识别图像中的物体、动作、场景
- **语言生成**：将视觉信息转化为流畅的文字

### 为什么重要？
- 帮助视障人士理解图像内容
- 图像检索和搜索优化
- 社交媒体自动标注
- 人机交互界面改进

## 2. 技术架构

### 编码器-解码器架构
```
图像 -> [CNN编码器] -> 特征向量 -> [LSTM解码器] -> 文字序列
```

**编码器 (Encoder)**：
- 使用预训练 CNN（如 ResNet）提取图像特征
- 移除最后的分类层，保留卷积特征图
- 特征图展平为序列，每个位置对应图像的一个区域

**解码器 (Decoder)**：
- 使用 LSTM 生成文字序列
- 每个时间步预测一个词
- 使用 Teacher Forcing 训练

### 注意力机制
注意力机制让解码器在生成每个词时能够"关注"图像的不同区域：

**Bahdanau (Additive) Attention**：
```
score = V * tanh(W_h * h_decoder + W_v * v_image)
attention_weights = softmax(score)
context = sum(attention_weights * v_image)
```

**Scaled Dot-Product Attention**：
```
score = Q * K^T / sqrt(d_k)
attention_weights = softmax(score)
context = attention_weights * V
```

## 3. 实现细节

### 数据流
1. 图像预处理：Resize、Normalize
2. CNN 编码：提取特征图 (batch, num_pixels, embed_dim)
3. LSTM 解码：
   - 初始化隐藏状态（从编码器特征平均值得到）
   - 逐时间步生成：嵌入 + 上下文 -> LSTM -> 注意力 -> 预测
4. 输出：词概率分布 (batch, seq_len, vocab_size)

### 关键技术点
- **Teacher Forcing**：训练时使用真实词作为下一步输入
- **门控机制**：选择性地使用上下文信息
- **梯度裁剪**：防止梯度爆炸
- **束搜索**：推理时保留多个候选序列

## 4. 学习收获

### 架构理解
- CNN 擅长提取空间特征，LSTM 擅长处理序列
- 注意力机制是连接视觉和语言的桥梁
- 门控机制帮助控制信息流

### 工程实践
- 模块化设计便于测试和维护
- 合成数据集便于快速验证
- 参数统计帮助理解模型复杂度

### 调试经验
- 张量维度检查是调试的关键
- 梯度流验证确保模型可训练
- 批量处理需要考虑序列长度对齐
