# 特征匹配系统设计

## 1. 系统架构

```
┌─────────────────────────────────────────────────────┐
│                    用户接口层                         │
│              (main.py, 命令行接口)                    │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                    业务逻辑层                         │
│    ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│    │ Detector │  │Descriptor│  │ Matcher  │       │
│    └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                    基础设施层                         │
│         OpenCV, NumPy, Matplotlib                   │
└─────────────────────────────────────────────────────┘
```

## 2. 模块设计

### 2.1 FeatureDetector（特征检测器）

**职责**: 检测图像中的特征点

**接口设计**:
```python
class FeatureDetector:
    def __init__(self, method: str = 'sift', **params):
        """
        初始化特征检测器
        Args:
            method: 'sift', 'orb', 'harris'
            **params: 算法特定参数
        """
        pass

    def detect(self, image: np.ndarray) -> List[KeyPoint]:
        """
        检测特征点
        Args:
            image: 灰度图像
        Returns:
            关键点列表
        """
        pass

    def detect_and_compute(self, image: np.ndarray) -> Tuple[List[KeyPoint], np.ndarray]:
        """
        同时检测关键点和计算描述子
        """
        pass
```

**支持的检测器**:
- SIFT: 尺度不变特征检测
- ORB: 快速角点检测
- Harris: 角点检测

### 2.2 DescriptorExtractor（描述子提取器）

**职责**: 计算特征点的描述子

**接口设计**:
```python
class DescriptorExtractor:
    def __init__(self, method: str = 'sift'):
        """
        初始化描述子提取器
        Args:
            method: 'sift', 'orb', 'brief'
        """
        pass

    def compute(self, image: np.ndarray, keypoints: List[KeyPoint]) -> np.ndarray:
        """
        计算描述子
        Args:
            image: 灰度图像
            keypoints: 关键点列表
        Returns:
            描述子矩阵 (N x D)
        """
        pass
```

**描述子类型**:
- SIFT: 128维浮点向量
- ORB: 256位二进制描述子
- BRIEF: 二进制描述子

### 2.3 FeatureMatcher（特征匹配器）

**职责**: 匹配两组描述子

**接口设计**:
```python
class FeatureMatcher:
    def __init__(self, method: str = 'bf', crossCheck: bool = True, **params):
        """
        初始化特征匹配器
        Args:
            method: 'bf'(暴力匹配), 'flann'
            crossCheck: 是否启用交叉验证
        """
        pass

    def match(self, desc1: np.ndarray, desc2: np.ndarray) -> List[DMatch]:
        """
        匹配描述子
        Args:
            desc1: 第一组描述子
            desc2: 第二组描述子
        Returns:
            匹配结果列表
        """
        pass

    def knn_match(self, desc1: np.ndarray, desc2: np.ndarray, k: int = 2) -> List[List[DMatch]]:
        """
        K近邻匹配
        """
        pass

    def ratio_test(self, matches: List[List[DMatch]], ratio: float = 0.7) -> List[DMatch]:
        """
        Lowe比率测试
        """
        pass
```

**匹配策略**:
- 暴力匹配: 精确但慢
- FLANN: 快速近似匹配
- 比率测试: 过滤误匹配

### 2.4 Visualizer（可视化工具）

**职责**: 可视化特征点和匹配结果

**接口设计**:
```python
class Visualizer:
    @staticmethod
    def draw_keypoints(image: np.ndarray, keypoints: List[KeyPoint],
                       output_path: str = None) -> np.ndarray:
        """绘制特征点"""
        pass

    @staticmethod
    def draw_matches(img1: np.ndarray, kp1: List[KeyPoint],
                     img2: np.ndarray, kp2: List[KeyPoint],
                     matches: List[DMatch],
                     output_path: str = None) -> np.ndarray:
        """绘制匹配结果"""
        pass

    @staticmethod
    def plot_match_statistics(matches: List[DMatch], output_path: str = None):
        """绘制匹配统计"""
        pass
```

## 3. 数据结构设计

### KeyPoint（关键点）
```python
class KeyPoint:
    x: float           # x坐标
    y: float           # y坐标
    size: float        # 特征尺度
    angle: float       # 方向角度
    response: float    # 响应强度
    octave: int        # 金字塔层级
    class_id: int      # 类别ID
```

### DMatch（匹配结果）
```python
class DMatch:
    queryIdx: int      # 第一组描述子索引
    trainIdx: int      # 第二组描述子索引
    distance: float    # 匹配距离
```

## 4. 配置设计

### 检测器参数
```yaml
sift:
  nfeatures: 0           # 最大特征点数（0表示不限制）
  nOctaveLayers: 3       # 每层 octave 的层数
  contrastThreshold: 0.04  # 对比度阈值
  edgeThreshold: 10      # 边缘阈值
  sigma: 1.6             # 高斯模糊参数

orb:
  nfeatures: 500         # 最大特征点数
  scaleFactor: 1.2       # 金字塔缩放因子
  nlevels: 8             # 金字塔层数
  edgeThreshold: 31      # 边缘阈值
  firstLevel: 0          # 第一层级别
  WTA_K: 2               # 生成描述子的点数
  scoreType: 0           # 角点响应类型
  patchSize: 31          # 描述子补丁大小
  fastThreshold: 20      # FAST阈值
```

### 匹配器参数
```yaml
bf:
  normType: 'NORM_L2'    # 距离类型
  crossCheck: true       # 交叉验证

flann:
  algorithm: 'FLANN_INDEX_KDTREE'  # 算法类型
  trees: 5               # KD树数量
  checks: 50             # 搜索次数
```

## 5. 错误处理设计

### 异常类型
```python
class FeatureMatchingError(Exception):
    """特征匹配基础异常"""
    pass

class InvalidImageError(FeatureMatchingError):
    """无效图像错误"""
    pass

class NoKeypointsError(FeatureMatchingError):
    """未检测到特征点错误"""
    pass

class MatchingFailedError(FeatureMatchingError):
    """匹配失败错误"""
    pass
```

### 错误处理策略
1. 输入验证: 检查图像格式、尺寸
2. 空结果处理: 检测不到特征点时返回空列表
3. 匹配失败: 记录日志，返回空匹配
4. 资源限制: 限制最大特征点数

## 6. 性能设计

### 时间复杂度
| 操作 | SIFT | ORB |
|------|------|-----|
| 检测 | O(N log N) | O(N) |
| 描述 | O(N) | O(N) |
| 匹配（暴力）| O(D²) | O(D²) |
| 匹配（FLANN）| O(D log D) | O(D log D) |

### 空间复杂度
- SIFT描述子: 128 * 4 bytes = 512 bytes/点
- ORB描述子: 32 bytes/点

### 优化策略
1. 限制特征点数量
2. 使用FLANN替代暴力匹配
3. 并行处理（多线程）
4. 图像金字塔降采样
