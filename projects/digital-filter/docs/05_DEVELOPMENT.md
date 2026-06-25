# 开发文档：数字滤波器

## 1. 环境配置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 依赖说明
- `numpy>=1.24.0`: 数值计算基础
- `scipy>=1.10.0`: 信号处理核心算法 (滤波器设计、滤波)
- `matplotlib>=3.7.0`: 可视化

## 2. 项目结构

```
digital-filter/
├── src/
│   ├── __init__.py     # 包入口，导出所有公共 API
│   ├── fir.py          # FIR 滤波器设计与实现
│   ├── iir.py          # IIR 滤波器设计与实现
│   ├── response.py     # 频率响应计算与绘图
│   └── utils.py        # 信号生成、噪声、SNR、绘图工具
├── tests/
│   ├── test_fir.py     # FIR 滤波器测试
│   └── test_iir.py     # IIR 滤波器测试
├── examples/
│   ├── audio_filter.py     # 音频滤波示例
│   ├── signal_denoising.py # 信号去噪示例
│   └── freq_response.py    # 频率响应对比示例
└── docs/
    ├── 01_RESEARCH.md
    ├── 02_REQUIREMENTS.md
    ├── 03_DESIGN.md
    ├── 04_PRODUCT.md
    └── 05_DEVELOPMENT.md
```

## 3. 核心实现

### 3.1 FIR 滤波器 (fir.py)

**FIRFilter 类**:
- 封装滤波器系数和采样率
- 提供 `apply()` 和 `apply_filtfilt()` 方法
- 使用 `scipy.signal.lfilter` 和 `scipy.signal.filtfilt`

**工厂函数**:
- `fir_lowpass()`: 使用 `scipy.signal.firwin` 设计低通滤波器
- `fir_highpass()`: 设置 `pass_zero=False`
- `fir_bandpass()`: 设置双截止频率
- `fir_bandstop()`: 设置 `pass_zero=True`
- `fir_frequency_sampling()`: 使用 IFFT + 窗函数

### 3.2 IIR 滤波器 (iir.py)

**IIRFilter 类**:
- 封装分子 (b) 和分母 (a) 系数
- 提供 `apply()`、`apply_filtfilt()`、`apply_sos()` 方法
- `sos()` 属性转换为第二阶节表示

**工厂函数**:
- `butterworth_*()`: 使用 `scipy.signal.butter`
- `chebyshev1_*()`: 使用 `scipy.signal.cheby1`
- `chebyshev2_*()`: 使用 `scipy.signal.cheby2`
- `elliptic_*()`: 使用 `scipy.signal.ellip`

### 3.3 频率响应 (response.py)

- `frequency_response()`: 使用 `scipy.signal.freqz` 计算频率响应
- `plot_response()`: 绘制幅频 + 相频双子图
- `plot_filter_comparison()`: 多滤波器叠加对比
- `group_delay()`: 使用 `scipy.signal.group_delay`

### 3.4 工具函数 (utils.py)

- `generate_signal()`: 生成多频率正弦叠加信号
- `add_noise()`: 按指定 SNR 添加高斯白噪声
- `snr()`: 计算信噪比
- `plot_comparison()`: 多信号时域对比图
- `plot_spectrum()`: FFT 频谱图

## 4. 开发规范

### 4.1 代码风格
- 遵循 PEP 8
- 使用类型提示 (type hints)
- 完整的 docstring (Google 风格)

### 4.2 测试规范
- 每个模块对应一个测试文件
- 使用 pytest 框架
- 测试覆盖：构造函数、滤波功能、边界条件

### 4.3 提交规范
```
feat: 新增 XXX 滤波器
fix: 修复 XXX 问题
docs: 更新文档
test: 新增测试用例
```

## 5. 运行测试

```bash
cd digital-filter
python -m pytest tests/ -v
```

## 6. 运行示例

```bash
cd examples
python audio_filter.py
python signal_denoising.py
python freq_response.py
```

输出保存在 `output/` 目录。
