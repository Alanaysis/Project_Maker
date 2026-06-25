# 实现细节文档 - 手势识别

## 1. 手部检测实现

### 肤色分割算法

```python
def _detect_skin(self, hsv_image: np.ndarray) -> np.ndarray:
    """
    肤色分割 - HSV颜色空间阈值

    关键参数：
    - H (色相): 0-20 度，覆盖常见肤色
    - S (饱和度): 20-255，排除灰白色
    - V (明度): 70-255，排除暗区域
    """
    mask = cv2.inRange(hsv_image, self.skin_lower, self.skin_upper)
    return mask
```

**为什么用HSV而不是RGB？**
- HSV对光照变化更鲁棒
- 色相(H)通道独立于亮度
- 便于设定肤色范围

### 形态学操作

```python
def _clean_mask(self, mask: np.ndarray) -> np.ndarray:
    """
    形态学清理

    操作顺序：
    1. 开运算：去除小噪声点
    2. 闭运算：填充手部内部空洞
    3. 膨胀：连接断裂区域
    """
    # 开运算去噪
    cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel, iterations=2)
    # 闭运算填充
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, self.kernel, iterations=2)
    # 膨胀连接
    cleaned = cv2.dilate(cleaned, self.kernel, iterations=1)
    return cleaned
```

## 2. 关键点提取实现

### CNN模型架构

```python
class KeypointNet(nn.Module):
    """
    关键点检测网络

    结构：
    - 4层卷积 (32 -> 64 -> 128 -> 256)
    - BatchNorm + ReLU + MaxPool
    - 全连接回归头

    输入: (B, 3, 128, 128)
    输出: (B, 42) - 21个关键点的(x, y)坐标
    """
```

**为什么用回归而不是热力图？**
- 回归方法更简单，适合学习
- 计算量更小
- 缺点是精度略低

### 坐标归一化

```python
# 输出使用sigmoid限制在[0, 1]
keypoints = torch.sigmoid(keypoints)
```

**为什么归一化？**
- 坐标范围固定，便于训练
- 不同尺寸图像可以统一处理
- 梯度更稳定

## 3. 特征工程实现

### 手指伸展状态

```python
def _get_finger_states(keypoints: np.ndarray) -> List[float]:
    """
    判断每根手指是否伸展

    方法：比较指尖和对应关节的y坐标
    - 指尖y < 关节y → 手指伸展（手指向上）
    - 指尖y > 关节y → 手指弯曲
    """
```

### 指尖距离特征

```python
def _get_tip_distances(keypoints: np.ndarray) -> List[float]:
    """
    计算指尖之间的相对距离

    选择5个指尖的两两组合中最具区分度的10对
    使用手掌宽度归一化
    """
```

### 特征向量组成

```
总维度: 66
├── finger_states: 5个 (bool)
├── tip_distances: 10个 (float)
├── finger_angles: 4个 (float)
├── palm_distances: 5个 (float)
└── normalized_coords: 42个 (21*2)
```

## 4. 手势分类实现

### 规则分类逻辑

```python
def classify_rule_based(self, keypoints: np.ndarray) -> dict:
    """
    基于规则的分类

    规则：
    - 拳头：所有手指都弯曲
    - 张开手掌：所有手指都伸展
    - 剪刀手：食指和中指伸展
    - 竖大拇指：只有拇指伸展
    - 指向：只有食指伸展
    - OK手势：拇指和食指接近
    """
```

### 神经网络分类

```python
class GestureClassifierNet(nn.Module):
    """
    手势分类网络

    结构：
    - 3层全连接 (66 -> 128 -> 64 -> 32)
    - BatchNorm + ReLU + Dropout
    - 输出层 (32 -> 7)
    """
```

## 5. 端到端集成

### GestureRecognizer管道

```python
def recognize(self, image: np.ndarray) -> List[RecognitionResult]:
    """
    端到端识别

    步骤：
    1. 手部检测 -> bbox列表
    2. 对每个bbox提取关键点
    3. 对每个关键点集合分类手势
    4. 组装结果
    """
```

## 6. 性能优化

### 已实现的优化

1. **批量处理**：支持批量关键点提取
2. **模型缓存**：模型只加载一次
3. **坐标预计算**：像素坐标预先计算

### 可优化的方向

1. **模型量化**：INT8量化减少计算量
2. **模型剪枝**：减少参数量
3. **TensorRT加速**：GPU推理优化
4. **多线程处理**：并行处理多个手部

## 7. 错误处理

### 常见问题及解决方案

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 手部检测失败 | 光照不好 | 调整肤色阈值 |
| 关键点不准 | 手部模糊 | 添加图像增强 |
| 分类错误 | 特征不明显 | 增加特征维度 |

### 边界情况处理

```python
# 空图像
if image is None or image.size == 0:
    return []

# 无手部
if len(hands) == 0:
    return []

# 关键点越界
keypoints = np.clip(keypoints, 0, 1)
```
