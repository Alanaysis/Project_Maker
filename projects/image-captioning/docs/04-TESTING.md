# 04 - 测试说明

## 测试策略

### 测试层次
1. **单元测试**：测试单个模块的功能
2. **集成测试**：测试模块间的协作
3. **端到端测试**：测试完整流程

### 测试覆盖
- 模块：encoder, attention, decoder, model, vocabulary, dataset
- 场景：正常输入、边界条件、异常处理
- 验证：输出形状、数值范围、梯度流

## 测试文件

### 1. test_encoder.py - CNN 编码器测试

**测试用例**：
- `test_output_shape_resnet18/34/50`：验证不同骨干网络的输出形状
- `test_num_pixels`：验证特征图像素数量
- `test_unsupported_backbone`：验证不支持的骨干网络抛出异常
- `test_gradient_flow`：验证梯度可以正常反向传播
- `test_single_image`：验证单张图像输入
- `test_batch_consistency`：验证批量处理的一致性

**运行**：
```bash
python tests/test_encoder.py
```

### 2. test_attention.py - 注意力机制测试

**测试用例**：
- `test_output_shape`：验证输出形状
- `test_attention_weights_sum_to_one`：验证权重之和为 1
- `test_attention_weights_non_negative`：验证权重非负
- `test_gradient_flow`：验证梯度反向传播
- `test_single_pixel`：验证单像素输入

**运行**：
```bash
python tests/test_attention.py
```

### 3. test_decoder.py - LSTM 解码器测试

**测试用例**：
- `test_training_forward_shape`：验证训练阶段输出形状
- `test_generate_greedy`：验证贪心生成
- `test_generate_beam_search`：验证束搜索生成
- `test_init_hidden_state`：验证隐藏状态初始化
- `test_gradient_flow`：验证梯度反向传播
- `test_scaled_dot_attention`：验证缩放点积注意力
- `test_generate_with_temperature`：验证温度参数影响

**运行**：
```bash
python tests/test_decoder.py
```

### 4. test_model.py - 完整模型测试

**测试用例**：
- `test_forward_shape`：验证前向传播输出形状
- `test_generate`：验证描述生成
- `test_count_parameters`：验证参数量统计
- `test_gradient_flow`：验证梯度反向传播
- `test_scaled_dot_attention`：验证缩放点积注意力
- `test_single_image`：验证单张图像输入
- `test_generate_with_beam_search`：验证束搜索生成

**运行**：
```bash
python tests/test_model.py
```

### 5. test_vocabulary.py - 词汇表测试

**测试用例**：
- `test_initial_special_tokens`：验证特殊标记初始化
- `test_build_from_captions`：验证从描述构建词汇表
- `test_encode_decode`：验证编码和解码
- `test_encode_with_max_length`：验证带最大长度的编码
- `test_unknown_word`：验证未知词处理
- `test_min_freq`：验证最小词频过滤
- `test_decode_skip_special`：验证解码时跳过特殊标记
- `test_encode_decode_roundtrip`：验证编码-解码往返一致性

**运行**：
```bash
python tests/test_vocabulary.py
```

### 6. test_dataset.py - 数据集测试

**测试用例**：
- `test_dataset_length`：验证数据集长度
- `test_getitem`：验证获取样本
- `test_collate_fn`：验证批量整理函数
- `test_caption_start_end`：验证描述包含 start 和 end 标记
- `test_collate_padding`：验证填充正确性

**运行**：
```bash
python tests/test_dataset.py
```

## 运行所有测试

```bash
cd projects/image-captioning
for test in tests/test_*.py; do
    echo "运行 $test..."
    python "$test"
    echo ""
done
```

## 测试结果解读

### 通过标准
- 所有断言（assert）通过
- 无运行时错误
- 梯度流正常

### 常见失败原因
1. **维度不匹配**：检查张量形状
2. **梯度为 None**：检查 requires_grad 设置
3. **数值溢出**：检查激活函数和损失函数
4. **索引越界**：检查词汇表大小

## 调试技巧

### 1. 逐步调试
```python
# 在测试中添加打印
print(f"输入形状: {input.shape}")
output = model(input)
print(f"输出形状: {output.shape}")
```

### 2. 梯度检查
```python
loss.backward()
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad norm = {param.grad.norm().item()}")
```

### 3. 数值检查
```python
print(f"输出范围: [{output.min().item()}, {output.max().item()}]")
print(f"输出均值: {output.mean().item()}")
```
