# 03 - 实现文档

## 1. 卡尔曼滤波器实现

### 1.1 状态空间模型

```python
# 状态向量: [x, y, vx, vy]
self.x = np.zeros(4, dtype=np.float64)

# 状态转移矩阵 F
self.F = np.array([
    [1, 0, dt, 0],
    [0, 1, 0, dt],
    [0, 0, 1,  0],
    [0, 0, 0,  1]
], dtype=np.float64)

# 观测矩阵 H
self.H = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0]
], dtype=np.float64)
```

### 1.2 预测步骤

```python
def predict(self) -> np.ndarray:
    # 状态预测
    self.x = self.F @ self.x

    # 协方差预测
    self.P = self.F @ self.P @ self.F.T + self.Q

    return self.x.copy()
```

### 1.3 更新步骤

```python
def update(self, measurement: np.ndarray) -> np.ndarray:
    # 卡尔曼增益
    S = self.H @ self.P @ self.H.T + self.R
    self.K = self.P @ self.H.T @ np.linalg.inv(S)

    # 状态更新
    y = measurement - self.H @ self.x
    self.x = self.x + self.K @ y

    # 协方差更新
    I = np.eye(4)
    self.P = (I - self.K @ self.H) @ self.P

    return self.x.copy()
```

### 1.4 过程噪声模型

```python
def _build_process_noise(self, q: float) -> np.ndarray:
    """离散白噪声加速度模型"""
    dt = self.dt
    Q = np.array([
        [dt**4/4, 0,        dt**3/2, 0       ],
        [0,        dt**4/4, 0,        dt**3/2 ],
        [dt**3/2,  0,        dt**2,   0       ],
        [0,        dt**3/2, 0,        dt**2   ]
    ]) * q
    return Q
```

### 1.5 自适应卡尔曼滤波

```python
class AdaptiveKalmanFilter(KalmanFilter):
    def update(self, measurement):
        # 计算残差
        residual = measurement - self.H @ self.x
        self.residuals.append(residual)

        # 自适应调整R
        if len(self.residuals) >= 3:
            empirical_cov = np.cov(np.array(self.residuals).T)
            innovation_cov = self.H @ self.P @ self.H.T
            target_R = empirical_cov - innovation_cov

            # 平滑更新
            self.R = (1 - α) * self.R + α * target_R

        return super().update(measurement)
```

## 2. 相关滤波实现

### 2.1 MOSSE算法实现

#### 初始化

```python
def init(self, frame, bbox):
    # 1. 获取搜索区域
    search_region = self._get_search_region(frame, bbox)
    patch = self._preprocess(search_region)

    # 2. 创建目标响应 (高斯峰)
    response = self._create_gaussian_response(size, center)

    # 3. FFT变换
    F = np.fft.fft2(patch)
    G = np.fft.fft2(response)

    # 4. 计算初始滤波模板
    self.H_num = G * np.conj(F)
    self.H_den = F * np.conj(F)
    self.H = self.H_num / (self.H_den + 1e-5)
```

#### 更新

```python
def update(self, frame):
    # 1. 获取搜索区域
    patch = self._preprocess(search_region)
    F = np.fft.fft2(patch)

    # 2. 计算相关响应
    response_fft = self.H * F
    response = np.real(np.fft.ifft2(response_fft))

    # 3. 找到峰值
    max_pos = np.unravel_index(np.argmax(response), response.shape)

    # 4. 计算位移
    dy = max_pos[0] - search_h // 2
    dx = max_pos[1] - search_w // 2

    # 5. 更新位置
    new_cx = self.center[0] + dx
    new_cy = self.center[1] + dy

    # 6. 更新模型
    if psr > threshold:
        self.H_num = η * (G * F*) + (1-η) * self.H_num
        self.H_den = η * (F * F*) + (1-η) * self.H_den
        self.H = self.H_num / (self.H_den + 1e-5)
```

### 2.2 KCF算法实现

#### 特征提取 (HOG)

```python
def _extract_hog(self, patch):
    # 1. 计算梯度
    gx = cv2.Sobel(patch, cv2.CV_64F, 1, 0, ksize=1)
    gy = cv2.Sobel(patch, cv2.CV_64F, 0, 1, ksize=1)

    # 2. 幅值和方向
    magnitude = np.sqrt(gx**2 + gy**2)
    orientation = np.arctan2(gy, gx)

    # 3. 分块直方图
    for i in range(n_cells_y):
        for j in range(n_cells_x):
            # 计算cell的梯度直方图
            hist = np.zeros(n_bins)
            for m, n in cell_pixels:
                bin_idx = orientation[m, n] * n_bins / 180
                hist[bin_idx] += magnitude[m, n]
            features[i, j] = hist

    # 4. L2归一化
    features = features / np.linalg.norm(features)
    return features
```

#### 核函数

```python
def _gaussian_kernel(self, x1, x2):
    """高斯核计算"""
    xx = np.sum(x1**2, axis=1).reshape(-1, 1)
    yy = np.sum(x2**2, axis=1).reshape(1, -1)
    xy = x1 @ x2.T

    d = xx + yy - 2 * xy
    k = np.exp(-1 / (self.sigma**2) * np.abs(d) / d.size)
    return k
```

### 2.3 PSR计算

```python
def _compute_psr(self, response, peak_pos):
    """峰值旁瓣比"""
    peak = response[peak_pos]

    # 创建掩码 (排除峰值周围)
    mask = np.ones_like(response, dtype=bool)
    y, x = peak_pos
    mask[y-r:y+r, x-r:x+r] = False

    # 旁瓣统计
    sidelobe = response[mask]
    mean_sidelobe = np.mean(sidelobe)
    std_sidelobe = np.std(sidelobe)

    psr = (peak - mean_sidelobe) / std_sidelobe
    return psr
```

## 3. 评估指标实现

### 3.1 IoU计算

```python
def compute_iou(bbox1, bbox2):
    """计算IoU"""
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2

    # 交集
    x_left = max(x1, x2)
    y_top = max(y1, y2)
    x_right = min(x1 + w1, x2 + w2)
    y_bottom = min(y1 + h1, y2 + h2)

    intersection = (x_right - x_left) * (y_bottom - y_top)

    # 并集
    union = w1 * h1 + w2 * h2 - intersection

    return intersection / union
```

### 3.2 精度图计算

```python
def compute_precision(center_errors, thresholds):
    """计算精度图"""
    precisions = []
    for threshold in thresholds:
        count = sum(1 for e in center_errors if e <= threshold)
        precisions.append(count / len(center_errors))
    return thresholds, precisions
```

### 3.3 成功率计算

```python
def compute_success_rate(iou_scores, thresholds):
    """计算成功率"""
    success_rates = []
    for threshold in thresholds:
        count = sum(1 for s in iou_scores if s >= threshold)
        success_rates.append(count / len(iou_scores))
    return thresholds, success_rates
```

## 4. 视频跟踪实现

### 4.1 完整跟踪流程

```python
class VideoTracker:
    def process_video(self, video_path):
        # 1. 打开视频
        cap = cv2.VideoCapture(video_path)

        # 2. 读取第一帧
        ret, frame = cap.read()

        # 3. 选择目标
        bbox = self.select_target(frame)

        # 4. 初始化跟踪
        self.init(frame, bbox)

        # 5. 跟踪循环
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 更新跟踪
            success, bbox = self.update(frame)

            # 可视化
            vis = self.draw_visualization(frame, bbox)

            # 显示
            cv2.imshow("Tracking", vis)
```

### 4.2 卡尔曼滤波集成

```python
def update(self, frame):
    # 1. 相关滤波跟踪
    result = self.tracker.update(frame)

    # 2. 卡尔曼滤波平滑
    if self.kalman:
        self.kalman.predict()
        self.kalman.update(np.array(result.center))
        smooth_pos = self.kalman.get_position()

        # 使用平滑后的位置
        self.center = smooth_pos
    else:
        self.center = result.center

    return True, self.bbox
```

## 5. 可视化实现

### 5.1 边界框绘制

```python
def draw_visualization(self, frame, bbox, confidence):
    vis = frame.copy()
    x, y, w, h = bbox

    # 边界框
    cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # 中心点
    cx, cy = int(x + w / 2), int(y + h / 2)
    cv2.circle(vis, (cx, cy), 3, (0, 0, 255), -1)

    # 置信度
    text = f"Conf: {confidence:.2f}"
    cv2.putText(vis, text, (x, y - 10), ...)

    return vis
```

### 5.2 轨迹绘制

```python
# 绘制历史轨迹
for i in range(1, len(self.trajectory)):
    pt1 = (int(self.trajectory[i-1][0]), int(self.trajectory[i-1][1]))
    pt2 = (int(self.trajectory[i][0]), int(self.trajectory[i][1]))
    cv2.line(vis, pt1, pt2, (255, 0, 0), 2)
```

## 6. 合成视频生成

```python
def create_synthetic_video(output_path, width, height, num_frames, target_size, motion_type):
    """创建合成测试视频"""
    writer = cv2.VideoWriter(output_path, ...)

    for i in range(num_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # 更新目标位置
        if motion_type == "linear":
            cx += 3
            cy += 2
        elif motion_type == "circular":
            cx = center_x + radius * cos(angle)
            cy = center_y + radius * sin(angle)

        # 绘制目标
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), -1)

        # 添加噪声
        noise = np.random.randint(0, 20, frame.shape, dtype=np.uint8)
        frame = cv2.add(frame, noise)

        writer.write(frame)
```

## 7. 性能优化

### 7.1 FFT优化

- 使用numpy.fft进行快速傅里叶变换
- 避免不必要的IFFT (只在需要时计算)

### 7.2 内存优化

- 使用float64提高精度
- 避免频繁的数组拷贝
- 使用in-place操作

### 7.3 计算优化

- 限制搜索区域大小
- 使用cell_size降低特征维度
- 批量处理多帧

## 8. 已知限制

1. **尺度固定**: 当前实现不支持尺度估计
2. **遮挡处理**: 缺乏遮挡检测和恢复机制
3. **特征单一**: MOSSE仅使用灰度特征
4. **初始化敏感**: 需要手动选择初始目标
