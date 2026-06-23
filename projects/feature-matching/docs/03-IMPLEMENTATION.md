# 特征匹配实现记录

## 1. 环境配置

### Python环境
- Python 3.8+
- OpenCV 4.x
- NumPy 1.20+
- Matplotlib 3.5+

### 安装依赖
```bash
pip install opencv-python>=4.5.0
pip install opencv-contrib-python>=4.5.0
pip install numpy>=1.20.0
pip install matplotlib>=3.5.0
```

## 2. 核心实现

### 2.1 FeatureDetector实现

```python
import cv2
import numpy as np
from typing import List, Tuple

class FeatureDetector:
    def __init__(self, method: str = 'sift', **params):
        self.method = method.lower()
        self.params = params
        self._detector = self._create_detector()

    def _create_detector(self):
        if self.method == 'sift':
            return cv2.SIFT_create(**self.params)
        elif self.method == 'orb':
            return cv2.ORB_create(**self.params)
        else:
            raise ValueError(f"Unsupported method: {self.method}")

    def detect(self, image: np.ndarray) -> List:
        if image is None:
            raise ValueError("Image cannot be None")
        return self._detector.detect(image)

    def detect_and_compute(self, image: np.ndarray) -> Tuple[List, np.ndarray]:
        if image is None:
            raise ValueError("Image cannot be None")
        return self._detector.detectAndCompute(image, None)
```

### 2.2 DescriptorExtractor实现

```python
class DescriptorExtractor:
    def __init__(self, method: str = 'sift'):
        self.method = method.lower()
        self._extractor = self._create_extractor()

    def _create_extractor(self):
        if self.method == 'sift':
            return cv2.SIFT_create()
        elif self.method == 'orb':
            return cv2.ORB_create()
        else:
            raise ValueError(f"Unsupported method: {self.method}")

    def compute(self, image: np.ndarray, keypoints: List) -> Tuple[List, np.ndarray]:
        if not keypoints:
            return keypoints, None
        return self._extractor.compute(image, keypoints)
```

### 2.3 FeatureMatcher实现

```python
class FeatureMatcher:
    def __init__(self, method: str = 'bf', cross_check: bool = True, **params):
        self.method = method.lower()
        self.cross_check = cross_check
        self.params = params
        self._matcher = self._create_matcher()

    def _create_matcher(self):
        if self.method == 'bf':
            norm_type = self.params.get('norm_type', cv2.NORM_L2)
            return cv2.BFMatcher(norm_type, self.cross_check)
        elif self.method == 'flann':
            index_params = dict(algorithm=1, trees=5)
            search_params = dict(checks=50)
            return cv2.FlannBasedMatcher(index_params, search_params)
        else:
            raise ValueError(f"Unsupported method: {self.method}")

    def match(self, desc1: np.ndarray, desc2: np.ndarray) -> List:
        if desc1 is None or desc2 is None:
            return []
        return self._matcher.match(desc1, desc2)

    def knn_match(self, desc1: np.ndarray, desc2: np.ndarray, k: int = 2) -> List:
        if desc1 is None or desc2 is None:
            return []
        return self._matcher.knnMatch(desc1, desc2, k)

    def ratio_test(self, matches: List, ratio: float = 0.7) -> List:
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < ratio * n.distance:
                    good_matches.append(m)
        return good_matches
```

### 2.4 Visualizer实现

```python
import matplotlib.pyplot as plt

class Visualizer:
    @staticmethod
    def draw_keypoints(image: np.ndarray, keypoints: List,
                       output_path: str = None) -> np.ndarray:
        img_kp = cv2.drawKeypoints(
            image, keypoints, None,
            flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS,
            color=(0, 255, 0)
        )
        if output_path:
            cv2.imwrite(output_path, img_kp)
        return img_kp

    @staticmethod
    def draw_matches(img1: np.ndarray, kp1: List,
                     img2: np.ndarray, kp2: List,
                     matches: List,
                     output_path: str = None) -> np.ndarray:
        img_matches = cv2.drawMatches(
            img1, kp1, img2, kp2, matches, None,
            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
        )
        if output_path:
            cv2.imwrite(output_path, img_matches)
        return img_matches

    @staticmethod
    def plot_match_statistics(matches: List, output_path: str = None):
        distances = [m.distance for m in matches]

        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        # 距离分布
        axes[0].hist(distances, bins=50, edgecolor='black')
        axes[0].set_xlabel('Distance')
        axes[0].set_ylabel('Count')
        axes[0].set_title('Match Distance Distribution')

        # 距离累积分布
        sorted_distances = np.sort(distances)
        cumulative = np.arange(1, len(sorted_distances) + 1) / len(sorted_distances)
        axes[1].plot(sorted_distances, cumulative)
        axes[1].set_xlabel('Distance')
        axes[1].set_ylabel('Cumulative Probability')
        axes[1].set_title('Cumulative Distance Distribution')

        plt.tight_layout()
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.show()
```

## 3. OpenCV API使用说明

### SIFT创建
```python
cv2.SIFT_create(
    nfeatures=0,           # 最大特征点数
    nOctaveLayers=3,       # 每octave层数
    contrastThreshold=0.04, # 对比度阈值
    edgeThreshold=10,      # 边缘阈值
    sigma=1.6              # 高斯sigma
)
```

### ORB创建
```python
cv2.ORB_create(
    nfeatures=500,         # 最大特征点数
    scaleFactor=1.2,       # 金字塔因子
    nlevels=8,             # 金字塔层数
    edgeThreshold=31,      # 边缘阈值
    firstLevel=0,          # 第一层
    WTA_K=2,               # 点数
    scoreType=cv2.ORB_HARRIS_SCORE, # 响应类型
    patchSize=31,          # 补丁大小
    fastThreshold=20       # FAST阈值
)
```

### BFMatcher创建
```python
cv2.BFMatcher(
    normType=cv2.NORM_L2,  # 距离类型
    crossCheck=True        # 交叉验证
)
```

### FlannBasedMatcher创建
```python
cv2.FlannBasedMatcher(
    indexParams={'algorithm': 1, 'trees': 5},  # 索引参数
    searchParams={'checks': 50}                 # 搜索参数
)
```

## 4. 实现注意事项

### 图像预处理
1. 转换为灰度图
2. 检查图像尺寸
3. 必要时进行归一化

### 特征点处理
1. 检查特征点数量
2. 处理空结果
3. 限制最大数量

### 匹配处理
1. 处理描述子为空的情况
2. 匹配数量验证
3. 距离阈值过滤

## 5. 调试技巧

### 查看特征点
```python
print(f"检测到 {len(keypoints)} 个特征点")
print(f"第一个关键点: ({keypoints[0].pt[0]:.1f}, {keypoints[0].pt[1]:.1f})")
print(f"描述子形状: {descriptors.shape}")
```

### 查看匹配结果
```python
print(f"匹配数量: {len(matches)}")
print(f"平均距离: {np.mean([m.distance for m in matches]):.2f}")
print(f"最小距离: {min(m.distance for m in matches):.2f}")
```

### 可视化调试
```python
# 显示特征点
cv2.imshow('Keypoints', img_kp)
cv2.waitKey(0)

# 显示匹配结果
cv2.imshow('Matches', img_matches)
cv2.waitKey(0)
```
