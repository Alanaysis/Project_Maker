# 04 - 测试文档：图像分割

## 1. 测试策略

### 1.1 测试层次

| 层次 | 测试文件 | 测试目标 |
|------|----------|----------|
| 单元测试 | test_blocks.py | DoubleConv, Down, Up 基础块 |
| 模块测试 | test_encoder.py | 编码器功能和形状 |
| 模块测试 | test_decoder.py | 解码器功能和形状 |
| 集成测试 | test_unet.py | 完整 U-Net 模型 |
| 功能测试 | test_loss.py | 损失函数正确性 |
| 功能测试 | test_dataset.py | 数据集、指标、训练器 |

### 1.2 测试覆盖

共 50+ 个测试用例，覆盖：
- 输出形状正确性
- 梯度流验证
- 边界情况处理
- 不同配置组合
- 数值正确性

## 2. 测试用例详解

### 2.1 构建块测试 (test_blocks.py)

**DoubleConv 测试**：
- `test_output_shape`：验证空间尺寸不变
- `test_batch_dimension`：验证批处理
- `test_custom_mid_channels`：验证自定义中间通道
- `test_no_batch_norm`：验证无 BN 模式
- `test_gradient_flow`：验证梯度可流过

**Down 测试**：
- `test_output_shape`：验证空间尺寸减半
- `test_spatial_reduction`：验证 2x 下采样
- `test_batch_handling`：验证批处理

**Up 测试**：
- `test_bilinear_upsampling`：验证双线性上采样
- `test_transpose_conv_upsampling`：验证转置卷积上采样
- `test_size_mismatch_padding`：验证奇数尺寸处理
- `test_gradient_flow`：验证跳跃连接梯度流

### 2.2 编码器测试 (test_encoder.py)

- `test_default_config_output_shapes`：验证 4 层编码器输出形状
- `test_two_level_encoder`：验证 2 层配置
- `test_three_level_encoder`：验证 3 层配置
- `test_single_channel_input`：验证灰度输入
- `test_batch_handling`：验证批处理
- `test_skip_channels_property`：验证通道属性
- `test_no_batch_norm`：验证无 BN 模式
- `test_gradient_flow`：验证梯度流

### 2.3 解码器测试 (test_decoder.py)

- `test_default_config_output_shape`：验证 4 层解码器输出形状
- `test_two_level_decoder`：验证 2 层配置
- `test_multi_class_output`：验证多类输出
- `test_bilinear_vs_transpose`：验证两种上采样方式
- `test_batch_handling`：验证批处理
- `test_no_batch_norm`：验证无 BN 模式
- `test_gradient_flow`：验证跳跃连接梯度流

### 2.4 U-Net 测试 (test_unet.py)

- `test_default_config_output_shape`：验证标准配置输出
- `test_small_input`：验证小尺寸输入
- `test_multi_class_output`：验证多类分割
- `test_grayscale_input`：验证灰度输入
- `test_batch_processing`：验证批处理
- `test_predict_method`：验证预测方法
- `test_predict_multiclass`：验证多类预测
- `test_count_parameters`：验证参数计数
- `test_gradient_flow`：验证端到端梯度流
- `test_bilinear_vs_transpose`：验证两种上采样
- `test_no_batch_norm`：验证无 BN 模式
- `test_deterministic_output`：验证确定性输出
- `test_repr`：验证字符串表示

### 2.5 损失函数测试 (test_loss.py)

**DiceLoss 测试**：
- `test_perfect_prediction`：完美预测损失接近 0
- `test_worst_prediction`：最差预测损失接近 1
- `test_output_range`：损失在 [0, 1] 范围
- `test_gradient_flow`：梯度可计算
- `test_smooth_factor`：平滑因子影响

**BCEDiceLoss 测试**：
- `test_output_scalar`：输出为标量
- `test_gradient_flow`：梯度可计算
- `test_weight_combination`：权重影响
- `test_equal_weights`：等权重组合
- `test_multiclass`：多类支持

### 2.6 数据集和训练测试 (test_dataset.py)

**SegmentationDataset 测试**：
- `test_numpy_input`：numpy 输入
- `test_tensor_input`：tensor 输入
- `test_getitem_returns_tensors`：返回 tensor
- `test_empty_dataset`：空数据集

**SyntheticDataset 测试**：
- `test_default_generation`：默认生成形状
- `test_custom_parameters`：自定义参数
- `test_reproducibility`：可重复性
- `test_mask_values`：掩码值范围
- `test_image_dtype`：图像数据类型

**Metrics 测试**：
- `test_perfect_iou`：完美 IoU
- `test_zero_iou`：零 IoU
- `test_perfect_dice`：完美 Dice
- `test_iou_range`：IoU 范围
- `test_dice_range`：Dice 范围

**Trainer 测试**：
- `test_train_epoch`：训练一个 epoch
- `test_validate`：验证功能
- `test_fit`：完整训练
- `test_fit_with_validation`：带验证的训练
- `test_training_reduces_loss`：训练降低损失

## 3. 测试运行

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_unet.py -v

# 运行特定测试类
pytest tests/test_unet.py::TestUNet -v

# 运行特定测试
pytest tests/test_unet.py::TestUNet::test_default_config_output_shape -v

# 显示详细输出
pytest tests/ -v --tb=short
```

## 4. 测试结果示例

```
tests/test_blocks.py::TestDoubleConv::test_output_shape PASSED
tests/test_blocks.py::TestDoubleConv::test_batch_dimension PASSED
tests/test_blocks.py::TestDoubleConv::test_custom_mid_channels PASSED
tests/test_blocks.py::TestDoubleConv::test_no_batch_norm PASSED
tests/test_blocks.py::TestDoubleConv::test_gradient_flow PASSED
tests/test_encoder.py::TestEncoder::test_default_config_output_shapes PASSED
tests/test_unet.py::TestUNet::test_default_config_output_shape PASSED
tests/test_unet.py::TestUNet::test_predict_method PASSED
tests/test_loss.py::TestDiceLoss::test_perfect_prediction PASSED
tests/test_dataset.py::TestTrainer::test_training_reduces_loss PASSED
```

## 5. 测试依赖

- pytest
- torch
- numpy

## 6. 未来测试扩展

- 性能基准测试
- 内存使用测试
- 与 PyTorch 官方实现对比
- 真实数据集集成测试
- 边界情况压力测试
