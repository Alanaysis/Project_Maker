# 技术设计文档 - 手势识别

## 1. 架构概述

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Gesture Recognition System                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Hand      │→ │  Keypoint   │→ │  Gesture    │          │
│  │  Detector   │  │  Extractor  │  │ Classifier  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│         ↑               ↑               ↑                   │
│         │               │               │                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Data Pipeline & Utilities               │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 模块划分

| 模块 | 职责 | 文件位置 |
|------|------|----------|
| HandDetector | 手部区域检测 | `src/gesture_recognition/models/hand_detector.py` |
| KeypointExtractor | 手部关键点提取 | `src/gesture_recognition/models/keypoint_extractor.py` |
| GestureClassifier | 手势分类 | `src/gesture_recognition/models/gesture_classifier.py` |
| GestureRecognizer | 端到端识别器 | `src/gesture_recognition/models/gesture_recognizer.py` |
| HandDataset | 数据集管理 | `src/gesture_recognition/data/hand_dataset.py` |
| Visualization | 可视化工具 | `src/gesture_recognition/utils/visualization.py` |
| Metrics | 评估指标 | `src/gesture_recognition/utils/metrics.py` |

## 2. 核心流程

### 主流程

```
输入图像 (BGR)
    │
    ▼
┌─────────────────┐
│  Hand Detector  │ ← 肤色分割 + 形态学操作
│                 │
│  输出: bbox列表  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Keypoint        │ ← CNN回归21个关键点
│ Extractor       │
│                 │
│ 输出: 21x2坐标  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Gesture         │ ← 特征提取 + 规则/神经网络分类
│ Classifier      │
│                 │
│ 输出: 手势类别  │
└────────┬────────┘
         │
         ▼
    RecognitionResult
```

### 子流程1：手部检测

```
输入图像
    │
    ▼
高斯模糊 (去噪)
    │
    ▼
BGR → HSV (颜色空间转换)
    │
    ▼
肤色阈值分割
    │
    ▼
形态学操作 (开运算 + 闭运算)
    │
    ▼
轮廓检测
    │
    ▼
面积过滤 (min_hand_area)
    │
    ▼
手部边界框
```

### 子流程2：关键点提取

```
手部图像
    │
    ▼
Resize (128x128)
    │
    ▼
归一化 ([0, 1])
    │
    ▼
CNN特征提取
    │
    ▼
全连接回归
    │
    ▼
Sigmoid激活
    │
    ▼
21个关键点坐标
```

## 3. 数据设计

### 手部关键点定义

```python
# 21个关键点索引定义
KEYPOINT_NAMES = [
    "wrist",           # 0: 手腕
    "thumb_cmc",       # 1: 拇指掌指关节
    "thumb_mcp",       # 2: 拇指近端指间关节
    "thumb_ip",        # 3: 拇指远端指间关节
    "thumb_tip",       # 4: 拇指尖
    "index_mcp",       # 5: 食指掌指关节
    "index_pip",       # 6: 食指近端指间关节
    "index_dip",       # 7: 食指远端指间关节
    "index_tip",       # 8: 食指尖
    # ... 其他手指类似
]
```

### 手势类别定义

```python
GESTURE_CLASSES = {
    0: "fist",         # 拳头
    1: "open_palm",    # 张开手掌
    2: "peace",        # 剪刀手/V字
    3: "thumbs_up",    # 竖大拇指
    4: "pointing",     # 指向
    5: "ok",           # OK手势
    6: "none",         # 无手势
}
```

### 特征向量设计

```
特征维度: 66
├── 手指伸展状态: 5个 (每根手指是否伸直)
├── 指尖距离: 10个 (指尖两两距离)
├── 手指角度: 4个 (手指间夹角)
├── 手掌到指尖距离: 5个
└── 归一化坐标: 42个 (21个关键点的x,y)
```

## 4. 接口设计

### HandDetector API

```python
class HandDetector:
    def detect(self, image: np.ndarray) -> List[dict]:
        """
        检测图像中的手部

        Args:
            image: BGR格式的输入图像

        Returns:
            List[dict]: 包含bbox, center, area, mask的字典列表
        """
```

### KeypointExtractor API

```python
class KeypointExtractor:
    def extract(
        self,
        image: np.ndarray,
        bbox: Optional[Tuple[int, int, int, int]] = None
    ) -> dict:
        """
        提取手部关键点

        Returns:
            dict: 包含keypoints, keypoints_pixel, confidence
        """
```

### GestureClassifier API

```python
class GestureClassifier:
    def classify(self, keypoints: np.ndarray) -> dict:
        """
        分类手势

        Returns:
            dict: 包含gesture, gesture_zh, confidence, probabilities
        """

    def classify_rule_based(self, keypoints: np.ndarray) -> dict:
        """
        基于规则的手势分类（无需训练）
        """
```

## 5. 技术选型

### 选型决策

| 决策点 | 选项A | 选项B | 选项C | 最终选择 |
|--------|-------|-------|-------|----------|
| 手部检测 | 肤色分割 | YOLO检测 | MediaPipe | 肤色分割 |
| 关键点提取 | CNN回归 | 热力图 | GNN | CNN回归 |
| 手势分类 | 规则方法 | SVM | 神经网络 | 两者都实现 |
| 图像处理 | OpenCV | PIL | Skimage | OpenCV |

### 选择理由

**手部检测选择肤色分割**：
1. 计算量小，适合学习
2. 不需要预训练模型
3. 代码简洁，易于理解

**关键点提取选择CNN回归**：
1. 实现简单直接
2. PyTorch学习价值高
3. 便于调试和可视化

## 6. 设计决策与权衡

### 决策1：关键点回归 vs 热力图

**背景**：关键点检测有两种主流方法

**方案对比**：

| 维度 | 回归方法 | 热力图方法 |
|------|----------|------------|
| 优点 | 实现简单，速度快 | 精度更高，对遮挡鲁棒 |
| 缺点 | 精度略低 | 计算量大，实现复杂 |
| 复杂度 | 低 | 高 |
| 适用场景 | 学习、原型 | 生产环境 |

**最终选择**：回归方法

**理由**：
1. 适合学习目的
2. 代码更简洁
3. 推理速度更快

### 决策2：规则分类 vs 神经网络分类

**背景**：手势分类可以用规则或学习方法

**方案对比**：

| 维度 | 规则方法 | 神经网络 |
|------|----------|----------|
| 优点 | 可解释，无需训练 | 精度高，可扩展 |
| 缺点 | 难以覆盖所有情况 | 需要标注数据 |
| 适用场景 | 学习、演示 | 生产环境 |

**最终选择**：两者都实现

**理由**：
1. 规则方法便于理解手势逻辑
2. 神经网络展示深度学习应用
3. 可以对比两种方法的效果

## 7. 扩展性设计

### 预留的扩展点

1. **手部检测器扩展**：
   - 可以替换为YOLO、SSD等检测器
   - 接口保持一致

2. **关键点提取器扩展**：
   - 可以替换为热力图方法
   - 可以使用预训练模型

3. **手势分类器扩展**：
   - 可以添加更多手势类别
   - 可以使用更复杂的模型

### 如何扩展

```python
# 添加新的手部检测器
class YOLOHandDetector(HandDetector):
    def detect(self, image):
        # YOLO检测逻辑
        pass

# 替换组件
recognizer = GestureRecognizer()
recognizer.hand_detector = YOLOHandDetector()
```
