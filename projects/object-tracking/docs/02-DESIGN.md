# 02 - 项目设计文档

## 1. 系统架构

### 1.1 整体架构

```
object-tracking/
├── src/
│   ├── __init__.py              # 模块初始化
│   ├── kalman_filter.py         # 卡尔曼滤波器
│   ├── correlation_filter.py    # 相关滤波跟踪器
│   ├── evaluation.py            # 跟踪评估
│   └── video_tracker.py         # 视频跟踪演示
├── tests/
│   ├── test_kalman_filter.py    # 卡尔曼滤波测试
│   ├── test_correlation_filter.py # 相关滤波测试
│   └── test_evaluation.py       # 评估测试
├── examples/
│   ├── demo_kalman.py           # 卡尔曼滤波演示
│   ├── demo_correlation.py      # 相关滤波演示
│   └── demo_video_tracking.py   # 视频跟踪演示
└── docs/
    ├── 01-RESEARCH.md           # 研究文档
    ├── 02-DESIGN.md             # 设计文档
    ├── 03-IMPLEMENTATION.md     # 实现文档
    ├── 04-TESTING.md            # 测试文档
    └── 05-DEVELOPMENT.md        # 开发文档
```

### 1.2 模块依赖关系

```
video_tracker.py
    ├── correlation_filter.py (MOSSETracker, KCFTracker)
    ├── kalman_filter.py (KalmanFilter)
    └── evaluation.py (TrackingEvaluator)

evaluation.py
    └── (独立模块，无内部依赖)

kalman_filter.py
    └── (独立模块，无内部依赖)

correlation_filter.py
    └── (独立模块，无内部依赖)
```

## 2. 核心类设计

### 2.1 KalmanFilter 类

```python
class KalmanFilter:
    """标准卡尔曼滤波器"""

    def __init__(self, dt, process_noise, measurement_noise):
        """初始化滤波器参数"""

    def predict(self) -> np.ndarray:
        """预测步骤"""

    def update(self, measurement) -> np.ndarray:
        """更新步骤"""

    def get_position(self) -> Tuple[float, float]:
        """获取当前位置"""

    def get_velocity(self) -> Tuple[float, float]:
        """获取当前速度"""

    def set_state(self, x, y, vx=0, vy=0):
        """设置初始状态"""

    def reset(self):
        """重置滤波器"""
```

**设计考虑:**
- 使用4维状态向量 [x, y, vx, vy]
- 2维观测向量 [x, y]
- 离散白噪声加速度模型
- 支持自定义时间步长

### 2.2 MOSSETracker 类

```python
class MOSSETracker:
    """MOSSE相关滤波跟踪器"""

    def __init__(self, learning_rate, sigma, padding, psr_threshold):
        """初始化跟踪器参数"""

    def init(self, frame, bbox) -> bool:
        """初始化跟踪"""

    def update(self, frame) -> TrackingResult:
        """更新跟踪"""

    def _get_search_region(self, frame, bbox) -> np.ndarray:
        """获取搜索区域"""

    def _preprocess(self, patch) -> np.ndarray:
        """预处理图像块"""

    def _create_gaussian_response(self, size, center) -> np.ndarray:
        """创建高斯响应图"""

    def _compute_psr(self, response, peak_pos) -> float:
        """计算峰值旁瓣比"""
```

**设计考虑:**
- 支持自定义学习率控制更新速度
- PSR阈值用于检测跟踪失败
- 高斯响应图作为训练目标
- 对数变换和归一化预处理

### 2.3 KCFTracker 类

```python
class KCFTracker:
    """KCF跟踪器"""

    def __init__(self, learning_rate, sigma, lambda_reg, padding, cell_size):
        """初始化跟踪器"""

    def init(self, frame, bbox) -> bool:
        """初始化跟踪"""

    def update(self, frame) -> TrackingResult:
        """更新跟踪"""

    def _get_features(self, frame, bbox) -> np.ndarray:
        """提取特征"""

    def _extract_hog(self, patch) -> np.ndarray:
        """提取HOG特征"""

    def _gaussian_kernel(self, x1, x2) -> np.ndarray:
        """计算高斯核"""
```

**设计考虑:**
- 使用HOG特征增强判别能力
- 核化相关滤波提高精度
- 支持多通道特征

### 2.4 TrackingEvaluator 类

```python
class TrackingEvaluator:
    """跟踪评估器"""

    def add_frame(self, tracker_name, pred_bbox, gt_bbox, frame_time):
        """添加一帧结果"""

    def evaluate(self, tracker_name) -> Dict[str, float]:
        """评估指定跟踪器"""

    def evaluate_all(self) -> Dict[str, Dict[str, float]]:
        """评估所有跟踪器"""

    def compare(self, metric) -> List[Tuple[str, float]]:
        """比较跟踪器"""

    def print_summary(self):
        """打印摘要"""
```

### 2.5 VideoTracker 类

```python
class VideoTracker:
    """视频目标跟踪器"""

    def __init__(self, tracker_type, use_kalman, show_visualization, output_path):
        """初始化"""

    def select_target(self, frame) -> Tuple[int, int, int, int]:
        """手动选择目标"""

    def init(self, frame, bbox) -> bool:
        """初始化跟踪"""

    def update(self, frame) -> Tuple[bool, Tuple[int, int, int, int]]:
        """更新跟踪"""

    def process_video(self, video_path, initial_bbox) -> List[Dict]:
        """处理视频"""

    def process_camera(self, camera_id) -> List[Dict]:
        """处理摄像头"""
```

## 3. 数据结构设计

### 3.1 TrackingResult

```python
@dataclass
class TrackingResult:
    """跟踪结果"""
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    confidence: float                 # 置信度 (PSR)
    center: Tuple[float, float]       # 中心坐标
```

### 3.2 TrackingMetrics

```python
@dataclass
class TrackingMetrics:
    """跟踪评估指标"""
    iou_scores: List[float]           # IoU分数
    center_errors: List[float]        # 中心误差
    frame_times: List[float]          # 帧处理时间
    num_frames: int                   # 总帧数
    num_lost: int                     # 丢失帧数
```

## 4. 算法流程设计

### 4.1 跟踪流程

```
输入帧
    ↓
┌─────────────────┐
│  获取搜索区域    │
└─────────────────┘
    ↓
┌─────────────────┐
│  特征提取        │
│  (灰度/HOG)     │
└─────────────────┘
    ↓
┌─────────────────┐
│  FFT变换        │
└─────────────────┘
    ↓
┌─────────────────┐
│  频域相关计算    │
└─────────────────┘
    ↓
┌─────────────────┐
│  IFFT + 峰值定位│
└─────────────────┘
    ↓
┌─────────────────┐
│  位置更新        │
└─────────────────┘
    ↓
┌─────────────────┐
│  模型更新        │
│  (学习率控制)    │
└─────────────────┘
    ↓
输出结果
```

### 4.2 卡尔曼滤波集成

```
相关滤波输出 (cx, cy)
        ↓
┌─────────────────┐
│  卡尔曼预测      │
└─────────────────┘
        ↓
┌─────────────────┐
│  卡尔曼更新      │
│  (使用CF输出)    │
└─────────────────┘
        ↓
┌─────────────────┐
│  平滑后位置      │
└─────────────────┘
        ↓
输出最终位置
```

## 5. 接口设计

### 5.1 跟踪器接口

```python
class BaseTracker:
    """跟踪器基类"""

    def init(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> bool:
        """初始化跟踪"""
        pass

    def update(self, frame: np.ndarray) -> TrackingResult:
        """更新跟踪"""
        pass
```

### 5.2 评估接口

```python
class BaseEvaluator:
    """评估器基类"""

    def add_frame(self, pred_bbox, gt_bbox):
        """添加帧结果"""
        pass

    def evaluate(self) -> Dict[str, float]:
        """评估"""
        pass
```

## 6. 性能设计

### 6.1 时间复杂度

| 操作 | 复杂度 | 说明 |
|------|--------|------|
| FFT | O(N log N) | N为搜索区域大小 |
| 相关计算 | O(N) | 频域点乘 |
| IFFT | O(N log N) | 峰值定位 |
| 卡尔曼更新 | O(n³) | n为状态维度(4) |

### 6.2 空间复杂度

- 滤波模板: O(W × H)
- 特征图: O(W × H × C)
- 协方差矩阵: O(n²)

### 6.3 优化策略

1. **搜索区域限制**: 填充比例2-2.5倍
2. **特征降维**: 使用cell_size降低HOG维度
3. **模型更新**: 学习率控制避免过拟合
4. **卡尔曼平滑**: 减少噪声抖动

## 7. 错误处理设计

### 7.1 跟踪失败检测

```python
# PSR阈值检测
if psr < self.psr_threshold:
    # 跟踪可能失败
    # 选项1: 保持上次位置
    # 选项2: 使用卡尔曼预测
    # 选项3: 暂停更新
```

### 7.2 边界处理

```python
# 搜索区域超出边界时
if x1 < 0 or y1 < 0 or x2 > w or y2 > h:
    # 零填充或镜像填充
    pass
```

### 7.3 异常处理

- 未初始化时调用update抛出RuntimeError
- 视频读取失败返回空结果
- 跟踪失败返回上次有效位置
