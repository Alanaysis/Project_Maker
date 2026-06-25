# 04 - 测试文档

## 1. 测试策略

### 1.1 测试层次

| 层次 | 范围 | 工具 |
|------|------|------|
| 单元测试 | 单个函数/类 | pytest |
| 集成测试 | 模块间交互 | pytest |
| 端到端测试 | 完整流程 | pytest + 合成数据 |

### 1.2 测试原则

1. **独立性**：每个测试用例独立运行
2. **可重复**：使用固定种子保证结果一致
3. **快速**：使用小尺寸数据加速测试
4. **全面**：覆盖正常和异常情况

## 2. 测试配置

### 2.1 共享 Fixtures

```python
# conftest.py

@pytest.fixture
def sample_frames():
    """生成合成视频帧 (T, C, H, W)"""
    return torch.randn(8, 3, 224, 224)

@pytest.fixture
def sample_frames_batch():
    """生成 batch 视频帧 (B, T, C, H, W)"""
    return torch.randn(2, 8, 3, 224, 224)

@pytest.fixture
def sample_numpy_frames():
    """生成合成 numpy 帧列表"""
    return [np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8) for _ in range(10)]

@pytest.fixture
def small_frames():
    """小尺寸帧，用于快速测试"""
    return torch.randn(4, 3, 64, 64)
```

**设计决策**：
- 使用 `torch.randn` 生成随机张量，快速且无需真实数据
- 提供单视频和 batch 两种 fixtures
- 提供 numpy 和 torch 两种格式
- `small_frames` 用于性能敏感的测试

## 3. 单元测试

### 3.1 FrameSampler 测试

```python
class TestFrameSampler:
    def test_uniform_sample(self):
        sampler = FrameSampler(num_frames=5, method="uniform")
        indices = sampler.sample(100)
        assert len(indices) == 5
        assert indices[0] == 0
        assert indices[-1] == 99

    def test_random_reproducibility(self):
        sampler1 = FrameSampler(num_frames=5, method="random", seed=42)
        sampler2 = FrameSampler(num_frames=5, method="random", seed=42)
        assert np.array_equal(sampler1.sample(100), sampler2.sample(100))

    def test_zero_frames(self):
        sampler = FrameSampler(num_frames=5, method="uniform")
        indices = sampler.sample(0)
        assert len(indices) == 0

    def test_invalid_method(self):
        sampler = FrameSampler(method="invalid")
        with pytest.raises(ValueError):
            sampler.sample(100)
```

**测试覆盖**：
- 正常采样（均匀、随机、密集）
- 边界情况（0帧、1帧、超过总帧数）
- 错误处理（无效方法）
- 可重复性（固定种子）

### 3.2 VideoFeatureExtractor 测试

```python
class TestVideoFeatureExtractor:
    def test_forward_single_video(self, sample_frames):
        extractor = VideoFeatureExtractor(backbone="resnet18", pretrained=False)
        output = extractor(sample_frames)
        assert output.shape == (512,)

    def test_forward_batch(self, sample_frames_batch):
        extractor = VideoFeatureExtractor(backbone="resnet18", pretrained=False)
        output = extractor(sample_frames_batch)
        assert output.shape == (2, 512)

    def test_temporal_pool_attention(self, sample_frames):
        extractor = VideoFeatureExtractor(backbone="resnet18", pretrained=False, pooling="attention")
        features = extractor.extract_frame_features(sample_frames)
        pooled = extractor.temporal_pool(features)
        assert pooled.shape == (512,)

    def test_invalid_backbone(self):
        with pytest.raises(ValueError):
            VideoFeatureExtractor(backbone="invalid_net")
```

**测试覆盖**：
- 不同骨干网络（resnet18, resnet34, resnet50）
- 不同池化方式（mean, max, attention）
- 单视频和 batch 输入
- 自定义特征维度
- 错误处理（无效骨干网络）

### 3.3 VideoContentClassifier 测试

```python
class TestVideoContentClassifier:
    def test_predict(self, sample_frames):
        classifier = VideoContentClassifier(num_classes=10, pretrained=False)
        results = classifier.predict(sample_frames, top_k=5)
        assert len(results) == 1
        assert "predicted_class" in results[0]
        assert "confidence" in results[0]
        assert len(results[0]["top_classes"]) == 5

    def test_predict_probabilities_sum_to_one(self, sample_frames):
        classifier = VideoContentClassifier(num_classes=10, pretrained=False)
        results = classifier.predict(sample_frames, top_k=10)
        prob_sum = sum(results[0]["top_probs"])
        assert abs(prob_sum - 1.0) < 0.01
```

**测试覆盖**：
- 前向传播形状
- 预测结果格式
- 概率归一化
- 特征提取
- batch 预测

### 3.4 VideoSummarizer 测试

```python
class TestVideoSummarizer:
    def test_compute_importance_scores(self, sample_frames):
        summarizer = VideoSummarizer(num_keyframes=3)
        scores = summarizer.compute_importance_scores(sample_frames)
        assert scores.shape == (8,)
        assert (scores >= 0).all()
        assert (scores <= 1).all()

    def test_generate_summary(self, sample_frames):
        summarizer = VideoSummarizer(num_keyframes=3)
        summary = summarizer.generate_summary(sample_frames)
        assert "num_frames" in summary
        assert "keyframe_indices" in summary
        assert summary["num_frames"] == 8

    def test_keyframes_less_than_total(self, small_frames):
        summarizer = VideoSummarizer(num_keyframes=10)
        indices, scores = summarizer.extract_keyframes(small_frames)
        assert len(indices) <= 4
```

**测试覆盖**：
- 重要性分数范围 [0, 1]
- 关键帧索引有序
- 关键帧数不超过总帧数
- 摘要结果完整性
- 场景变化检测

### 3.5 KeyframeExtractor 测试

```python
class TestKeyframeExtractor:
    @pytest.fixture
    def color_frames(self):
        colors = [(255,0,0), (0,255,0), (0,0,255), ...]
        return [np.full((100,100,3), c, dtype=np.uint8) for c in colors]

    def test_histogram_extraction(self, color_frames):
        extractor = KeyframeExtractor(method="histogram", max_keyframes=4)
        indices, scores = extractor.extract(color_frames)
        assert len(indices) <= 4
        assert all(indices[i] <= indices[i+1] for i in range(len(indices)-1))

    def test_clustering_extraction(self, color_frames):
        extractor = KeyframeExtractor(method="clustering", max_keyframes=3)
        indices, scores = extractor.extract(color_frames)
        assert len(indices) <= 3
```

**测试覆盖**：
- 四种提取方法
- 空帧列表
- 单帧输入
- 相似帧处理
- 最大关键帧数限制

### 3.6 ContentAnalyzer 测试

```python
class TestContentAnalyzer:
    def test_analyze_frames(self, sample_frames):
        analyzer = ContentAnalyzer(num_classes=10, num_frames=8)
        results = analyzer.analyze_frames(sample_frames)
        assert "video_feature" in results
        assert "predictions" in results
        assert "keyframe_indices" in results

    def test_compute_frame_similarity(self, sample_frames):
        analyzer = ContentAnalyzer()
        similarity = analyzer.compute_frame_similarity(sample_frames)
        assert similarity.shape == (8, 8)
        for i in range(8):
            assert abs(similarity[i, i] - 1.0) < 0.01

    def test_detect_segments(self, sample_frames):
        analyzer = ContentAnalyzer()
        segments = analyzer.detect_segments(sample_frames)
        assert len(segments) >= 1
        for start, end in segments:
            assert start <= end
```

**测试覆盖**：
- 完整分析流程
- 帧间相似度（对角线为 1）
- 片段检测
- numpy 帧输入

### 3.7 VideoDataset 测试

```python
class TestSyntheticVideoDataset:
    def test_getitem(self):
        dataset = SyntheticVideoDataset(num_samples=10, num_frames=8, num_classes=5)
        frames, label = dataset[0]
        assert frames.shape == (8, 3, 224, 224)
        assert 0 <= label < 5

    def test_reproducibility(self):
        ds1 = SyntheticVideoDataset(num_samples=5, seed=42)
        ds2 = SyntheticVideoDataset(num_samples=5, seed=42)
        _, label1 = ds1[0]
        _, label2 = ds2[0]
        assert label1 == label2

class TestVideoDataset:
    def test_init_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset = VideoDataset(tmpdir)
            assert len(dataset) == 0
```

**测试覆盖**：
- 合成数据集生成
- 真实数据集加载（空目录、不存在目录）
- 可重复性
- 不同尺寸

## 4. 运行测试

### 4.1 运行所有测试

```bash
cd projects/video-understanding
python -m pytest tests/ -v
```

### 4.2 运行特定测试

```bash
# 运行特定文件
python -m pytest tests/test_feature_extractor.py -v

# 运行特定类
python -m pytest tests/test_feature_extractor.py::TestVideoFeatureExtractor -v

# 运行特定方法
python -m pytest tests/test_feature_extractor.py::TestVideoFeatureExtractor::test_forward_single_video -v
```

### 4.3 生成覆盖率报告

```bash
python -m pytest tests/ --cov=video_understanding --cov-report=html
```

## 5. 测试结果示例

```
tests/test_frame_sampler.py::TestFrameSampler::test_init PASSED
tests/test_frame_sampler.py::TestFrameSampler::test_uniform_sample PASSED
tests/test_frame_sampler.py::TestFrameSampler::test_random_sample PASSED
tests/test_frame_sampler.py::TestFrameSampler::test_dense_sample PASSED
tests/test_frame_sampler.py::TestFrameSampler::test_sample_more_than_available PASSED
tests/test_frame_sampler.py::TestFrameSampler::test_zero_frames PASSED
tests/test_frame_sampler.py::TestFrameSampler::test_single_frame PASSED
tests/test_frame_sampler.py::TestFrameSampler::test_invalid_method PASSED
tests/test_frame_sampler.py::TestFrameSampler::test_sample_with_scores PASSED
tests/test_frame_sampler.py::TestFrameSampler::test_random_reproducibility PASSED
tests/test_frame_sampler.py::TestFrameSampler::test_repr PASSED

tests/test_feature_extractor.py::TestVideoFeatureExtractor::test_init_resnet18 PASSED
tests/test_feature_extractor.py::TestVideoFeatureExtractor::test_init_resnet50 PASSED
tests/test_feature_extractor.py::TestVideoFeatureExtractor::test_invalid_backbone PASSED
tests/test_feature_extractor.py::TestVideoFeatureExtractor::test_forward_single_video PASSED
tests/test_feature_extractor.py::TestVideoFeatureExtractor::test_forward_batch PASSED
...

======================== 70 passed in 45.23s ========================
```

## 6. 测试最佳实践

1. **使用 fixtures**：共享测试数据，减少重复代码
2. **测试边界**：覆盖空输入、单元素、超大输入等情况
3. **测试异常**：验证错误处理是否正确
4. **使用 pytest.raises**：测试异常抛出
5. **保持独立**：每个测试用例不依赖其他测试
