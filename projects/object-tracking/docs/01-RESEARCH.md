# 01 - 目标跟踪技术研究

## 1. 概述

目标跟踪 (Object Tracking) 是计算机视觉中的核心任务之一，旨在视频序列中持续定位和跟踪特定目标。本项目实现基于相关滤波和卡尔曼滤波的目标跟踪系统。

## 2. 目标跟踪分类

### 2.1 按目标数量分类

| 类型 | 描述 | 典型方法 |
|------|------|----------|
| 单目标跟踪 (SOT) | 跟踪单个指定目标 | MOSSE, KCF, SiamFC |
| 多目标跟踪 (MOT) | 同时跟踪多个目标 | SORT, DeepSORT |
| 特定目标跟踪 | 跟踪特定类别目标 | 行人跟踪、车辆跟踪 |

### 2.2 按方法分类

| 类型 | 描述 | 代表方法 |
|------|------|----------|
| 生成式 | 学习目标外观模型 | MOSSE, KCF, CSK |
| 判别式 | 区分目标和背景 | Struck, HCF |
| 深度学习 | 使用神经网络 | SiamFC, SiamRPN, TransT |
| 滤波方法 | 状态估计 | 卡尔曼滤波, 粒子滤波 |

## 3. 相关滤波跟踪

### 3.1 基本原理

相关滤波 (Correlation Filter) 利用信号处理中的相关性概念进行目标跟踪:

```
相关响应 = 滤波模板 * 输入特征
目标位置 = argmax(相关响应)
```

### 3.2 核心优势

1. **计算效率**: 利用FFT在频域计算，时间复杂度O(N log N)
2. **循环样本**: 通过循环移位生成大量训练样本
3. **实时性能**: 可达到数百FPS的跟踪速度

### 3.3 MOSSE算法

MOSSE (Minimum Output Sum of Squared Error) 是最经典的相关滤波跟踪算法。

**核心公式:**
```
min Σ |F_i * H - G_i|²
  H

解: H = Σ(G_i * F_i*) / Σ(F_i * F_i*)
```

其中:
- F: 输入特征的FFT
- G: 期望响应 (高斯峰)
- H: 滤波模板
- *: 共轭

**更新策略:**
```
H_num = η * (G * F*) + (1-η) * H_num
H_den = η * (F * F*) + (1-η) * H_den
H = H_num / H_den
```

### 3.4 KCF算法

KCF (Kernelized Correlation Filter) 在MOSSE基础上引入核技巧:

**核化相关:**
```
k_xx' = exp(-1/σ² * (||x||² + ||x'||² - 2*x*x'))
```

**优势:**
- 更强的判别能力
- 支持多通道特征 (如HOG)
- 更好的跟踪精度

## 4. 卡尔曼滤波

### 4.1 基本原理

卡尔曼滤波是一种递归状态估计方法，包含两个主要步骤:

1. **预测步骤** (Prediction):
   ```
   x' = F * x
   P' = F * P * F^T + Q
   ```

2. **更新步骤** (Update):
   ```
   K = P' * H^T * (H * P' * H^T + R)^-1
   x = x' + K * (z - H * x')
   P = (I - K * H) * P'
   ```

### 4.2 状态空间模型

**状态向量:**
```
x = [px, py, vx, vy]^T
```
- px, py: 位置
- vx, vy: 速度

**状态转移矩阵:**
```
F = [1 0 dt 0]
    [0 1 0 dt]
    [0 0 1  0]
    [0 0 0  1]
```

**观测矩阵:**
```
H = [1 0 0 0]
    [0 1 0 0]
```

### 4.3 噪声参数

- **过程噪声 Q**: 描述运动模型的不确定性
- **测量噪声 R**: 描述观测的不确定性
- **初始协方差 P₀**: 初始状态的不确定性

## 5. 跟踪评估指标

### 5.1 IoU (Intersection over Union)

```
IoU = |A ∩ B| / |A ∪ B|
```

- 完美匹配: IoU = 1.0
- 通常认为 IoU > 0.5 为成功跟踪

### 5.2 中心误差 (Center Error)

```
CE = √((cx_pred - cx_gt)² + (cy_pred - cy_gt)²)
```

- 单位: 像素
- 通常认为 CE < 20 像素为成功跟踪

### 5.3 精度图 (Precision Plot)

- 横轴: 中心误差阈值
- 纵轴: 误差小于阈值的帧比例
- 常用阈值: 20像素处的精度值

### 5.4 成功率图 (Success Plot)

- 横轴: IoU阈值
- 纵轴: IoU大于阈值的帧比例
- 常用指标: AUC (曲线下面积)

## 6. 主流跟踪算法对比

| 算法 | 特征 | 速度 | 精度 | 特点 |
|------|------|------|------|------|
| MOSSE | 灰度 | ~600 FPS | 中等 | 简单高效 |
| KCF | HOG | ~170 FPS | 较好 | 核化相关 |
| CSK | 灰度+核 | ~300 FPS | 中等 | 密集采样 |
| DSST | HOG | ~40 FPS | 好 | 尺度估计 |
| ECO | HOG+CNN | ~8 FPS | 很好 | 高效卷积 |

## 7. 参考文献

1. Bolme, D. S., et al. "Visual object tracking using adaptive correlation filters." CVPR 2010.
2. Henriques, J. F., et al. "High-speed tracking with kernelized correlation filters." TPAMI 2015.
3. Kalman, R. E. "A new approach to linear filtering and prediction problems." 1960.
4. Danelljan, M., et al. "Accurate scale estimation for robust visual tracking." BMVC 2014.
5. Wu, Y., et al. "Object tracking: A survey." Foundations and Trends in Computer Graphics and Vision 2015.
