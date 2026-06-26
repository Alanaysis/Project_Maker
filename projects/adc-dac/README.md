"""
ADC/DAC 模拟 (ADC/DAC Simulation)
===================================

一个用于学习模数/数模转换原理的交互式仿真项目。

本项目实现了完整的 ADC/DAC 仿真流程，包括：
- 采样理论 (奈奎斯特定理、混叠)
- 量化分析 (均匀量化、非均匀量化)
- ADC/DAC 模型
- 重建滤波器
- 信号质量指标 (SNR, THD, ENOB, SFDR)

## 学习目标 / Learning Objectives

### 中文
- 理解 ADC/DAC 工作原理
- 掌握采样定理和量化过程
- 学会信号质量分析和误差评估
- 了解 A-law/mu-law 非均匀量化

### English
- Understand ADC/DAC working principles
- Master sampling theorem and quantization
- Learn signal quality analysis and error evaluation
- Learn about A-law/mu-law non-uniform quantization

## 项目结构 / Project Structure

```
adc-dac/
├── src/                      # 核心模块
│   ├── __init__.py
│   ├── sampling.py           # 采样 (Sampling)
│   ├── quantization.py       # 量化 (Quantization)
│   ├── adc.py                # ADC 模型
│   ├── dac.py                # DAC 模型
│   ├── reconstruction.py     # 重建滤波器
│   └── metrics.py            # 信号质量指标
├── examples/                 # 演示脚本
│   ├── 01_adc_dac_simulation.py
│   ├── 02_quantization_error_analysis.py
│   ├── 03_sampling_rate_effects.py
│   └── 04_snr_vs_bit_depth.py
├── tests/                    # 单元测试
│   ├── test_sampling.py
│   ├── test_quantization.py
│   ├── test_adc_dac.py
│   └── test_reconstruction.py
├── README.md
└── requirements.txt
```

## 快速开始 / Quick Start

### 安装依赖 / Install Dependencies
```bash
pip install -r requirements.txt
```

### 运行示例 / Run Examples
```bash
# 1. ADC/DAC 仿真演示
python examples/01_adc_dac_simulation.py

# 2. 量化误差分析
python examples/02_quantization_error_analysis.py

# 3. 采样率效应
python examples/03_sampling_rate_effects.py

# 4. SNR vs 位数
python examples/04_snr_vs_bit_depth.py
```

### 运行测试 / Run Tests
```bash
pytest tests/ -v
```

## ADC/DAC 理论基础 / Theory Background

### 1. 采样 (Sampling)

**奈奎斯特采样定理**: 要无失真地重建信号，采样频率必须至少是信号最高频率的 2 倍。

$$f_s \geq 2 \cdot f_{max}$$

**混叠 (Aliasing)**: 当采样频率不足时，高频信号会被"折叠"到低频，造成失真。

### 2. 量化 (Quantization)

**均匀量化**: 量化间隔相等。
- 量化级数: $L = 2^B$ (B 为位数)
- 量化步长: $\Delta = V_{range} / L$
- 量化误差范围: $[-\Delta/2, +\Delta/2]$

**非均匀量化**: A-law (欧洲/中国) 和 mu-law (北美/日本) 用于电话系统，对小信号使用更细的量化间隔。

### 3. SNR 公式

理想 ADC 的信噪比:
$$SNR = 6.02 \cdot B + 1.76 \text{ (dB)}$$

其中 B 是量化位数。每增加 1 bit，SNR 提高约 6 dB。

### 4. ENOB (有效位数)

$$ENOB = \frac{SINAD - 1.76}{6.02}$$

ENOB 表示 ADC 的实际有效分辨率，通常小于标称位数。

## 许可证 / License

MIT License

## 作者 / Author

Learning Project Factory
