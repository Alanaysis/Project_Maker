# 04 - 测试文档

## 1. 测试策略

### 1.1 测试层次

| 层次 | 描述 | 覆盖范围 |
|------|------|----------|
| 单元测试 | 测试单个函数/方法 | 边界条件、正常情况 |
| 集成测试 | 测试模块间交互 | 数据流、接口 |
| 系统测试 | 测试完整功能 | 端到端流程 |

### 1.2 测试工具

- pytest: 测试框架
- numpy: 数值计算验证
- cv2: 图像处理测试

## 2. 卡尔曼滤波器测试

### 2.1 测试文件

`tests/test_kalman_filter.py`

### 2.2 测试用例

#### 初始化测试

```python
def test_initialization(self):
    """测试初始化"""
    kf = KalmanFilter(dt=1.0)
    assert kf is not None
    assert kf.dt == 1.0
    assert len(kf.x) == 4
```

#### 状态设置测试

```python
def test_set_state(self):
    """测试状态设置"""
    kf = KalmanFilter()
    kf.set_state(100, 200, 5, 3)

    assert kf.x[0] == 100
    assert kf.x[1] == 200
    assert kf.x[2] == 5
    assert kf.x[3] == 3
```

#### 预测测试

```python
def test_predict(self):
    """测试预测步骤"""
    kf = KalmanFilter(dt=1.0)
    kf.set_state(100, 200, 5, 3)

    predicted = kf.predict()

    # 匀速运动: x' = x + vx * dt
    assert abs(predicted[0] - 105) < 1e-6
    assert abs(predicted[1] - 203) < 1e-6
```

#### 更新测试

```python
def test_update(self):
    """测试更新步骤"""
    kf = KalmanFilter(dt=1.0, measurement_noise=0.1)
    kf.set_state(100, 200, 5, 3)

    kf.predict()
    measurement = np.array([106.0, 204.0])
    updated = kf.update(measurement)

    # 应该接近测量值和预测值的加权平均
    assert abs(updated[0] - 106) < 1.0
```

#### 匀速跟踪测试

```python
def test_constant_velocity_tracking(self):
    """测试匀速运动跟踪"""
    kf = KalmanFilter(dt=1.0, process_noise=1e-3, measurement_noise=1.0)
    kf.set_state(100, 200, 5, 3)

    true_positions = [(100 + 5*i, 200 + 3*i) for i in range(50)]
    measurements = [
        np.array([x + np.random.randn() * 2, y + np.random.randn() * 2])
        for x, y in true_positions
    ]

    errors = []
    for true_pos, meas in zip(true_positions, measurements):
        kf.predict()
        kf.update(meas)
        estimated = kf.get_position()
        error = np.sqrt((estimated[0] - true_pos[0])**2 + ...)
        errors.append(error)

    avg_error = np.mean(errors)
    assert avg_error < 3.0
```

#### 协方差收敛测试

```python
def test_covariance_convergence(self):
    """测试协方差收敛"""
    kf = KalmanFilter(dt=1.0, process_noise=1e-3, measurement_noise=1.0)
    kf.set_state(0, 0)

    initial_uncertainty = kf.get_position_uncertainty()

    for _ in range(50):
        kf.predict()
        kf.update(np.array([0.0, 0.0]))

    final_uncertainty = kf.get_position_uncertainty()

    assert final_uncertainty[0] < initial_uncertainty[0]
```

## 3. 相关滤波器测试

### 3.1 测试文件

`tests/test_correlation_filter.py`

### 3.2 测试用例

#### 初始化测试

```python
def test_initialization(self):
    """测试初始化"""
    tracker = MOSSETracker(learning_rate=0.2)
    assert tracker is not None
    assert not tracker.initialized
```

#### 帧初始化测试

```python
def test_init_with_frame(self):
    """测试用帧初始化"""
    tracker = MOSSETracker()
    frame, bbox = create_test_frame()

    success = tracker.init(frame, bbox)
    assert success
    assert tracker.initialized
```

#### 更新测试

```python
def test_update_after_init(self):
    """测试初始化后的更新"""
    tracker = MOSSETracker()
    frame, bbox = create_test_frame()
    tracker.init(frame, bbox)

    new_frame, _ = create_test_frame(target_pos=(155, 155))
    result = tracker.update(new_frame)

    assert isinstance(result, TrackingResult)
    assert result.confidence >= 0
```

#### 跟踪一致性测试

```python
def test_tracking_consistency(self):
    """测试跟踪一致性"""
    tracker = MOSSETracker(learning_rate=0.3)

    init_pos = (150, 150)
    frame, bbox = create_test_frame(target_pos=init_pos)
    tracker.init(frame, bbox)

    positions = []
    for i in range(10):
        new_pos = (init_pos[0] + 2*i, init_pos[1] + 2*i)
        frame, _ = create_test_frame(target_pos=new_pos)
        result = tracker.update(frame)
        positions.append(result.center)

    # 位置应该变化
    assert positions[-1][0] > positions[0][0]
```

#### PSR计算测试

```python
def test_psr_calculation(self):
    """测试PSR计算"""
    tracker = MOSSETracker()

    response = np.random.randn(10, 10)
    response[5, 5] = 10  # 设置峰值

    psr = tracker._compute_psr(response, (5, 5))
    assert psr > 0
```

#### 高斯响应测试

```python
def test_gaussian_response(self):
    """测试高斯响应创建"""
    tracker = MOSSETracker()
    response = tracker._create_gaussian_response((10, 10), (5, 5))

    # 峰值应该在中心
    assert response[5, 5] == np.max(response)
```

## 4. 评估模块测试

### 4.1 测试文件

`tests/test_evaluation.py`

### 4.2 测试用例

#### IoU测试

```python
def test_perfect_overlap(self):
    """测试完全重叠"""
    bbox = (100, 100, 50, 50)
    iou = compute_iou(bbox, bbox)
    assert abs(iou - 1.0) < 1e-6

def test_no_overlap(self):
    """测试无重叠"""
    bbox1 = (100, 100, 50, 50)
    bbox2 = (300, 300, 50, 50)
    iou = compute_iou(bbox1, bbox2)
    assert iou == 0.0

def test_partial_overlap(self):
    """测试部分重叠"""
    bbox1 = (100, 100, 50, 50)
    bbox2 = (120, 120, 50, 50)
    iou = compute_iou(bbox1, bbox2)
    expected = 900 / 4100
    assert abs(iou - expected) < 1e-6
```

#### 中心误差测试

```python
def test_same_center(self):
    """测试相同中心"""
    bbox = (100, 100, 50, 50)
    error = compute_center_error(bbox, bbox)
    assert error == 0.0

def test_known_distance(self):
    """测试已知距离"""
    bbox1 = (100, 100, 50, 50)
    bbox2 = (130, 140, 50, 50)
    error = compute_center_error(bbox1, bbox2)
    expected = np.sqrt(30**2 + 40**2)
    assert abs(error - expected) < 1e-6
```

#### 精度图测试

```python
def test_perfect_tracking(self):
    """测试完美跟踪"""
    errors = [0.0] * 100
    thresholds, precisions = compute_precision(errors)

    for p in precisions:
        assert p == 1.0
```

#### 评估器测试

```python
def test_evaluate(self):
    """测试评估"""
    evaluator = TrackingEvaluator()

    for i in range(20):
        gt = (100 + 5*i, 100 + 3*i, 50, 50)
        pred = gt  # 完美跟踪
        evaluator.add_frame("perfect", pred, gt)

    result = evaluator.evaluate("perfect")
    assert result["average_iou"] > 0.99
```

## 5. 运行测试

### 5.1 运行所有测试

```bash
cd projects/object-tracking
python -m pytest tests/ -v
```

### 5.2 运行特定测试

```bash
# 运行卡尔曼滤波测试
python -m pytest tests/test_kalman_filter.py -v

# 运行相关滤波测试
python -m pytest tests/test_correlation_filter.py -v

# 运行评估测试
python -m pytest tests/test_evaluation.py -v
```

### 5.3 查看测试覆盖率

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## 6. 测试结果示例

```
tests/test_kalman_filter.py::TestKalmanFilter::test_initialization PASSED
tests/test_kalman_filter.py::TestKalmanFilter::test_set_state PASSED
tests/test_kalman_filter.py::TestKalmanFilter::test_predict PASSED
tests/test_kalman_filter.py::TestKalmanFilter::test_update PASSED
tests/test_kalman_filter.py::TestKalmanFilter::test_constant_velocity_tracking PASSED

tests/test_correlation_filter.py::TestMOSSETracker::test_initialization PASSED
tests/test_correlation_filter.py::TestMOSSETracker::test_init_with_frame PASSED
tests/test_correlation_filter.py::TestMOSSETracker::test_update_after_init PASSED

tests/test_evaluation.py::TestIoU::test_perfect_overlap PASSED
tests/test_evaluation.py::TestIoU::test_no_overlap PASSED
tests/test_evaluation.py::TestCenterError::test_known_distance PASSED
```

## 7. 测试数据

### 7.1 合成测试数据

- 线性运动轨迹
- 圆周运动轨迹
- 随机运动轨迹
- 不同噪声级别

### 7.2 测试帧生成

```python
def create_test_frame(width, height, target_pos, target_size, noise_level):
    """创建测试帧"""
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # 绘制目标
    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), -1)

    # 添加噪声
    noise = np.random.randint(0, noise_level, frame.shape, dtype=np.uint8)
    frame = cv2.add(frame, noise)

    return frame, bbox
```
