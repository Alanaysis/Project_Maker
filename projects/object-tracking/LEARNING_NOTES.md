# 目标跟踪 - 学习笔记

## 学习目标

1. 理解目标跟踪原理
2. 掌握相关滤波
3. 学会卡尔曼滤波

## 核心概念

### 1. 目标跟踪的本质

目标跟踪是计算机视觉中的时序问题:
- **输入**: 视频帧序列 + 初始目标位置
- **输出**: 每帧中目标的位置

核心挑战:
- 目标外观变化 (光照、姿态、遮挡)
- 背景干扰
- 实时性要求

### 2. 相关滤波原理

相关滤波利用信号处理中的相关性概念:

**时域相关:**
```
(f * g)(τ) = ∫ f(t) g(t+τ) dt
```

**频域计算 (FFT加速):**
```
F{f * g} = F{f} · F{g}*
```

**跟踪应用:**
```
响应 = IFFT(滤波模板 · 输入特征的FFT)
目标位置 = argmax(响应)
```

**为什么快?**
- 时域卷积 = 频域点乘
- FFT复杂度: O(N log N)
- 循环移位生成大量样本

### 3. 卡尔曼滤波原理

卡尔曼滤波是递归贝叶斯估计:

**预测 (先验):**
```
x̂⁻ = F · x̂
P⁻ = F · P · Fᵀ + Q
```

**更新 (后验):**
```
K = P⁻ · Hᵀ · (H · P⁻ · Hᵀ + R)⁻¹
x̂ = x̂⁻ + K · (z - H · x̂⁻)
P = (I - K · H) · P⁻
```

**直觉理解:**
- 预测: 根据运动模型猜测位置
- 更新: 结合观测修正猜测
- 卡尔曼增益: 平衡预测和观测的信任度

### 4. MOSSE算法详解

MOSSE是最经典的相关滤波跟踪算法:

**目标函数:**
```
min_H Σᵢ |Fᵢ ⊙ H - Gᵢ|²
```

**解析解:**
```
H = (Σᵢ Gᵢ ⊙ Fᵢ*) / (Σᵢ Fᵢ ⊙ Fᵢ*)
```

**在线更新:**
```
Hₙᵤₘ = η · (G ⊙ F*) + (1-η) · Hₙᵤₘ
Hᵈᵉⁿ = η · (F ⊙ F*) + (1-η) · Hᵈᵉⁿ
H = Hₙᵤₘ / Hᵈᵉⁿ
```

**关键参数:**
- 学习率 η: 控制更新速度
- σ: 高斯响应的标准差
- PSR: 跟踪置信度指标

### 5. KCF算法改进

KCF在MOSSE基础上的改进:

**核技巧:**
```
k(x,x') = exp(-1/σ² ||x-x'||²)
```

**优势:**
- 更强的判别能力
- 支持多通道特征 (HOG)
- 更好的跟踪精度

## 实践心得

### 1. 参数调优

**学习率 (learning_rate):**
- 太大: 容易漂移
- 太小: 适应慢
- 建议: 0.1-0.3

**填充比例 (padding):**
- 太大: 计算量增加
- 太小: 容易丢失
- 建议: 2.0-2.5

**PSR阈值:**
- 太高: 频繁丢失
- 太低: 接受错误跟踪
- 建议: 5-15

### 2. 卡尔曼滤波调优

**过程噪声 Q:**
- 描述运动模型的不确定性
- 匀速运动: 较小 (1e-3)
- 机动目标: 较大 (1e-1)

**测量噪声 R:**
- 描述观测的不确定性
- 取决于跟踪器精度
- 可以自适应调整

### 3. 调试技巧

**可视化:**
- 绘制轨迹对比
- 显示置信度
- 绘制误差曲线

**诊断:**
- 检查PSR值
- 分析残差
- 比较预测和观测

## 学习资源

### 论文

1. Bolme et al., "Visual Object Tracking using Adaptive Correlation Filters" (CVPR 2010)
2. Henriques et al., "High-Speed Tracking with Kernelized Correlation Filters" (TPAMI 2015)
3. Kalman, "A New Approach to Linear Filtering and Prediction Problems" (1960)

### 教程

1. [OpenCV Tracking Tutorial](https://docs.opencv.org/4.x/d9/df8/group__tracking.html)
2. [PySearcher Tracking Benchmark](http://visual-tracking.net/)

### 代码

1. [OpenCV Tracker Implementations](https://github.com/opencv/opencv_contrib)
2. [PyOTB](https://github.com/votchallenge/pyotb)

## 总结

### 核心收获

1. **相关滤波**: 利用FFT加速，实现高效跟踪
2. **卡尔曼滤波**: 状态估计和平滑的有效工具
3. **评估指标**: IoU、中心误差、精度图、成功率图

### 适用场景

| 算法 | 适用场景 | 不适用场景 |
|------|----------|------------|
| MOSSE | 实时跟踪、简单背景 | 大尺度变化、严重遮挡 |
| KCF | 多特征融合、复杂背景 | 极端形变 |
| 卡尔曼 | 匀速/匀加速运动 | 高度非线性运动 |

### 进一步学习

1. 尺度估计: DSST, SAMF
2. 深度学习: SiamFC, SiamRPN, TransT
3. 多目标跟踪: SORT, DeepSORT
4. 长期跟踪: TLD, LCT
