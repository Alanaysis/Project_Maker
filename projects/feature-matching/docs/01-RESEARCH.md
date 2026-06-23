# 特征匹配研究笔记

## 1. 特征检测发展历史

### 早期方法（1980s-1990s）
- Moravec角点检测器（1980）
- Harris角点检测器（1988）
- SUSAN角点检测器（1997）

### 现代方法（2000s-至今）
- SIFT（2004）- Lowe
- SURF（2006）- Bay等
- ORB（2011）- Rublee等
- AKAZE（2013）- Alcantarilla等

## 2. SIFT深度研究

### 尺度空间理论

尺度空间是图像在不同尺度下的表示，用于检测不同大小的特征。

**高斯尺度空间**:
$$L(x,y,\sigma) = G(x,y,\sigma) * I(x,y)$$

其中高斯核：
$$G(x,y,\sigma) = \frac{1}{2\pi\sigma^2}e^{-\frac{x^2+y^2}{2\sigma^2}}$$

**尺度空间参数**:
- octaves: 图像分辨率层级（通常4-5层）
- scales_per_octave: 每层尺度数（通常3-5层）
- sigma: 初始高斯模糊参数

### DOG金字塔

**Difference of Gaussian**:
$$D(x,y,\sigma) = L(x,y,k\sigma) - L(x,y,\sigma)$$

优点：
- 近似尺度归一化LOG
- 计算高效（直接相减）

### 关键点定位

#### 亚像素精度
使用泰勒展开：
$$D(x) = D + \frac{\partial D^T}{\partial x}x + \frac{1}{2}x^T\frac{\partial^2 D}{\partial x^2}x$$

求导令为0：
$$\hat{x} = -\frac{\partial^2 D^{-1}}{\partial x^2}\frac{\partial D}{\partial x}$$

#### 去除低对比度点
$$|D(\hat{x})| \geq 0.03$$

#### 去除边缘响应
主曲率比值检测：
$$\frac{Tr(H)^2}{Det(H)} < \frac{(r+1)^2}{r}$$
其中 $r = 10$

### 方向分配

在关键点邻域内计算梯度：
$$m(x,y) = \sqrt{(L(x+1,y)-L(x-1,y))^2 + (L(x,y+1)-L(x,y-1))^2}$$
$$\theta(x,y) = \tan^{-1}\frac{L(x,y+1)-L(x,y-1)}{L(x+1,y)-L(x-1,y)}$$

使用36 bin（每10度）的直方图，取主方向（>80%最大值的方向）

### 描述子生成

1. 将关键点周围16x16区域旋转到主方向
2. 分成4x4个子区域（每个4x4像素）
3. 每个子区域计算8方向梯度直方图
4. 拼接得到128维描述子

**归一化**:
$$\hat{d} = \frac{d}{||d||_2}$$

截断到0.2后再归一化（提高光照不变性）

## 3. ORB深度研究

### FAST角点检测

**FAST-9检测规则**:
- 圆形邻域16个像素
- 连续9个像素比中心亮+阈值 或 暗-阈值
- 使用机器学习优化（ID3决策树）

**非极大值抑制**:
- 计算角点响应值
- 在3x3邻域内取最大值

### 灰度质心法（Intensity Centroid）

计算矩：
$$m_{pq} = \sum_{x,y} x^p y^q I(x,y)$$

质心：
$$C = (\frac{m_{10}}{m_{00}}, \frac{m_{01}}{m_{00}})$$

方向：
$$\theta = \tan^{-1}(m_{01}, m_{10})$$

### BRIEF描述子

**采样模式**:
- 在关键点周围31x31窗口内随机选取256个点对
- 使用高斯分布采样（σ² = 0.04 * patch_size²）

**二进制比较**:
$$b_i = \begin{cases} 1 & I(p_i) < I(q_i) \\ 0 & otherwise \end{cases}$$

**距离计算**（汉明距离）:
$$d = popcount(b_1 \oplus b_2)$$

### rBRIEF（旋转BRIEF）

将采样模式旋转θ角度：
$$\begin{pmatrix} x' \\ y' \end{pmatrix} = \begin{pmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{pmatrix} \begin{pmatrix} x \\ y \end{pmatrix}$$

## 4. 特征匹配研究

### 距离度量

#### 欧氏距离（SIFT）
$$d = \sqrt{\sum_{i=1}^{128}(a_i - b_i)^2}$$

#### 汉明距离（ORB）
$$d = popcount(a \oplus b)$$

### 匹配策略

#### 暴力匹配
- 时间复杂度: O(n²)
- 精确但慢

#### FLANN（Fast Library for Approximate Nearest Neighbors）
- KD树索引
- 层次化k-means聚类
- 时间复杂度: O(n log n)

### 匹配质量评估

#### 比率测试
$$\frac{d_1}{d_2} < threshold$$
- threshold = 0.7-0.8
- 低阈值 = 更严格

#### RANSAC
- 随机采样一致性
- 估计几何变换（单应性矩阵）
- 剔除误匹配

#### 交叉验证
- 双向匹配
- 只保留双向一致的匹配

## 5. 性能对比

| 算法 | 检测速度 | 描述子维度 | 匹配速度 | 精度 | 专利 |
|------|---------|-----------|---------|------|------|
| SIFT | 慢 | 128维浮点 | 中 | 高 | 是（已过期）|
| SURF | 中 | 64/128维浮点 | 中 | 高 | 是 |
| ORB | 快 | 256位二进制 | 快 | 中 | 否 |
| AKAZE | 中 | MLDB描述子 | 中 | 高 | 否 |

## 6. 参考文献

1. Lowe, D.G. (2004). "Distinctive Image Features from Scale-Invariant Keypoints". IJCV.
2. Rublee, E. et al. (2011). "ORB: An efficient alternative to SIFT or SURF". ICCV.
3. Bay, H. et al. (2008). "SURF: Speeded Up Robust Features". ECCV.
4. Muja, M. & Lowe, D.G. (2009). "Fast Approximate Nearest Neighbors with Automatic Algorithm Configuration". VISAPP.
