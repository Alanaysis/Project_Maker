# 05 - 开发指南

## 开发环境

### 依赖安装
```bash
pip install torch torchvision pillow numpy
```

### 目录结构
```
projects/image-captioning/
├── src/           # 源代码
├── tests/         # 测试文件
├── docs/          # 文档
├── examples/      # 示例
└── checkpoints/   # 模型检查点
```

## 开发流程

### 1. 添加新模块
1. 在 `src/` 创建新文件
2. 在 `src/__init__.py` 添加导出
3. 编写单元测试
4. 更新文档

### 2. 修改现有模块
1. 先运行现有测试确保基线通过
2. 进行修改
3. 运行测试验证
4. 更新相关文档

### 3. 提交代码
1. 确保所有测试通过
2. 检查代码风格
3. 更新 README（如有必要）

## 扩展指南

### 1. 添加新的注意力机制
```python
# 在 src/attention.py 中添加
class NewAttention(nn.Module):
    def __init__(self, encoder_dim, decoder_dim, attention_dim):
        super().__init__()
        # 初始化层

    def forward(self, encoder_out, decoder_hidden):
        # 计算注意力
        return context, attention_weights
```

然后在 `LSTMDecoder.__init__` 中添加：
```python
if attention_type == "new_type":
    self.attention = NewAttention(encoder_dim, hidden_dim, attention_dim)
```

### 2. 添加新的编码器骨干网络
```python
# 在 src/encoder.py 中添加
elif backbone == "efficientnet":
    efficientnet = models.efficientnet_b0(pretrained=pretrained)
    self.backbone = nn.Sequential(*list(efficientnet.children())[:-2])
    self.feature_dim = 1280
```

### 3. 添加新的解码策略
```python
# 在 src/decoder.py 中添加
def _nucleus_sampling(self, encoder_out, max_length, start_idx, end_idx, p=0.9):
    """核采样（Nucleus Sampling）"""
    # 实现核采样逻辑
```

## 性能优化

### 1. 混合精度训练
```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()
with autocast():
    predictions, _ = model(images, captions, lengths)
    loss = criterion(predictions, targets)

scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

### 2. 数据加载优化
```python
DataLoader(
    dataset,
    batch_size=32,
    num_workers=4,        # 多进程加载
    pin_memory=True,      # 锁页内存
    prefetch_factor=2,    # 预取
)
```

### 3. 模型优化
```python
# 梯度累积
for i, (images, captions, lengths) in enumerate(train_loader):
    predictions, _ = model(images, captions, lengths)
    loss = criterion(predictions, targets) / accumulation_steps
    loss.backward()

    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

## 常见问题

### 1. CUDA 内存不足
- 减小 batch_size
- 使用梯度累积
- 使用混合精度训练
- 减小模型尺寸

### 2. 训练不收敛
- 检查学习率（太大或太小）
- 检查数据预处理
- 检查损失函数
- 添加梯度裁剪

### 3. 生成质量差
- 增加训练数据
- 使用束搜索
- 调整温度参数
- 使用更大的模型

## 代码规范

### 命名规范
- 类名：PascalCase（如 `ImageCaptioningModel`）
- 函数名：snake_case（如 `forward`）
- 变量名：snake_case（如 `encoder_out`）
- 常量名：UPPER_CASE（如 `PAD_TOKEN`）

### 文档规范
- 每个模块有模块级文档字符串
- 每个类有类级文档字符串
- 每个函数有函数级文档字符串
- 使用类型注解

### 测试规范
- 每个测试函数独立
- 测试名称描述测试内容
- 使用 assert 验证结果
- 测试覆盖正常和边界情况
