# 设计文档：数字滤波器

## 1. 架构概览

```
digital-filter/
├── src/
│   ├── fir.py       # FIR 滤波器：设计 + 滤波操作
│   ├── iir.py       # IIR 滤波器：设计 + 滤波操作
│   ├── response.py  # 频率响应计算与可视化
│   └── utils.py     # 信号生成、噪声、SNR、绘图工具
└── tests/
    ├── test_fir.py
    └── test_iir.py
```

## 2. 模块设计

### 2.1 FIR 模块 (`fir.py`)

**类**: `FIRFilter`
- `__init__(coefficients, fs)`: 初始化滤波器系数和采样率
- `apply(x)`: 单向滤波 (lfilter)
- `apply_filtfilt(x)`: 零相位滤波 (filtfilt)
- `order` 属性: 滤波器阶数

**工厂函数**:
- `fir_lowpass(cutoff, num_taps, fs, window)` → FIRFilter
- `fir_highpass(cutoff, num_taps, fs, window)` → FIRFilter
- `fir_bandpass(low, high, num_taps, fs, window)` → FIRFilter
- `fir_bandstop(low, high, num_taps, fs, window)` → FIRFilter
- `fir_frequency_sampling(desired, fs, window)` → FIRFilter

**设计流程 (窗函数法)**:
```
输入: 截止频率 fc, 采样率 fs, 窗口类型 win
  ↓
归一化: fc_norm = fc / (fs/2)
  ↓
scipy.firwin(N, fc_norm, window=win)
  ↓
返回 FIRFilter(h, fs)
```

**设计流程 (频率采样法)**:
```
输入: 期望频率响应 H_d[k], 采样率 fs
  ↓
IDFT: h = ifft(H_d)
  ↓
循环移位: h = roll(h, N//2)
  ↓
加窗: h = h * window
  ↓
返回 FIRFilter(h, fs)
```

### 2.2 IIR 模块 (`iir.py`)

**类**: `IIRFilter`
- `__init__(b, a, fs)`: 初始化分子/分母系数
- `apply(x)`: 单向滤波
- `apply_filtfilt(x)`: 零相位滤波
- `apply_sos(x)`: SOS 形式滤波 (数值稳定)
- `sos()` 属性: 转换为 SOS 表示
- `order` 属性: 滤波器阶数

**工厂函数**:
- `butterworth_lowpass/highpass/bandpass/bandstop(cutoff, order, fs)`
- `chebyshev1_lowpass/highpass(cutoff, order, ripple, fs)`
- `chebyshev2_lowpass/highpass(cutoff, order, attenuation, fs)`
- `elliptic_lowpass/highpass/bandpass(cutoff, order, ripple, attenuation, fs)`

**设计流程**:
```
输入: 截止频率 fc, 阶数 N, 采样率 fs, 纹波/衰减参数
  ↓
归一化: fc_norm = fc / (fs/2)
  ↓
scipy.butter/cheby1/cheby2/ellip(N, fc_norm, btype)
  ↓
返回 IIRFilter(b, a, fs)
```

### 2.3 频率响应模块 (`response.py`)

**函数**:
- `frequency_response(b, a, fs, worN)` → (freqs, mag_db, phase_deg)
- `plot_response(b, a, fs, title, save_path)`: 绘制幅频+相频响应
- `plot_filter_comparison(filters, labels, ...)`: 多滤波器对比图
- `group_delay(b, a, fs, worN)`: 计算群延迟

### 2.4 工具模块 (`utils.py`)

**函数**:
- `generate_signal(duration, fs, components)` → (t, x)
- `add_noise(x, snr_db)` → noisy_x
- `snr(clean, noisy)` → snr_db
- `plot_comparison(t, signals, labels, ...)`: 多信号对比图
- `plot_spectrum(x, fs, ...)`: 频谱图

## 3. API 设计原则

### 3.1 统一接口
所有滤波器工厂函数返回 `FIRFilter` 或 `IIRFilter` 对象，提供相同的 `apply()` 和 `apply_filtfilt()` 方法。

### 3.2 参数约定
- 频率参数统一使用 Hz
- 采样率 `fs` 默认 1.0 (归一化频率)
- 阶数/抽头数为整数

### 3.3 级联设计
```python
# FIR + IIR 级联
fir = fir_lowpass(200, 51, 1000)
iir = butterworth_lowpass(100, 4, 1000)
y = iir.apply(fir.apply(x))
```

## 4. 数值稳定性

### 4.1 FIR 滤波器
- 总是稳定 (无反馈)
- 直接卷积实现

### 4.2 IIR 滤波器
- 高阶滤波器使用 SOS 表示避免系数精度问题
- `apply_sos()` 使用 `scipy.signal.sosfilt`
- `filtfilt()` 消除相位失真

## 5. 可视化设计

### 5.1 频率响应图
- 上图: 幅频响应 (dB vs Hz)
- 下图: 相频响应 (度 vs Hz)
- 网格线、轴标签、图例

### 5.2 信号对比图
- 多子图纵向排列，共享 x 轴
- 每个子图标注信号名称
- 支持保存为 PNG
