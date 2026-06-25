# 设计文档: 傅里叶变换

## 1. 架构设计

### 1.1 模块划分

```
fourier-transform/
├── src/
│   ├── dft.py          # 离散傅里叶变换 (DFT/IDFT)
│   ├── fft.py          # 快速傅里叶变换 (FFT/IFFT)
│   ├── spectrum.py     # 频谱分析工具
│   ├── signals.py      # 信号生成工具
│   └── visualization.py # 可视化工具
├── tests/
│   ├── test_dft.py
│   ├── test_fft.py
│   ├── test_spectrum.py
│   └── test_signals.py
└── examples/
    ├── basic_example.py
    ├── signal_analysis.py
    ├── filter_example.py
    └── visualization_example.py
```

### 1.2 依赖关系

```
signals.py (独立)
    ↓
dft.py (独立)
    ↓
fft.py (独立)
    ↓
spectrum.py → dft.py, fft.py
    ↓
visualization.py → spectrum.py, dft.py, fft.py
```

## 2. 核心算法设计

### 2.1 DFT 设计

**接口设计**:
```python
def dft(x: np.ndarray) -> np.ndarray
def idft(X: np.ndarray) -> np.ndarray
```

**实现策略**: 使用 DFT 矩阵的矩阵-向量乘法。

**数学基础**:
```
W = [e^{-j*2*π*k*n/N}] for k,n in [0, N-1]
X = W @ x
```

**时间复杂度**: O(N^2)
**空间复杂度**: O(N^2) (矩阵) 或 O(N) (逐元素计算)

### 2.2 FFT 设计

**接口设计**:
```python
def fft(x: np.ndarray) -> np.ndarray   # 递归实现，自动补零
def ifft(X: np.ndarray) -> np.ndarray  # 逆变换
def fft_radix2(x: np.ndarray) -> np.ndarray  # 迭代实现，要求 2 的幂
```

**递归 FFT 算法**:
```
function FFT(x):
    N = length(x)
    if N == 1: return x

    even = FFT(x[0::2])  // 偶数索引
    odd = FFT(x[1::2])   // 奇数索引

    for k = 0 to N/2-1:
        t = exp(-j*2*π*k/N) * odd[k]
        X[k] = even[k] + t
        X[k + N/2] = even[k] - t

    return X
```

**迭代 FFT 算法 (Radix-2)**:
```
function FFT_Radix2(x):
    N = length(x)
    X = bit_reverse_copy(x)

    for length = 2, 4, 8, ..., N:
        half = length / 2
        twiddle = exp(-j*2*π*[0..half-1] / length)

        for start = 0, length, 2*length, ...:
            for j = 0 to half-1:
                t = twiddle[j] * X[start + j + half]
                X[start + j + half] = X[start + j] - t
                X[start + j] = X[start + j] + t

    return X
```

### 2.3 频谱分析设计

**接口设计**:
```python
def magnitude_spectrum(X) -> np.ndarray    # 幅度谱
def power_spectrum(X) -> np.ndarray        # 功率谱
def phase_spectrum(X) -> np.ndarray        # 相位谱
def frequency_bins(N, fs) -> np.ndarray    # 频率轴
def find_peaks(spectrum, threshold) -> list # 峰值检测
def spectral_centroid(X, fs) -> float      # 频谱质心
```

## 3. 数据流设计

### 3.1 核心流程

```
输入信号 x[n]
    ↓
FFT: X[k] = FFT(x[n])
    ↓
频谱分析:
  - 幅度谱 |X[k]|
  - 功率谱 |X[k]|^2
  - 相位谱 ∠X[k]
    ↓
特征提取:
  - 峰值频率
  - 频谱质心
  - 带宽
    ↓
可视化 / 输出
```

### 3.2 频域滤波流程

```
输入信号 x[n]
    ↓
FFT: X[k]
    ↓
频域滤波: Y[k] = X[k] * H[k]
    ↓
IFFT: y[n] = IFFT(Y[k])
    ↓
输出信号 y[n]
```

## 4. 接口设计

### 4.1 统一接口

所有 FFT 函数接受 numpy 数组，返回复数 numpy 数组。

输入类型:
- 实数数组 `np.ndarray` (float)
- 复数数组 `np.ndarray` (complex)

输出类型:
- 复数数组 `np.ndarray` (complex)

### 4.2 自动补零

`fft()` 函数自动将输入补零到 2 的幂，方便使用。`fft_radix2()` 要求输入长度必须为 2 的幂。

### 4.3 可视化接口

所有绘图函数:
- 可选 `ax` 参数（复用已有 Axes）
- 返回 `ax` 对象（支持链式调用）
- 自动检查 matplotlib 是否可用

## 5. 性能设计

### 5.1 复杂度对比

| 算法 | 时间复杂度 | 空间复杂度 | N=1024 |
|------|-----------|-----------|--------|
| DFT (矩阵) | O(N^2) | O(N^2) | ~1s |
| DFT (循环) | O(N^2) | O(N) | ~10s |
| FFT (递归) | O(N log N) | O(N log N) | ~1ms |
| FFT (迭代) | O(N log N) | O(N) | ~0.5ms |

### 5.2 优化策略

1. **补零到 2 的幂**: 利用 Radix-2 FFT 的高效性
2. **避免重复计算**: 预计算旋转因子
3. **原地计算**: 迭代 FFT 可以原地操作
4. **NumPy 向量化**: 利用 NumPy 的底层优化

## 6. 错误处理设计

### 6.1 输入验证

- 空数组: 返回空数组
- 非 2 的幂 (fft_radix2): 抛出 ValueError
- 非 2D 数组 (fft2d): 抛出 ValueError

### 6.2 数值稳定性

- 避免除以零: 在功率谱 dB 计算中使用 `max(val, 1e-10)`
- 复数处理: 自动转换输入为复数类型
