# 目标跟踪 (Object Tracking)

实现视频中的目标跟踪，包括相关滤波跟踪和卡尔曼滤波。

## 项目概述

本项目实现了经典的目标跟踪算法:
- **MOSSE**: 基于最小输出平方误差和的相关滤波跟踪
- **KCF**: 核化相关滤波跟踪
- **卡尔曼滤波**: 状态估计和平滑

## 核心循环

```
初始目标 → 特征提取 → 模型匹配 → 位置更新 → 目标跟踪
```

## 功能特性

- 相关滤波跟踪 (MOSSE, KCF)
- 卡尔曼滤波平滑
- 跟踪评估 (IoU, 中心误差, 精度图)
- 视频跟踪演示
- 多目标跟踪支持

## 快速开始

### 安装依赖

```bash
pip install numpy opencv-python matplotlib pytest
```

### 基本使用

```python
from src.correlation_filter import MOSSETracker
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

### 使用卡尔曼滤波平滑

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

## 演示脚本

### 卡尔曼滤波演示

```bash
python examples/demo_kalman.py
```

### 相关滤波演示

```bash
python examples/demo_correlation.py
```

### 视频跟踪演示

```bash
python examples/demo_video_tracking.py
```

## 测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_kalman_filter.py -v
python -m pytest tests/test_correlation_filter.py -v
python -m pytest tests/test_evaluation.py -v
```

## 项目结构

```
object-tracking/
├── src/
│   ├── __init__.py
│   ├── kalman_filter.py         # 卡尔曼滤波器
│   ├── correlation_filter.py    # 相关滤波跟踪器
│   ├── evaluation.py            # 跟踪评估
│   └── video_tracker.py         # 视频跟踪演示
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

## 技术栈

- **语言**: Python
- **框架**: OpenCV
- **依赖**: numpy, opencv-python, matplotlib

## 学习目标

- 理解目标跟踪原理
- 掌握相关滤波
- 学会卡尔曼滤波

## 文档

- [研究文档](docs/01-RESEARCH.md) - 目标跟踪技术研究
- [设计文档](docs/02-DESIGN.md) - 项目架构设计
- [实现文档](docs/03-IMPLEMENTATION.md) - 核心算法实现
- [测试文档](docs/04-TESTING.md) - 测试策略和用例
- [开发文档](docs/05-DEVELOPMENT.md) - 开发指南和API
- [学习笔记](LEARNING_NOTES.md) - 学习心得和总结

## 参考文献

1. Bolme et al., "Visual Object Tracking using Adaptive Correlation Filters" (CVPR 2010)
2. Henriques et al., "High-Speed Tracking with Kernelized Correlation Filters" (TPAMI 2015)
3. Kalman, "A New Approach to Linear Filtering and Prediction Problems" (1960)

## License

MIT
