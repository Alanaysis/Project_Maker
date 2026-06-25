# 开发手册 - 手势识别

## 1. 环境搭建

### 系统要求

- 操作系统：Windows/macOS/Linux
- Python 版本：3.8+
- 推荐：GPU（可选，用于加速训练）

### 安装步骤

```bash
# 1. 进入项目目录
cd projects/gesture-recognition

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 或以开发模式安装
pip install -e ".[dev]"

# 5. 验证安装
python -c "import gesture_recognition; print('安装成功')"
```

## 2. 项目结构

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
│   ├── conftest.py
│   ├── test_hand_detector.py
│   ├── test_keypoint_extractor.py
│   ├── test_gesture_classifier.py
│   └── test_hand_dataset.py
├── scripts/
│   ├── train.py                      # 训练脚本
│   └── evaluate.py                   # 评估脚本
├── examples/
│   └── basic_recognition.py          # 基础示例
├── configs/
│   └── default.yaml
└── docs/
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 3. 快速开始

### 运行基础示例

```bash
# 运行基础识别示例
python examples/basic_recognition.py
```

### 训练模型

```bash
# 使用合成数据训练
python scripts/train.py --synthetic --epochs 10 --batch-size 32

# 查看训练结果
ls checkpoints/
```

### 评估模型

```bash
# 评估模型
python scripts/evaluate.py --checkpoint checkpoints/best_model.pth --synthetic
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行带覆盖率的测试
pytest tests/ -v --cov=gesture_recognition
```

## 4. 核心模块解析

### HandDetector - 手部检测

**文件位置**：`src/gesture_recognition/models/hand_detector.py`

**职责**：从图像中检测手部区域

**核心代码**：

```python
# ⭐ 重点代码 - 肤色分割
def _detect_skin(self, hsv_image: np.ndarray) -> np.ndarray:
    """
    HSV颜色空间的肤色分割

    关键点：
    1. H通道(色相)对肤色最敏感
    2. S通道排除灰白色
    3. V通道排除暗区域
    """
    mask = cv2.inRange(hsv_image, self.skin_lower, self.skin_upper)
    return mask
```

**理解要点**：
- HSV颜色空间的选择原因
- 形态学操作的组合使用
- 轮廓检测和面积过滤

### KeypointExtractor - 关键点提取

**文件位置**：`src/gesture_recognition/models/keypoint_extractor.py`

**职责**：从手部图像提取21个关键点

**核心代码**：

```python
# ⭐ 重点代码 - CNN回归关键点
class KeypointNet(nn.Module):
    """
    关键点检测网络

    关键设计：
    1. 4层卷积提取空间特征
    2. 全连接层回归坐标
    3. Sigmoid输出归一化坐标
    """
```

**理解要点**：
- 回归vs热力图方法的权衡
- 坐标归一化的重要性
- 批量归一化的作用

### GestureClassifier - 手势分类

**文件位置**：`src/gesture_recognition/models/gesture_classifier.py`

**职责**：将关键点分类为手势

**核心代码**：

```python
# ⭐ 重点代码 - 特征工程
class KeypointFeatureExtractor:
    """
    从关键点提取分类特征

    特征包括：
    1. 手指伸展状态
    2. 指尖距离
    3. 手指角度
    4. 归一化坐标
    """
```

**理解要点**：
- 特征工程的思路
- 规则方法vs神经网络方法
- 手势的几何特征表示

## 5. 重点难点攻克

### 难点1：关键点坐标归一化

**问题描述**：不同图像尺寸的关键点坐标不可直接比较

**解决方案**：使用sigmoid输出归一化坐标[0,1]

**关键代码**：
```python
# 输出使用sigmoid限制在[0,1]
keypoints = torch.sigmoid(keypoints)
```

**学习要点**：
- 为什么需要归一化
- sigmoid函数的作用
- 如何转换回像素坐标

### 难点2：手指伸展状态判断

**问题描述**：如何判断一根手指是否伸直

**解决方案**：比较指尖和关节的y坐标

**关键代码**：
```python
# 指尖y < 关节y → 手指伸展（向上）
extended = float(keypoints[tip, 1] < keypoints[mcp, 1])
```

**学习要点**：
- 图像坐标系的特点
- 手部关键点的拓扑关系
- 简单规则的有效性

### 难点3：特征工程设计

**问题描述**：如何从关键点中提取有区分度的特征

**解决方案**：结合几何特征和归一化坐标

**关键代码**：
```python
features = []
features.extend(finger_states)    # 手指状态
features.extend(tip_distances)    # 指尖距离
features.extend(angles)          # 手指角度
features.extend(palm_distances)  # 手掌距离
features.extend(normalized.flatten())  # 归一化坐标
```

**学习要点**：
- 特征工程的思路
- 不同特征的作用
- 特征组合的效果

## 6. 调试技巧

### 常用调试方法

1. **可视化关键点**
   ```python
   from gesture_recognition.utils.visualization import draw_hand_landmarks
   vis = draw_hand_landmarks(image, keypoints)
   cv2.imshow("Debug", vis)
   ```

2. **打印特征向量**
   ```python
   features = KeypointFeatureExtractor.extract_features(keypoints)
   print(f"Features: {features}")
   print(f"Finger states: {features[:5]}")
   ```

3. **检查中间结果**
   ```python
   hands = detector.detect(image)
   print(f"Detected {len(hands)} hands")
   for hand in hands:
       print(f"  bbox: {hand['bbox']}, area: {hand['area']}")
   ```

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 检测不到手部 | 光照太暗/太亮 | 调整skin_lower/upper参数 |
| 关键点不准 | 模型未训练 | 使用预训练模型或训练更多epoch |
| 分类错误 | 特征不明显 | 检查特征提取逻辑 |

## 7. 扩展指南

### 添加新的手势类别

1. 在`GESTURE_CLASSES`中添加新类别
2. 在`GESTURE_NAMES_ZH`中添加中文名
3. 在`HandDataset`中添加对应的合成数据模板
4. 在`classify_rule_based`中添加分类规则
5. 重新训练神经网络分类器

### 替换手部检测器

```python
# 创建新的检测器
class MyHandDetector(HandDetector):
    def detect(self, image):
        # 自定义检测逻辑
        pass

# 替换到识别器
recognizer = GestureRecognizer()
recognizer.hand_detector = MyHandDetector()
```

### 添加新的特征

```python
# 在KeypointFeatureExtractor中添加
@staticmethod
def _get_my_new_feature(keypoints: np.ndarray) -> List[float]:
    """新特征"""
    # 实现
    return [feature_values...]

# 在extract_features中调用
def extract_features(keypoints: np.ndarray) -> np.ndarray:
    features = []
    # ... 现有特征
    features.extend(cls._get_my_new_feature(keypoints))
    return np.array(features)
```

## 8. 代码规范

### 命名规范

- 类名：PascalCase（如`HandDetector`）
- 函数名：snake_case（如`detect_skin`）
- 变量名：snake_case（如`keypoints`）
- 常量名：UPPER_CASE（如`GESTURE_CLASSES`）

### 文档规范

- 每个模块有模块级docstring
- 每个类有类级docstring
- 每个公共方法有方法级docstring
- 关键代码有行内注释

### 代码风格

- 遵循PEP 8
- 使用类型注解
- 函数不超过50行
- 类不超过300行
