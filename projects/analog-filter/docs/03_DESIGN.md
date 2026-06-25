# 模拟滤波器设计文档

## 1. 系统架构

### 1.1 模块划分

```
analog-filter/
├── src/
│   ├── lowpass.py          # 低通滤波器
│   ├── highpass.py         # 高通滤波器
│   ├── bandpass.py         # 带通滤波器
│   ├── bandstop.py         # 带阻滤波器
│   ├── frequency_response.py # 频率响应分析
│   ├── visualization.py    # 可视化工具
│   └── applications.py     # 实际应用
├── tests/
└── examples/
```

### 1.2 类设计

```
RCLowPass          # RC 低通滤波器
RLLowPass          # RL 低通滤波器
RCHighPass         # RC 高通滤波器
RLHighPass         # RL 高通滤波器
RLCBandPass        # RLC 带通滤波器
RLCBandStop        # RLC 带阻滤波器
AudioCrossover     # 音频分频器
NotchFilter        # 陷波滤波器
SignalConditioner  # 信号调理器
```

## 2. 滤波器设计

### 2.1 RC 低通滤波器

**电路参数**:
- R: 电阻值 (Ω)
- C: 电容值 (F)

**计算公式**:
```python
tau = R * C                    # 时间常数
fc = 1 / (2 * pi * tau)       # 截止频率

# 传递函数
H(s) = 1 / (1 + s * tau)

# 幅度响应
|H(jω)| = 1 / sqrt(1 + (ω * tau)^2)

# 相位响应
φ(ω) = -arctan(ω * tau)
```

**设计示例**:
```python
# 设计 1kHz 截止频率的 RC 低通
fc = 1000  # Hz
R = 1000   # Ω
C = 1 / (2 * pi * R * fc)  # ≈ 0.159μF

filt = RCLowPass(R, C)
```

### 2.2 RL 低通滤波器

**电路参数**:
- R: 电阻值 (Ω)
- L: 电感值 (H)

**计算公式**:
```python
tau = L / R                    # 时间常数
fc = R / (2 * pi * L)         # 截止频率

# 传递函数
H(s) = (R/L) / (s + R/L)
```

### 2.3 RC 高通滤波器

**计算公式**:
```python
# 传递函数
H(s) = s * tau / (1 + s * tau)

# 幅度响应
|H(jω)| = ω * tau / sqrt(1 + (ω * tau)^2)
```

### 2.4 RL 高通滤波器

**计算公式**:
```python
# 传递函数
H(s) = s / (s + R/L)
```

### 2.5 RLC 带通滤波器

**电路参数**:
- R: 电阻值 (Ω)
- L: 电感值 (H)
- C: 电容值 (F)

**计算公式**:
```python
omega0 = 1 / sqrt(L * C)      # 中心角频率
f0 = omega0 / (2 * pi)        # 中心频率
bw = 1 / (2 * pi * R * C)     # 带宽
Q = omega0 * R * C             # 品质因数

# 传递函数
H(s) = (s / (R*C)) / (s^2 + s/(R*C) + 1/(L*C))
```

**截止频率**:
```python
# 下截止频率
f_low = f0 * (sqrt(1 + 1/(4*Q^2)) - 1/(2*Q))

# 上截止频率
f_high = f0 * (sqrt(1 + 1/(4*Q^2)) + 1/(2*Q))
```

### 2.6 RLC 带阻滤波器

**计算公式**:
```python
# 传递函数
H(s) = (s^2 + 1/(L*C)) / (s^2 + s/(R*C) + 1/(L*C))
```

**特性**:
- 在中心频率 f0 处增益为 0
- 在直流和无穷大频率处增益为 1

## 3. 频率响应分析设计

### 3.1 频率数组生成

```python
def generate_log_freq(start, stop, num_points):
    """生成对数间隔频率数组"""
    return np.logspace(log10(start), log10(stop), num_points)

def generate_linear_freq(start, stop, num_points):
    """生成线性间隔频率数组"""
    return np.linspace(start, stop, num_points)
```

### 3.2 截止频率检测

```python
def find_cutoff_frequency(f, mag_db, attenuation=-3.0):
    """查找 -3dB 截止频率"""
    # 找到最大增益
    max_gain = max(mag_db)
    target = max_gain + attenuation  # attenuation 为负值

    # 找到第一个低于目标的频率点
    # 使用线性插值提高精度
```

### 3.3 滤波器级联

```python
def cascade_transfer_functions(filters, f):
    """级联多个滤波器的传递函数"""
    H_total = 1
    for filt in filters:
        H_total *= filt.transfer_function(f)
    return H_total
```

## 4. 应用模块设计

### 4.1 音频分频器

```python
class AudioCrossover:
    def __init__(self, crossover_freq, R=1000):
        # 计算电容值
        C = 1 / (2 * pi * R * crossover_freq)
        self.lowpass = RCLowPass(R, C)
        self.highpass = RCHighPass(R, C)

    def process(self, signal, t, channel='low'):
        # 频域滤波
        # FFT -> 应用滤波器 -> IFFT
```

### 4.2 陷波滤波器

```python
class NotchFilter:
    def __init__(self, notch_freq, Q=30):
        # 设计 RLC 参数
        L = 1  # 1H
        C = 1 / ((2*pi*notch_freq)^2 * L)
        R = (1/Q) * sqrt(L/C)
        self.bandstop = RLCBandStop(R, L, C)
```

### 4.3 信号调理器

```python
class SignalConditioner:
    def __init__(self, fs):
        self.fs = fs

    def remove_dc_offset(self, signal, t, cutoff=1.0):
        # 高通滤波

    def remove_powerline_hum(self, signal, t, freq=50):
        # 陷波滤波

    def band_limit(self, signal, t, f_low, f_high):
        # 带通滤波
```

## 5. 可视化设计

### 5.1 波特图

```python
def plot_bode(filter_obj, f, title="波特图"):
    """绘制波特图"""
    fig, (ax1, ax2) = plt.subplots(2, 1)

    # 幅频响应
    ax1.semilogx(f, filter_obj.magnitude_db(f))
    ax1.set_ylabel('幅度 (dB)')

    # 相频响应
    ax2.semilogx(f, filter_obj.phase(f))
    ax2.set_ylabel('相位 (度)')
    ax2.set_xlabel('频率 (Hz)')
```

### 5.2 对比图

```python
def plot_comparison(filters, f, labels=None):
    """对比多个滤波器"""
    for filt, label in zip(filters, labels):
        plt.semilogx(f, filt.magnitude_db(f), label=label)
    plt.legend()
```

## 6. 数据流设计

### 6.1 滤波器创建流程

```
用户输入参数
    ↓
参数验证 (R > 0, L > 0, C > 0)
    ↓
计算派生参数 (τ, fc, Q)
    ↓
创建滤波器对象
```

### 6.2 频率响应计算流程

```
输入频率数组 f
    ↓
计算角频率 ω = 2πf
    ↓
计算复频率 s = jω
    ↓
代入传递函数 H(s)
    ↓
计算幅度 |H| 和相位 ∠H
    ↓
返回结果
```

### 6.3 信号处理流程

```
输入信号 x(t)
    ↓
FFT: X(f) = FFT{x(t)}
    ↓
应用滤波器: Y(f) = H(f) × X(f)
    ↓
IFFT: y(t) = IFFT{Y(f)}
    ↓
输出信号 y(t)
```

## 7. 错误处理设计

### 7.1 参数验证

```python
def __init__(self, R, C):
    if R <= 0:
        raise ValueError("电阻值 R 必须为正数")
    if C <= 0:
        raise ValueError("电容值 C 必须为正数")
```

### 7.2 数值稳定性

```python
# 避免 log(0) 错误
mag_db = 20 * log10(max(mag, 1e-30))
```

## 8. 测试设计

### 8.1 单元测试策略

- 测试构造函数参数验证
- 测试直流增益 (f → 0)
- 测试截止频率处增益 (-3dB)
- 测试高频衰减速率
- 测试相位范围
- 测试阶跃响应特性

### 8.2 集成测试策略

- 测试滤波器级联
- 测试实际信号处理
- 测试应用模块

## 9. 性能优化

### 9.1 向量化计算

使用 NumPy 向量化操作，避免 Python 循环：

```python
# 好: 向量化
magnitude = np.abs(H)

# 差: 循环
magnitude = [abs(h) for h in H]
```

### 9.2 内存优化

- 使用就地操作减少内存分配
- 避免不必要的数组复制
