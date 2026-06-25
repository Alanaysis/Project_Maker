# 05 - 开发文档

## 1. 开发环境

### 1.1 依赖

```
numpy>=1.21.0
opencv-python>=4.5.0
matplotlib>=3.5.0 (可选，用于可视化)
pytest>=7.0.0 (测试)
```

### 1.2 安装

```bash
cd projects/object-tracking
pip install -r requirements.txt
```

### 1.3 目录结构

```
object-tracking/
├── src/
│   ├── __init__.py
│   ├── kalman_filter.py
│   ├── correlation_filter.py
│   ├── evaluation.py
│   └── video_tracker.py
├── tests/
│   ├── test_kalman_filter.py
│   ├── test_correlation_filter.py
│   └── test_evaluation.py
├── examples/
│   ├── demo_kalman.py
│   ├── demo_correlation.py
│   └── demo_video_tracking.py
└── docs/
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 2. 快速开始

### 2.1 基本使用

```python
from src.correlation_filter import MOSSETracker
from src.kalman_filter import KalmanFilter
import cv2

# 创建跟踪器
tracker = MOSSETracker(learning_rate=0.2)

# 读取视频
cap = cv2.VideoCapture("video.mp4")
ret, frame = cap.read()

# 选择目标
bbox = cv2.selectROI("Select", frame)

# 初始化
tracker.init(frame, bbox)

# 跟踪循环
while True:
    ret, frame = cap.read()
    if not ret:
        break

    result = tracker.update(frame)
    x, y, w, h = result.bbox
    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.imshow("Tracking", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
```

### 2.2 使用卡尔曼滤波平滑

```python
from src.video_tracker import VideoTracker

# 创建跟踪器 (自动集成卡尔曼滤波)
tracker = VideoTracker(
    tracker_type="mosse",
    use_kalman=True
)

# 处理视频
tracker.process_video("video.mp4")
```

## 3. API参考

### 3.1 KalmanFilter

```python
class KalmanFilter:
    def __init__(self, dt=1.0, process_noise=1e-3, measurement_noise=1e-1)
    def predict(self) -> np.ndarray
    def update(self, measurement: np.ndarray) -> np.ndarray
    def get_state(self) -> Tuple[float, float, float, float]
    def get_position(self) -> Tuple[float, float]
    def get_velocity(self) -> Tuple[float, float]
    def set_state(self, x, y, vx=0, vy=0)
    def reset(self, x=0, y=0, vx=0, vy=0)
```

### 3.2 MOSSETracker

```python
class MOSSETracker:
    def __init__(self, learning_rate=0.125, sigma=2.0, padding=2.0, psr_threshold=8.0)
    def init(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> bool
    def update(self, frame: np.ndarray) -> TrackingResult
```

### 3.3 KCFTracker

```python
class KCFTracker:
    def __init__(self, learning_rate=0.0125, sigma=0.6, lambda_reg=1e-4,
                 padding=2.5, cell_size=4)
    def init(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> bool
    def update(self, frame: np.ndarray) -> TrackingResult
```

### 3.4 TrackingResult

```python
@dataclass
class TrackingResult:
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    confidence: float                 # 置信度
    center: Tuple[float, float]       # 中心坐标
```

### 3.5 TrackingEvaluator

```python
class TrackingEvaluator:
    def add_frame(self, tracker_name, pred_bbox, gt_bbox, frame_time=0.0)
    def evaluate(self, tracker_name) -> Dict[str, float]
    def evaluate_all(self) -> Dict[str, Dict[str, float]]
    def compare(self, metric) -> List[Tuple[str, float]]
    def print_summary(self)
```

### 3.6 VideoTracker

```python
class VideoTracker:
    def __init__(self, tracker_type="mosse", use_kalman=True,
                 show_visualization=True, output_path=None)
    def select_target(self, frame) -> Tuple[int, int, int, int]
    def init(self, frame, bbox) -> bool
    def update(self, frame) -> Tuple[bool, Tuple[int, int, int, int]]
    def process_video(self, video_path, initial_bbox=None) -> List[Dict]
    def process_camera(self, camera_id=0) -> List[Dict]
    def save_history(self, path)
    def load_history(self, path)
```

## 4. 演示脚本

### 4.1 卡尔曼滤波演示

```bash
python examples/demo_kalman.py
```

演示内容:
- 生成不同类型的运动轨迹
- 添加观测噪声
- 运行卡尔曼滤波
- 可视化结果

### 4.2 相关滤波演示

```bash
python examples/demo_correlation.py
```

演示内容:
- 创建合成测试序列
- 运行MOSSE和KCF跟踪器
- 评估性能
- 比较结果

### 4.3 视频跟踪演示

```bash
python examples/demo_video_tracking.py
```

演示内容:
- 单目标跟踪
- 多目标跟踪
- 跟踪评估
- 实时摄像头跟踪

## 5. 自定义扩展

### 5.1 添加新的跟踪器

```python
class MyTracker:
    def __init__(self):
        self.initialized = False

    def init(self, frame, bbox):
        """初始化跟踪"""
        self.bbox = bbox
        self.initialized = True
        return True

    def update(self, frame):
        """更新跟踪"""
        # 实现跟踪逻辑
        return TrackingResult(
            bbox=self.bbox,
            confidence=1.0,
            center=(self.bbox[0] + self.bbox[2]/2,
                   self.bbox[1] + self.bbox[3]/2)
        )
```

### 5.2 添加新的特征

```python
def _extract_custom_features(self, patch):
    """提取自定义特征"""
    # 实现特征提取
    return features
```

### 5.3 添加新的评估指标

```python
def compute_custom_metric(pred, gt):
    """计算自定义指标"""
    # 实现指标计算
    return value
```

## 6. 性能调优

### 6.1 MOSSE参数

| 参数 | 默认值 | 说明 | 建议范围 |
|------|--------|------|----------|
| learning_rate | 0.125 | 模型更新速度 | 0.05-0.3 |
| sigma | 2.0 | 高斯响应标准差 | 1.0-5.0 |
| padding | 2.0 | 搜索区域填充 | 1.5-3.0 |
| psr_threshold | 8.0 | PSR阈值 | 5.0-15.0 |

### 6.2 KCF参数

| 参数 | 默认值 | 说明 | 建议范围 |
|------|--------|------|----------|
| learning_rate | 0.0125 | 模型更新速度 | 0.005-0.05 |
| sigma | 0.6 | 高斯核带宽 | 0.3-1.0 |
| lambda_reg | 1e-4 | 正则化参数 | 1e-5-1e-3 |
| cell_size | 4 | HOG cell大小 | 2-8 |

### 6.3 卡尔曼滤波参数

| 参数 | 默认值 | 说明 | 建议范围 |
|------|--------|------|----------|
| dt | 1.0 | 时间步长 | 0.1-10.0 |
| process_noise | 1e-3 | 过程噪声 | 1e-5-1e-1 |
| measurement_noise | 1e-1 | 测量噪声 | 1e-2-10.0 |

## 7. 常见问题

### 7.1 跟踪丢失

**问题**: 跟踪器丢失目标

**解决方案**:
- 降低learning_rate
- 增大padding
- 降低psr_threshold
- 使用卡尔曼滤波预测

### 7.2 跟踪漂移

**问题**: 跟踪框逐渐偏离目标

**解决方案**:
- 增大learning_rate
- 使用更鲁棒的特征 (HOG)
- 增加正则化

### 7.3 速度慢

**问题**: 跟踪速度慢

**解决方案**:
- 减小搜索区域 (降低padding)
- 使用更大的cell_size
- 降低图像分辨率

## 8. 未来改进

### 8.1 尺度估计

- 实现DSST (Discriminative Scale Space Tracking)
- 多尺度搜索

### 8.2 遮挡处理

- 基于PSR的遮挡检测
- 遮挡时使用卡尔曼预测
- 重新检测机制

### 8.3 深度特征

- 使用预训练CNN提取特征
- 实现SiamFC类跟踪器

### 8.4 多目标关联

- 实现匈牙利算法
- 基于外观的重识别

## 9. 参考资料

1. [OpenCV Tracking API](https://docs.opencv.org/4.x/d9/df8/group__tracking.html)
2. [PyOTB Benchmark](http://visual-tracking.net/)
3. [MOSSE Paper](https://www.cs.colostate.edu/~draper/papers/bolme_cvpr10.pdf)
4. [KCF Paper](https://arxiv.org/abs/1404.7584)
