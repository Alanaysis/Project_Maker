# 数字滤波器 (Digital Filter)

基于 Python 的数字滤波器设计与分析库，支持 FIR 和 IIR 滤波器的设计、频率响应分析和实际信号处理应用。

## 功能特性

### FIR 滤波器
- **窗函数法**: Hamming、Hanning、Blackman、Kaiser 等窗函数
- **频率采样法**: 基于理想频率响应采样的滤波器设计
- 支持低通、高通、带通、带阻滤波器

### IIR 滤波器
- **Butterworth**: 最大平坦幅频响应
- **Chebyshev Type I**: 等纹波通带，陡峭过渡带
- **Chebyshev Type II**: 等纹波阻带，平坦通带
- **椭圆滤波器 (Elliptic/Cauer)**: 最陡峭过渡带，通带和阻带均有纹波

### 滤波器设计
- 低通 / 高通 / 带通 / 带阻
- 阶数自动选择与手动指定
- 第二阶节 (SOS) 表示，提高数值稳定性

### 频率响应分析
- 幅频响应 (Magnitude Response)
- 相频响应 (Phase Response)
- 群延迟 (Group Delay)
- 多滤波器对比图

### 实际应用
- 音频滤波与去噪
- 信号去噪 (宽带噪声、窄带干扰)
- 多策略去噪对比

## 项目结构

```
digital-filter/
├── src/
│   ├── __init__.py          # 包入口
│   ├── fir.py               # FIR 滤波器实现
│   ├── iir.py               # IIR 滤波器实现
│   ├── response.py          # 频率响应分析
│   └── utils.py             # 工具函数 (信号生成、可视化)
├── tests/
│   ├── test_fir.py          # FIR 滤波器测试
│   └── test_iir.py          # IIR 滤波器测试
├── examples/
│   ├── audio_filter.py      # 音频滤波示例
│   ├── signal_denoising.py  # 信号去噪示例
│   └── freq_response.py     # 频率响应对比示例
├── docs/
│   ├── 01_RESEARCH.md       # 研究文档
│   ├── 02_REQUIREMENTS.md   # 需求文档
│   ├── 03_DESIGN.md         # 设计文档
│   ├── 04_PRODUCT.md        # 产品文档
│   └── 05_DEVELOPMENT.md    # 开发文档
├── requirements.txt
└── README.md
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### FIR 低通滤波器

```python
from src.fir import fir_lowpass
from src.utils import generate_signal, add_noise

# 生成含噪信号
t, clean = generate_signal(fs=1000, components=[(50, 1.0), (200, 0.5)])
noisy = add_noise(clean, snr_db=15)

# 设计 FIR 低通滤波器 (截止频率 80Hz)
filt = fir_lowpass(cutoff=80, num_taps=101, fs=1000)

# 应用零相位滤波
filtered = filt.apply_filtfilt(noisy)
```

### IIR Butterworth 滤波器

```python
from src.iir import butterworth_lowpass

filt = butterworth_lowpass(cutoff=80, order=6, fs=1000)
filtered = filt.apply_filtfilt(noisy)
```

### 频率响应可视化

```python
from src.response import plot_response

plot_response(filt.b, filt.a, fs=1000, title="Butterworth LP", save_path="response.png")
```

### 运行示例

```bash
cd examples
python audio_filter.py
python signal_denoising.py
python freq_response.py
```

## 滤波器类型对比

| 滤波器类型 | 通带平坦度 | 过渡带陡度 | 相位线性 | 阶数效率 |
|-----------|-----------|-----------|---------|---------|
| FIR (窗函数) | 好 | 中等 | 线性 | 低 |
| Butterworth | 最平坦 | 缓 | 非线性 | 中 |
| Chebyshev I | 有纹波 | 陡 | 非线性 | 高 |
| Chebyshev II | 平坦 | 陡 | 非线性 | 高 |
| Elliptic | 有纹波 | 最陡 | 非线性 | 最高 |

## 测试

```bash
cd digital-filter
python -m pytest tests/ -v
```
