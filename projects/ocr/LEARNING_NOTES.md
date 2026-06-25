# OCR 文字识别系统 - 学习笔记

## 项目概述

本项目实现了一个完整的 OCR 文字识别系统，包含文字检测和文字识别两大核心模块。通过这个项目，我深入学习了 OCR 技术的原理和实现。

## 学习收获

### 1. OCR 基础知识

**什么是 OCR？**
OCR（Optical Character Recognition）是将图像中的文字转换为可编辑文本的技术。一个完整的 OCR 系统通常包含：
- 图像预处理
- 文字检测
- 文字识别
- 后处理

**核心流程：**
```
图像输入 → 预处理 → 文字检测 → 区域裁剪 → 文字识别 → 文本输出
```

### 2. 文字检测技术

**传统方法：**
- 连通组件分析
- 边缘检测
- 形态学操作

**深度学习方法：**
- CTPN：基于锚框的文字检测
- EAST：单阶段高效检测
- SegLink：基于分割的检测

**简单检测器实现思路：**
1. 灰度化
2. 自适应二值化
3. 形态学膨胀（连接相邻文字）
4. 轮廓检测
5. 最小外接矩形

### 3. CRNN 架构

CRNN（Convolutional Recurrent Neural Network）是文字识别的经典架构：

**结构组成：**
```
输入图像 → CNN特征提取 → RNN序列建模 → CTC解码 → 输出文本
```

**关键创新：**
1. **CNN 提取特征**：将图像转换为特征序列
2. **RNN 建模依赖**：捕捉序列上下文信息
3. **CTC 对齐**：解决输入输出长度不一致问题

**CTC 原理：**
- 不需要逐字符标注位置
- 自动学习输入输出对齐
- 使用 blank 标签处理重复字符

### 4. PyTorch 实现要点

**模型定义：**
```python
class CRNN(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.cnn = nn.Sequential(...)  # 特征提取
        self.rnn = nn.LSTM(...)       # 序列建模
        self.fc = nn.Linear(...)      # 分类
    
    def forward(self, x):
        conv = self.cnn(x)           # (B, C, H, W)
        # 转换为序列格式
        b, c, h, w = conv.size()
        conv = conv.squeeze(2)       # (B, C, W)
        conv = conv.permute(2, 0, 1) # (W, B, C) = (T, B, C)
        rnn_out, _ = self.rnn(conv)
        output = self.fc(rnn_out)
        return output
```

**CTC 损失：**
```python
criterion = nn.CTCLoss(blank=0)
loss = criterion(log_probs, targets, input_lengths, target_lengths)
```

### 5. OpenCV 图像处理

**常用操作：**
```python
# 灰度化
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 二值化
binary = cv2.adaptiveThreshold(gray, 255, 
                                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, 11, 2)

# 形态学操作
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
dilated = cv2.dilate(binary, kernel, iterations=1)

# 轮廓检测
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, 
                                cv2.CHAIN_APPROX_SIMPLE)

# 透视变换
M = cv2.getPerspectiveTransform(src_pts, dst_pts)
warped = cv2.warpPerspective(image, M, (w, h))
```

### 6. 评估指标

**检测评估：**
- IoU (Intersection over Union)
- Precision / Recall / F1

**识别评估：**
- 字符准确率
- 词准确率
- 编辑距离

**计算编辑距离：**
```python
def edit_distance(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1
    
    return dp[m][n]
```

## 遇到的问题与解决

### 问题 1: CRNN 输出形状不正确

**问题描述：** CNN 输出的高度维度不为 1，导致无法转换为序列格式。

**解决方案：** 确保 CNN 的池化层将高度降为 1：
```python
nn.MaxPool2d((2, 1), (2, 1))  # 只在高度方向池化
```

### 问题 2: CTC Loss 计算错误

**问题描述：** 输入长度和目标长度设置不正确。

**解决方案：** 
```python
# 输入长度是序列的实际长度
input_lengths = torch.full((batch_size,), seq_len, dtype=torch.long)

# 目标长度是每个样本的目标字符数
target_lengths = torch.tensor([len(t) for t in targets])
```

### 问题 3: 文字检测噪声干扰

**问题描述：** 简单检测器会检测到很多非文字区域。

**解决方案：** 
1. 调整面积阈值
2. 增加形态学操作
3. 使用更复杂的检测器

## 深入思考

### 1. 为什么使用 CRNN？

**优势：**
- 端到端训练
- 不需要逐字符标注
- 处理变长序列
- 参数量相对较小

**局限：**
- 依赖 CNN 的感受野
- RNN 难以并行化
- 对长文本效果有限

### 2. CTC vs Attention

| 方面 | CTC | Attention |
|------|-----|-----------|
| 对齐方式 | 单调对齐 | 软对齐 |
| 训练难度 | 简单 | 较难 |
| 长文本 | 较好 | 较差 |
| 推理速度 | 快 | 慢 |

### 3. 检测+识别 vs 端到端

**分离架构（本项目）：**
- 优点：模块化、易调试
- 缺点：误差累积

**端到端架构：**
- 优点：整体优化
- 缺点：复杂度高

## 扩展方向

### 1. 模型改进
- 使用 Transformer 替代 RNN
- 使用注意力机制
- 引入语言模型

### 2. 功能扩展
- 多语言支持
- 表格识别
- 版面分析

### 3. 工程优化
- 模型量化
- 模型剪枝
- 部署优化

## 代码实现要点

### 1. 模块化设计

```python
# 检测器接口
class TextDetector:
    def detect(self, image) -> List[np.ndarray]:
        pass

# 识别器接口
class TextRecognizer:
    def recognize(self, image) -> Tuple[str, float]:
        pass

# OCR 引擎
class OCREngine:
    def __init__(self, detector, recognizer):
        self.detector = detector
        self.recognizer = recognizer
```

### 2. 工具函数封装

```python
# 图像处理
def resize_image(image, max_size):
    pass

def crop_text_region(image, bbox):
    pass

# 可视化
def draw_bboxes(image, bboxes):
    pass

def draw_results(image, results):
    pass
```

### 3. 评估系统

```python
class OCREvaluator:
    def compute_char_accuracy(self):
        pass
    
    def compute_word_accuracy(self):
        pass
    
    def compute_edit_distance(self):
        pass
```

## 总结

通过本项目，我掌握了：

1. **OCR 基本原理**：理解了文字检测和识别的完整流程
2. **CRNN 架构**：深入理解了 CNN + RNN + CTC 的设计思想
3. **PyTorch 实践**：学会了用 PyTorch 实现自定义模型
4. **OpenCV 应用**：掌握了图像处理的常用技术
5. **系统设计**：学会了模块化设计和接口抽象

这个项目为后续学习更复杂的 OCR 系统打下了坚实的基础。

## 参考资源

1. Shi, B., et al. (2017). An End-to-End Trainable Neural Network for Image-based Sequence Recognition
2. Zhou, X., et al. (2017). EAST: An Efficient and Accurate Scene Text Detector
3. Graves, A., et al. (2006). Connectionist Temporal Classification
4. PyTorch 官方文档
5. OpenCV 官方文档