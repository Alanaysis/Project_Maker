# 04 - 测试文档：Vision Transformer

## 1. 测试策略

### 1.1 测试层次

| 层次 | 测试内容 | 测试文件 |
|------|----------|----------|
| 单元测试 | 各模块的输入输出形状、梯度传播 | `test_patch_embedding.py`, `test_attention.py`, `test_transformer.py` |
| 集成测试 | 完整模型的端到端功能 | `test_vit.py` |
| 功能测试 | 训练流程、推理流程 | `test_vit.py` |

### 1.2 测试原则

1. **形状验证**：每个模块的输出形状必须正确
2. **梯度验证**：所有可训练参数必须有梯度
3. **数值验证**：注意力权重必须归一化（和为 1）
4. **独立性验证**：批次中的样本必须独立

## 2. 测试用例详情

### 2.1 Patch Embedding 测试

```
test_output_shape_default     - 默认参数 (224x224, 16x16 patch)
test_output_shape_small       - 小图像 (28x28, 7x7 patch)
test_num_patches              - patch 数量计算
test_cls_token_in_output      - CLS token 是否正确添加
test_position_embedding_shape - 位置编码形状
test_cls_token_shape          - CLS token 形状
test_batch_independence       - 批次独立性
test_gradient_flow            - 梯度传播
test_invalid_image_size       - 非法输入处理
test_single_channel           - 灰度图像
test_different_patch_sizes    - 不同 patch 大小
test_projection_is_conv2d     - 投影层类型
```

### 2.2 Multi-Head Self-Attention 测试

```
test_output_shape                - 输出形状
test_output_shape_different_heads - 不同头数
test_attention_weights_sum_to_one - 注意力权重归一化
test_attention_weights_non_negative - 注意力权重非负
test_gradient_flow               - 梯度传播
test_head_dimension              - 头维度计算
test_scale_factor                - 缩放因子
test_embed_dim_divisible_by_heads - 维度整除检查
test_batch_independence          - 批次独立性
```

### 2.3 Transformer Encoder 测试

```
test_output_shape          - 输出形状
test_depth                 - 层数
test_final_norm            - 最终 LayerNorm
test_gradient_flow         - 梯度传播
test_different_depths      - 不同深度
```

### 2.4 VisionTransformer 测试

```
test_output_shape_default      - 默认配置
test_output_shape_small        - 小模型
test_vit_tiny_factory          - 工厂方法
test_vit_small_factory         - 工厂方法
test_attention_weights_return  - 注意力权重返回
test_get_attention_maps        - 注意力图获取
test_gradient_flow             - 梯度传播
test_parameter_count           - 参数量
test_tiny_model_parameter_count - Tiny 参数量
test_batch_independence        - 批次独立性
test_training_mode             - 训练模式切换
test_end_to_end_backward       - 端到端反向传播
test_representation_size       - 带隐藏层的分类头
test_different_num_classes     - 不同类别数
```

## 3. 测试运行

### 3.1 运行所有测试

```bash
cd projects/vit
pytest tests/ -v
```

### 3.2 运行特定测试文件

```bash
pytest tests/test_patch_embedding.py -v
pytest tests/test_attention.py -v
pytest tests/test_vit.py -v
```

### 3.3 运行特定测试类

```bash
pytest tests/test_vit.py::TestVisionTransformer -v
```

### 3.4 运行特定测试

```bash
pytest tests/test_vit.py::TestVisionTransformer::test_output_shape_default -v
```

## 4. 测试覆盖

### 4.1 覆盖率目标

| 模块 | 目标覆盖率 | 实际覆盖率 |
|------|-----------|-----------|
| patch_embedding.py | 100% | ~95% |
| attention.py | 100% | ~90% |
| transformer.py | 100% | ~90% |
| vit.py | 100% | ~85% |

### 4.2 未覆盖的功能

- `trainer.py`：需要真实数据集，不纳入单元测试
- `visualization.py`：可视化功能，手动验证

## 5. 边界情况

### 5.1 输入验证

- 图像尺寸必须能被 patch_size 整除
- embed_dim 必须能被 num_heads 整除
- batch_size 可以为任意正整数

### 5.2 数值稳定性

- 注意力权重使用 float32 精度
- softmax 使用数值稳定的实现
- 梯度裁剪防止梯度爆炸

### 5.3 边界值

- batch_size = 1
- num_patches = 1 (最小情况)
- num_heads = 1 (单头注意力)

## 6. 性能测试

### 6.1 推理时间基准

在 CPU 上的推理时间（单个样本）：

| 模型 | 输入尺寸 | 参数量 | 推理时间 |
|------|----------|--------|----------|
| ViT-Tiny | 224x224 | ~5.7M | ~50ms |
| ViT-Small | 224x224 | ~22M | ~200ms |
| ViT-Base | 224x224 | ~86M | ~800ms |

### 6.2 内存使用

| 模型 | 参数内存 | 激活内存 | 总内存 |
|------|----------|----------|--------|
| ViT-Tiny | ~23MB | ~100MB | ~150MB |
| ViT-Small | ~88MB | ~400MB | ~600MB |
| ViT-Base | ~344MB | ~1.5GB | ~2GB |

## 7. 持续集成

### 7.1 CI 流程

1. 代码提交触发测试
2. 运行所有单元测试
3. 检查测试覆盖率
4. 报告测试结果

### 7.2 测试环境

- Python 3.8+
- PyTorch 1.12+
- pytest 7.0+
