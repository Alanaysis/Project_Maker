# 特征匹配 SIFT/ORB

实现图像特征点检测和匹配，理解计算机视觉中的特征提取与匹配技术。

## 学习目标

- 理解特征点检测原理（角点、边缘、斑点）
- 掌握 SIFT（Scale-Invariant Feature Transform）算法
- 掌握 ORB（Oriented FAST and Rotated BRIEF）算法
- 学会特征匹配方法（暴力匹配、FLANN）

## 核心循环

```
图像 → 特征点检测 → 描述子 → 匹配
```

## 技术栈

- **主语言**: Python 3.8+
- **框架**: OpenCV 4.x
- **依赖**: NumPy, Matplotlib

## 项目结构

```
feature-matching/
├── README.md
├── LEARNING_NOTES.md
├── requirements.txt
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── src/
│   ├── __init__.py
│   ├── detector.py          # 特征点检测器
│   ├── descriptor.py        # 描述子计算
│   ├── matcher.py           # 特征匹配器
│   ├── visualizer.py        # 可视化工具
│   └── main.py              # 主程序入口
├── tests/
│   ├── __init__.py
│   ├── test_detector.py
│   ├── test_descriptor.py
│   └── test_matcher.py
└── data/
    └── examples/            # 示例图像
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行特征匹配
python src/main.py --input data/examples/ --method sift

# 运行测试
pytest tests/
```

## 核心功能

### 1. 特征点检测
- SIFT: 尺度不变特征变换
- ORB: 快速角点检测 + 方向计算
- Harris角点检测

### 2. 描述子计算
- SIFT描述子: 128维梯度直方图
- ORB描述子: 256位二进制描述子
- BRIEF描述子: 二进制比较

### 3. 特征匹配
- 暴力匹配 (Brute-Force)
- FLANN快速匹配
- 比率测试筛选

### 4. 可视化
- 特征点绘制
- 匹配结果展示
- 匹配质量评估

## API使用

```python
from src.detector import FeatureDetector
from src.descriptor import DescriptorExtractor
from src.matcher import FeatureMatcher

# 初始化
detector = FeatureDetector(method='sift')
extractor = DescriptorExtractor(method='sift')
matcher = FeatureMatcher(method='bf')

# 处理图像
img1 = cv2.imread('image1.jpg', cv2.IMREAD_GRAYSCALE)
img2 = cv2.imread('image2.jpg', cv2.IMREAD_GRAYSCALE)

# 检测特征点
kp1 = detector.detect(img1)
kp2 = detector.detect(img2)

# 计算描述子
des1 = extractor.compute(img1, kp1)
des2 = extractor.compute(img2, kp2)

# 特征匹配
matches = matcher.match(des1, des2)
```

## 参考资源

- [OpenCV Feature Detection Tutorial](https://docs.opencv.org/4.x/d7/d66/tutorial_feature_detection.html)
- [SIFT Paper (Lowe 2004)](https://www.cs.ubc.ca/~lowe/papers/ijcv04.pdf)
- [ORB Paper (Rublee et al. 2011)](https://ieeexplore.ieee.org/document/6126544)
