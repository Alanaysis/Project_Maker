# 手势识别 (Gesture Recognition)

基于深度学习的手势识别系统，实现从图像输入到手势分类的完整流程。

## 核心流程

```
图像输入 → 手部检测 → 关键点提取 → 手势分类 → 输出
   │          │           │           │         │
   ▼          ▼           ▼           ▼         ▼
 BGR图     肤色分割     CNN回归    规则/NN    手势标签
          轮廓检测     21关键点    特征提取   置信度
```

## 项目结构

```
gesture-recognition/
├── README.md
├── LEARNING_NOTES.md
├── setup.py
├── requirements.txt
├── src/gesture_recognition/
│   ├── __init__.py
│   ├── models/
│   │   ├── hand_detector.py          # 手部检测
│   │   ├── keypoint_extractor.py     # 关键点提取
│   │   ├── gesture_classifier.py     # 手势分类
│   │   └── gesture_recognizer.py     # 端到端识别器
│   ├── data/
│   │   └── hand_dataset.py           # 数据集
│   └── utils/
│       ├── visualization.py          # 可视化工具
│       └── metrics.py                # 评估指标
├── tests/
├── scripts/
│   ├── train.py                      # 训练脚本
│   └── evaluate.py                   # 评估脚本
├── examples/
│   └── basic_recognition.py          # 基础示例
└── docs/
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 安装

```bash
# 克隆项目后进入目录
cd projects/gesture-recognition

# 安装项目（开发模式）
pip install -e ".[dev]"

# 或安装依赖
pip install -r requirements.txt
```

## 使用

### 基础用法（合成数据）

```bash
# 运行基础识别示例
python examples/basic_recognition.py

# 使用合成数据训练（无需真实数据）
python scripts/train.py --synthetic --epochs 10 --batch-size 32

# 评估模型
python scripts/evaluate.py --checkpoint checkpoints/best_model.pth --synthetic
```

### API使用

```python
import torch
import numpy as np
from gesture_recognition import GestureRecognizer

# 创建识别器（使用规则分类）
recognizer = GestureRecognizer(use_neural_classifier=False)

# 识别手势
image = np.zeros((480, 640, 3), dtype=np.uint8)  # 实际图像
results = recognizer.recognize(image)

for result in results:
    print(f"Hand {result.hand_id}: {result.gesture_zh} ({result.confidence:.2f})")
```

### 关键点提取

```python
from gesture_recognition import KeypointExtractor

# 创建提取器
extractor = KeypointExtractor()

# 提取关键点
result = extractor.extract(image, bbox=(100, 100, 200, 200))
keypoints = result["keypoints"]  # (21, 2) 归一化坐标
```

### 手势分类

```python
from gesture_recognition.models.gesture_classifier import GestureClassifier

# 创建分类器
classifier = GestureClassifier()

# 规则分类
result = classifier.classify_rule_based(keypoints)
print(f"Gesture: {result['gesture_zh']}")

# 神经网络分类
result = classifier.classify(keypoints)
print(f"Gesture: {result['gesture_zh']} ({result['confidence']:.2f})")
```

### 可视化

```python
from gesture_recognition.utils.visualization import draw_hand_landmarks, draw_gesture_result

# 绘制关键点
vis = draw_hand_landmarks(image, keypoints_pixel)

# 绘制识别结果
vis = draw_gesture_result(vis, result)
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行带覆盖率的测试
pytest tests/ -v --cov=gesture_recognition
```

## 学习目标

- **手势识别原理**: 理解手势识别的基本流程和核心算法
- **手部关键点检测**: 掌握关键点回归方法
- **手势分类**: 学会规则方法和神经网络方法
- **特征工程**: 理解如何设计有效特征
- **端到端系统**: 学会构建完整的识别系统

## 技术栈

- **语言**: Python 3.8+
- **深度学习框架**: PyTorch 1.12+
- **视觉处理**: OpenCV
- **数据处理**: NumPy
- **可视化**: Matplotlib
- **测试**: pytest

## API示例

### 端到端识别

```python
from gesture_recognition import GestureRecognizer

recognizer = GestureRecognizer()
results = recognizer.recognize(image)
```

### 批量处理

```python
# 处理视频
results = recognizer.process_video("input.mp4", "output.mp4")

# 处理摄像头
recognizer.process_camera(camera_id=0)
```

## 支持的手势

| 手势 | 英文 | 说明 |
|------|------|------|
| 拳头 | fist | 所有手指弯曲 |
| 张开手掌 | open_palm | 所有手指伸展 |
| 剪刀手 | peace | 食指和中指伸展 |
| 竖大拇指 | thumbs_up | 只有拇指伸展 |
| 指向 | pointing | 只有食指伸展 |
| OK手势 | ok | 拇指和食指形成圆 |

## 重点难点

### 重点1：肤色分割
**为什么重要**：手部检测的基础
**关键代码**：`src/gesture_recognition/models/hand_detector.py`
**理解要点**：
- HSV颜色空间的优势
- 形态学操作的作用

### 重点2：关键点回归
**为什么重要**：手势识别的核心
**关键代码**：`src/gesture_recognition/models/keypoint_extractor.py`
**理解要点**：
- CNN回归方法
- 坐标归一化技巧

### 重点3：特征工程
**为什么重要**：连接关键点和手势的桥梁
**关键代码**：`src/gesture_recognition/models/gesture_classifier.py`
**理解要点**：
- 手指状态特征
- 距离和角度特征

## 值得思考

### 1. 为什么用肤色分割而不是深度学习检测？
**背景**：手部检测有多种方法
**权衡**：肤色分割简单快速但对光照敏感；深度学习检测鲁棒但需要数据和计算
**结论**：学习目的选择简单方法，生产环境用深度学习

### 2. 回归方法 vs 热力图方法？
**优点**：回归简单快速；热力图精度高
**缺点**：回归精度略低；热力图计算量大
**适用场景**：原型用回归，产品用热力图

## 参考资源

- [MediaPipe Hands](https://google.github.io/mediapipe/solutions/hands.html) - Google的实时手部追踪
- [OpenPose](https://github.com/CMU-Perceptual-Computing-Lab/openpose) - 多人姿态估计
- [Hand Keypoint Detection](https://arxiv.org/abs/1704.07809) - 手部关键点检测论文
- [Gesture Recognition Survey](https://arxiv.org/abs/2001.01930) - 手势识别综述

## 学习路径

建议学习顺序：
1. 阅读 [01-RESEARCH.md](docs/01-RESEARCH.md) 了解技术背景
2. 阅读 [02-DESIGN.md](docs/02-DESIGN.md) 理解架构设计
3. 阅读 [03-IMPLEMENTATION.md](docs/03-IMPLEMENTATION.md) 学习实现细节
4. 阅读 [04-TESTING.md](docs/04-TESTING.md) 了解测试策略
5. 阅读 [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) 开始开发
6. 运行 [examples/basic_recognition.py](examples/basic_recognition.py)
7. 阅读源代码，重点关注 ⭐ 标记的部分
8. 完成 [LEARNING_NOTES.md](LEARNING_NOTES.md) 中的练习
