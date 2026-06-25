# 04 - 测试策略

## 1. 测试目标

- 验证每个模块的功能正确性
- 确保模型前向传播的维度正确
- 验证帧采样策略的边界条件
- 测试数据集的合成数据模式
- 验证特征提取管道的完整性

## 2. 测试结构

```
tests/
├── __init__.py
├── conftest.py                 # pytest配置，添加src到sys.path
├── test_spatial_model.py       # 空间模型测试
├── test_temporal_model.py      # 时序模型测试
├── test_action_classifier.py   # 端到端分类器测试
├── test_frame_sampler.py       # 帧采样器测试
├── test_feature_extractor.py   # 特征提取器测试
└── test_video_dataset.py       # 视频数据集测试
```

## 3. 测试用例

### 3.1 空间模型测试 (test_spatial_model.py)

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_default_initialization | 默认初始化 | 骨干=resnet18, 特征维度=512 |
| test_resnet50_initialization | ResNet-50初始化 | 特征维度=2048 |
| test_custom_feature_dim | 自定义特征维度 | 投影层存在, 维度正确 |
| test_invalid_backbone | 无效骨干网络 | 抛出ValueError |
| test_forward_single_frame | 单帧前向传播 | 输出shape=(B, 512) |
| test_forward_video_clip | 视频片段前向传播 | 输出shape=(B, T, 512) |
| test_forward_with_projection | 带投影的前向传播 | 输出shape=(B, 256) |
| test_freeze_backbone | 冻结骨干网络 | 所有参数requires_grad=False |
| test_not_freeze_backbone | 不冻结骨干网络 | 存在可训练参数 |

### 3.2 时序模型测试 (test_temporal_model.py)

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_lstm_initialization | LSTM初始化 | 输出维度=hidden_dim |
| test_gru_initialization | GRU初始化 | 输出维度=hidden_dim |
| test_transformer_initialization | Transformer初始化 | 输出维度=input_dim |
| test_invalid_arch | 无效架构 | 抛出ValueError |
| test_lstm_forward | LSTM前向传播 | 输出shape正确 |
| test_gru_forward | GRU前向传播 | 输出shape正确 |
| test_transformer_forward | Transformer前向传播 | 输出shape正确 |
| test_bidirectional_lstm | 双向LSTM | 输出维度=hidden_dim*2 |
| test_with_lengths | 变长序列 | 支持pack_padded_sequence |
| test_dropout_applied | Dropout生效 | 训练模式下输出不同 |

### 3.3 动作分类器测试 (test_action_classifier.py)

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_initialization | 初始化 | num_classes正确 |
| test_forward | 前向传播 | 输出shape=(B, num_classes) |
| test_forward_with_lengths | 变长序列前向 | 支持lengths参数 |
| test_predict | 预测接口 | 返回top-k结果, 概率和为1 |
| test_different_backbones | 不同骨干 | 支持resnet18/34 |
| test_different_temporal_archs | 不同时序架构 | 支持lstm/gru/transformer |
| test_get_spatial_features | 提取空间特征 | 输出3D张量 |
| test_get_temporal_features | 提取时序特征 | 输出2D张量 |
| test_freeze_backbone | 冻结骨干 | 参数不可训练 |

### 3.4 帧采样器测试 (test_frame_sampler.py)

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_default_initialization | 默认参数 | num_frames=16, strategy=uniform |
| test_invalid_strategy | 无效策略 | 抛出ValueError |
| test_invalid_num_frames | 无效帧数 | 抛出ValueError |
| test_uniform_sample_short_video | 短视频均匀采样 | 返回所有帧 |
| test_uniform_sample_long_video | 长视频均匀采样 | 返回num_frames个索引 |
| test_random_sample_* | 随机采样 | 索引排序, 范围正确 |
| test_dense_sample | 密集采样 | 步长一致 |
| test_temporal_jitter_sample | 时序抖动采样 | 索引在有效范围 |
| test_zero_frames_error | 零帧错误 | 抛出ValueError |

### 3.5 特征提取器测试 (test_feature_extractor.py)

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_initialization | 初始化 | 模型存在 |
| test_extract_spatial | 空间特征提取 | 输出shape正确 |
| test_extract_temporal | 时序特征提取 | 输出shape正确 |
| test_extract_both | 完整特征提取 | 返回spatial和temporal |
| test_extract_with_lengths | 变长序列 | 支持lengths |
| test_save_load_features | 保存加载 | 特征一致 |
| test_load_nonexistent_file | 文件不存在 | 抛出FileNotFoundError |

### 3.6 视频数据集测试 (test_video_dataset.py)

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_synthetic_dataset | 合成数据集 | 长度和类别数正确 |
| test_synthetic_getitem | 获取样本 | 张量shape和标签范围 |
| test_synthetic_with_custom_sampler | 自定义采样器 | 帧数正确 |
| test_synthetic_class_names | 类别名称 | 名称列表正确 |
| test_invalid_data_root | 无效数据路径 | 抛出ValueError |
| test_synthetic_batch | 批量加载 | DataLoader正常工作 |

## 4. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_spatial_model.py -v

# 运行带覆盖率的测试
pytest tests/ -v --cov=action_recognition --cov-report=html

# 运行特定测试类
pytest tests/test_spatial_model.py::TestSpatialModel -v

# 运行特定测试方法
pytest tests/test_spatial_model.py::TestSpatialModel::test_default_initialization -v
```

## 5. 测试依赖

- pytest>=7.0.0
- pytest-cov>=4.0.0
- torch>=1.12.0
- torchvision>=0.13.0

## 6. 测试覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| models/spatial_model.py | >90% |
| models/temporal_model.py | >90% |
| models/action_classifier.py | >85% |
| data/frame_sampler.py | >95% |
| data/video_dataset.py | >80% |
| features/extractor.py | >85% |
| **整体** | **>85%** |
