# 04 - 测试文档

## 测试策略

### 测试层次

1. **单元测试**: 测试单个函数和类
2. **集成测试**: 测试模块间的交互
3. **系统测试**: 测试完整的检测流程
4. **性能测试**: 测试推理速度和内存占用

### 测试覆盖

- 点云处理模块
- 模型模块
- 可视化模块
- 数据加载模块
- 后处理模块

## 单元测试

### 1. 点云处理测试

```python
# tests/test_point_cloud.py

import pytest
import numpy as np
import sys
sys.path.append('..')

from src.data.point_cloud import PointCloud


class TestPointCloud:
    """点云类测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.points = np.random.rand(1000, 4).astype(np.float32)
        self.pc = PointCloud(self.points)
    
    def test_init(self):
        """测试初始化"""
        assert self.pc.points.shape == (1000, 4)
        assert self.pc.points.dtype == np.float32
    
    def test_filter_by_range(self):
        """测试范围过滤"""
        x_range = (-10, 10)
        y_range = (-10, 10)
        z_range = (-3, 1)
        
        filtered = self.pc.filter_by_range(x_range, y_range, z_range)
        
        # 验证过滤后的点在范围内
        assert np.all(filtered.points[:, 0] >= x_range[0])
        assert np.all(filtered.points[:, 0] <= x_range[1])
        assert np.all(filtered.points[:, 1] >= y_range[0])
        assert np.all(filtered.points[:, 1] <= y_range[1])
    
    def test_downsample(self):
        """测试降采样"""
        voxel_size = 0.1
        downsampled = self.pc.downsample(voxel_size)
        
        # 验证降采样后点数减少
        assert downsampled.points.shape[0] <= self.pc.points.shape[0]
    
    def test_remove_ground(self):
        """测试地面点去除"""
        # 创建包含地面点的点云
        ground_points = np.random.rand(100, 4)
        ground_points[:, 2] = -1.5  # 地面高度
        
        object_points = np.random.rand(100, 4)
        object_points[:, 2] = 0.5  # 物体高度
        
        all_points = np.vstack([ground_points, object_points])
        pc = PointCloud(all_points)
        
        non_ground = pc.remove_ground()
        
        # 验证地面点被去除
        assert non_ground.points.shape[0] < all_points.shape[0]
```

### 2. 模型测试

```python
# tests/test_model.py

import pytest
import torch
import sys
sys.path.append('..')

from src.models.pointpillars import PointPillars
from src.models.backbone import Backbone2D


class TestPointPillars:
    """PointPillars 模型测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.model = PointPillars(
            voxel_size=[0.16, 0.16, 4],
            point_cloud_range=[-40, -40, -3, 40, 40, 1],
            num_classes=3
        )
    
    def test_model_init(self):
        """测试模型初始化"""
        assert self.model is not None
        assert isinstance(self.model, PointPillars)
    
    def test_forward(self):
        """测试前向传播"""
        # 创建模拟输入
        batch_size = 2
        num_points = 1000
        points = torch.randn(batch_size, num_points, 4)
        
        # 前向传播
        output = self.model(points)
        
        # 验证输出形状
        assert 'cls_score' in output
        assert 'bbox_pred' in output
        assert 'dir_pred' in output
    
    def test_parameters(self):
        """测试模型参数"""
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(
            p.numel() for p in self.model.parameters() if p.requires_grad
        )
        
        # 验证参数数量合理
        assert total_params > 0
        assert trainable_params > 0


class TestBackbone2D:
    """2D 骨干网络测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.backbone = Backbone2D(in_channels=64)
    
    def test_forward(self):
        """测试前向传播"""
        # 创建模拟输入
        x = torch.randn(2, 64, 200, 176)
        
        # 前向传播
        outputs = self.backbone(x)
        
        # 验证输出
        assert len(outputs) == 3  # 三个尺度的特征图
        
        # 验证特征图尺寸
        assert outputs[0].shape[1] == 64
        assert outputs[1].shape[1] == 128
        assert outputs[2].shape[1] == 256
```

### 3. 可视化测试

```python
# tests/test_visualization.py

import pytest
import numpy as np
import sys
sys.path.append('..')

from src.utils.visualization import Visualizer


class TestVisualizer:
    """可视化工具测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.visualizer = Visualizer()
    
    def test_visualize_point_cloud(self):
        """测试点云可视化"""
        # 创建模拟点云
        points = np.random.rand(1000, 3).astype(np.float32)
        
        # 测试可视化函数是否能正常调用
        # 注意：这里只测试函数是否能正常运行，不测试可视化效果
        try:
            self.visualizer.visualize_point_cloud(
                points,
                point_size=2.0,
                background_color=[0, 0, 0]
            )
        except Exception as e:
            pytest.fail(f"可视化点云失败: {e}")
    
    def test_visualize_boxes3d(self):
        """测试 3D 边界框可视化"""
        # 创建模拟边界框
        boxes = np.random.rand(10, 7).astype(np.float32)
        
        try:
            self.visualizer.visualize_boxes3d(
                boxes,
                color=(0, 1, 0),
                line_width=2
            )
        except Exception as e:
            pytest.fail(f"可视化 3D 边界框失败: {e}")
    
    def test_visualize_bev(self):
        """测试鸟瞰图可视化"""
        # 创建模拟点云
        points = np.random.rand(1000, 3).astype(np.float32)
        
        try:
            self.visualizer.visualize_bev(
                points,
                bev_range=(-50, 50, -50, 50),
                resolution=0.1
            )
        except Exception as e:
            pytest.fail(f"可视化鸟瞰图失败: {e}")
```

## 集成测试

### 1. 数据加载测试

```python
# tests/test_data_loader.py

import pytest
import numpy as np
import sys
sys.path.append('..')

from src.data.kitti_loader import KITTILoader


class TestKITTILoader:
    """KITTI 数据加载器测试"""
    
    @pytest.fixture
    def loader(self, tmp_path):
        """创建临时数据加载器"""
        # 创建模拟的 KITTI 数据目录结构
        (tmp_path / 'velodyne').mkdir()
        (tmp_path / 'label_2').mkdir()
        (tmp_path / 'calib').mkdir()
        
        # 创建模拟的点云文件
        points = np.random.rand(100, 4).astype(np.float32)
        points.tofile(str(tmp_path / 'velodyne' / '000001.bin'))
        
        # 创建模拟的标注文件
        with open(tmp_path / 'label_2' / '000001.txt', 'w') as f:
            f.write('Car 0.00 0 -1.57 614.24 181.78 727.31 284.77 1.57 1.73 4.15 1.00 1.49 16.04 1.55\n')
        
        return KITTILoader(str(tmp_path), split='training')
    
    def test_load_point_cloud(self, loader):
        """测试点云加载"""
        points = loader.load_point_cloud('000001')
        
        assert points is not None
        assert isinstance(points, np.ndarray)
        assert points.shape[1] == 4  # x, y, z, intensity
    
    def test_load_labels(self, loader):
        """测试标注加载"""
        labels = loader.load_labels('000001')
        
        assert labels is not None
        assert len(labels) > 0
        assert 'class' in labels[0]
        assert 'bbox' in labels[0]
```

### 2. 检测流程测试

```python
# tests/test_detection.py

import pytest
import torch
import numpy as np
import sys
sys.path.append('..')

from src.models.pointpillars import PointPillars
from src.utils.transforms import PointCloudTransforms


class TestDetectionPipeline:
    """检测流程测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.model = PointPillars(
            voxel_size=[0.16, 0.16, 4],
            point_cloud_range=[-40, -40, -3, 40, 40, 1],
            num_classes=3
        )
        self.model.eval()
    
    def test_end_to_end(self):
        """测试端到端检测流程"""
        # 创建模拟点云
        points = np.random.rand(1000, 4).astype(np.float32)
        
        # 预处理
        points_tensor = torch.from_numpy(points).unsqueeze(0)
        
        # 推理
        with torch.no_grad():
            predictions = self.model(points_tensor)
        
        # 验证预测结果
        assert 'cls_score' in predictions
        assert 'bbox_pred' in predictions
        assert 'dir_pred' in predictions
        
        # 验证输出形状
        cls_score = predictions['cls_score']
        assert cls_score.shape[0] == 1  # batch size
        assert cls_score.shape[1] > 0   # 有预测结果
    
    def test_data_augmentation(self):
        """测试数据增强"""
        # 创建模拟数据
        points = np.random.rand(1000, 4).astype(np.float32)
        boxes = np.random.rand(10, 7).astype(np.float32)
        
        # 测试随机翻转
        flipped_points, flipped_boxes = PointCloudTransforms.random_flip(
            points, boxes, prob=1.0
        )
        
        # 验证翻转后数据形状不变
        assert flipped_points.shape == points.shape
        assert flipped_boxes.shape == boxes.shape
        
        # 测试随机旋转
        rotated_points, rotated_boxes = PointCloudTransforms.random_rotation(
            points, boxes, range=(0, 0.1)
        )
        
        # 验证旋转后数据形状不变
        assert rotated_points.shape == points.shape
        assert rotated_boxes.shape == boxes.shape
```

## 性能测试

### 1. 推理速度测试

```python
# tests/test_performance.py

import pytest
import torch
import time
import sys
sys.path.append('..')

from src.models.pointpillars import PointPillars


class TestPerformance:
    """性能测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.model = PointPillars(
            voxel_size=[0.16, 0.16, 4],
            point_cloud_range=[-40, -40, -3, 40, 40, 1],
            num_classes=3
        )
        self.model.eval()
        self.model.cuda()
    
    def test_inference_speed(self):
        """测试推理速度"""
        # 创建模拟输入
        points = torch.randn(1, 1000, 4).cuda()
        
        # 预热
        for _ in range(10):
            with torch.no_grad():
                self.model(points)
        
        # 测试推理时间
        torch.cuda.synchronize()
        start_time = time.time()
        
        num_iterations = 100
        for _ in range(num_iterations):
            with torch.no_grad():
                self.model(points)
        
        torch.cuda.synchronize()
        end_time = time.time()
        
        # 计算平均推理时间
        avg_time = (end_time - start_time) / num_iterations
        fps = 1.0 / avg_time
        
        print(f"平均推理时间: {avg_time*1000:.2f} ms")
        print(f"FPS: {fps:.2f}")
        
        # 验证推理速度满足要求 (至少 10 FPS)
        assert fps >= 10, f"推理速度过慢: {fps:.2f} FPS"
    
    def test_memory_usage(self):
        """测试内存占用"""
        # 清空缓存
        torch.cuda.empty_cache()
        
        # 记录初始内存
        initial_memory = torch.cuda.memory_allocated()
        
        # 创建模型和输入
        points = torch.randn(1, 1000, 4).cuda()
        
        # 推理
        with torch.no_grad():
            self.model(points)
        
        # 记录峰值内存
        peak_memory = torch.cuda.max_memory_allocated()
        
        # 计算内存占用
        memory_usage = (peak_memory - initial_memory) / 1024 / 1024  # MB
        
        print(f"内存占用: {memory_usage:.2f} MB")
        
        # 验证内存占用合理 (小于 2GB)
        assert memory_usage < 2048, f"内存占用过大: {memory_usage:.2f} MB"
```

### 2. 准确性测试

```python
class TestAccuracy:
    """准确性测试"""
    
    def test_kitti_validation(self):
        """测试 KITTI 验证集性能"""
        # 注意：这个测试需要实际的 KITTI 数据集
        # 这里只测试评估函数是否能正常运行
        
        # 创建模拟的预测结果和真实标注
        predictions = [
            {
                'boxes': np.random.rand(10, 7),
                'scores': np.random.rand(10),
                'labels': np.random.randint(0, 3, 10)
            }
        ]
        
        ground_truth = [
            {
                'boxes': np.random.rand(10, 7),
                'labels': np.random.randint(0, 3, 10)
            }
        ]
        
        # 计算 mAP
        from src.utils.evaluation import compute_map
        mAP = compute_map(predictions, ground_truth)
        
        # 验证 mAP 在合理范围内
        assert 0 <= mAP <= 1
```

## 测试运行

### 运行所有测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_point_cloud.py

# 运行特定测试类
pytest tests/test_point_cloud.py::TestPointCloud

# 运行特定测试方法
pytest tests/test_point_cloud.py::TestPointCloud::test_filter_by_range

# 显示详细输出
pytest -v tests/

# 显示打印输出
pytest -s tests/

# 生成覆盖率报告
pytest --cov=src tests/
```

### 测试配置

```python
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## 测试覆盖率目标

| 模块 | 目标覆盖率 | 当前覆盖率 |
|------|-----------|-----------|
| 点云处理 | 90% | - |
| 模型模块 | 85% | - |
| 可视化模块 | 80% | - |
| 数据加载 | 90% | - |
| 后处理 | 85% | - |
| **总体** | **85%** | - |

## 持续集成

### GitHub Actions 配置

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=src tests/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 测试最佳实践

1. **测试命名**: 使用描述性的测试名称
2. **测试隔离**: 每个测试应该独立运行
3. **测试数据**: 使用固定的测试数据
4. **测试清理**: 测试后清理资源
5. **测试覆盖**: 确保关键路径被测试

## 参考资源

1. Pytest 官方文档: https://docs.pytest.org/
2. PyTorch 测试指南: https://pytorch.org/docs/stable/testing.html
3. 测试覆盖率: https://coverage.readthedocs.io/
