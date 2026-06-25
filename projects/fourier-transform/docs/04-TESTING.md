# 测试文档: 傅里叶变换

## 1. 测试策略

### 1.1 测试层次

1. **单元测试**: 每个函数的独立测试
2. **集成测试**: 模块间协作测试
3. **性质测试**: 数学性质验证
4. **对比测试**: 与 numpy.fft 对比

### 1.2 测试覆盖

| 模块 | 测试文件 | 测试用例数 |
|------|---------|-----------|
| dft.py | test_dft.py | 20+ |
| fft.py | test_fft.py | 25+ |
| spectrum.py | test_spectrum.py | 30+ |
| signals.py | test_signals.py | 15+ |

## 2. DFT 测试

### 2.1 基本功能

- 空输入、单元素输入
- 常数信号（只有 DC 分量）
- 纯正弦波（峰值在正确频率）
- 复数输入

### 2.2 正确性验证

```python
def test_dft_matches_numpy():
    """DFT 结果与 numpy.fft.fft 一致"""
    x = np.random.randn(16)
    X_ours = dft(x)
    X_numpy = np.fft.fft(x)
    assert np.allclose(X_ours, X_numpy, atol=1e-10)
```

### 2.3 数学性质

- **线性**: DFT(ax + by) = a*DFT(x) + b*DFT(y)
- **Parseval 定理**: 时域和频域能量相等
- **循环移位**: 时域移位 = 频域乘旋转因子
- **共轭对称性**: X[k] = conj(X[N-k]) (实数信号)

### 2.4 IDFT 测试

- DFT + IDFT 往返恢复
- 与 numpy.fft.ifft 对比
- 脉冲信号 ↔ 常数频谱

## 3. FFT 测试

### 3.1 基本功能

- 各种长度: 1, 2, 4, 8, ..., 1024
- 非 2 的幂自动补零
- 复数输入

### 3.2 正确性验证

```python
def test_fft_matches_numpy():
    """FFT 结果与 numpy.fft.fft 一致"""
    for N in [4, 8, 16, 32, 64, 128]:
        x = np.random.randn(N)
        assert np.allclose(fft(x), np.fft.fft(x), atol=1e-10)
```

### 3.3 递归 vs 迭代

```python
def test_radix2_matches_recursive():
    """迭代和递归实现一致"""
    x = np.random.randn(32)
    assert np.allclose(fft(x), fft_radix2(x), atol=1e-10)
```

### 3.4 IFFT 测试

- FFT + IFFT 往返恢复
- 非 2 的幂长度处理
- 与 numpy.fft.ifft 对比

### 3.5 二维 FFT

- 常数矩阵
- 与 numpy.fft.fft2 对比
- 可分离性验证

### 3.6 边界情况

- 全零信号
- 非常小/大的值
- 交替信号 (+1, -1, ...)
- 单位脉冲

### 3.7 性能测试

```python
@pytest.mark.slow
def test_fft_faster_than_dft():
    """FFT 比 DFT 快"""
    # N=1024 时，FFT 应该至少快 5 倍
```

## 4. 频谱分析测试

### 4.1 幅度谱

- 常数信号只有 DC 分量
- 纯正弦波在正确频率有峰值
- 非负性
- 对称性 (实数信号)

### 4.2 功率谱

- 功率 = 幅度^2
- 归一化后最大值为 1
- dB 计算正确

### 4.3 相位谱

- 余弦波相位为 0
- 正弦波相位为 -π/2
- 相位展开

### 4.4 频率轴

- 基本长度和范围
- Nyquist 频率正确
- 频率分辨率

### 4.5 峰值检测

- 单峰、多峰
- 阈值过滤
- 最小距离约束
- 与 FFT 结合

### 4.6 频谱特征

- 频谱质心: 低频信号 vs 高频信号
- 带宽: 窄带 vs 宽带信号

## 5. 信号生成测试

### 5.1 正弦波

- 频率正确性（FFT 验证）
- 幅度正确性
- 持续时间
- 相位

### 5.2 其他信号

- 方波: 只有 +1/-1
- 锯齿波: 范围 [-1, 1]
- 三角波: 对称性
- 白噪声: 统计特性

## 6. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块
pytest tests/test_dft.py -v
pytest tests/test_fft.py -v
pytest tests/test_spectrum.py -v

# 运行并显示覆盖率
pytest tests/ -v --tb=short

# 跳过慢测试
pytest tests/ -v -m "not slow"
```

## 7. 测试数据

使用 `np.random.seed(42)` 确保测试可重复。

参考实现: `numpy.fft.fft` 和 `numpy.fft.ifft`。
