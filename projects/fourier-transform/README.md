# Fourier Transform Learning Project / 傅里叶变换学习项目

## English Description

A comprehensive learning project for understanding Fourier Transform, implementing DFT and FFT algorithms from scratch, and performing frequency spectrum analysis. This project focuses on building deep understanding through hands-on implementation rather than relying on existing libraries.

## 中文描述

一个全面的傅里叶变换学习项目，从零实现 DFT 和 FFT 算法，并进行频谱分析。本项目注重通过动手实现来建立深刻理解，而非依赖现有库。

---

## Learning Objectives / 学习目标

- Understand the mathematical principles of Fourier Transform / 理解傅里叶变换原理
- Master the FFT (Cooley-Tukey) algorithm / 掌握 FFT 算法
- Learn frequency spectrum analysis techniques / 学会频谱分析
- Compare DFT vs FFT performance / 对比 DFT 与 FFT 性能

---

## Project Structure / 项目结构

```
fourier-transform/
├── src/
│   ├── __init__.py
│   ├── dft.py          # Discrete Fourier Transform implementation
│   ├── fft.py          # Cooley-Tukey FFT algorithm
│   ├── inverse.py      # Inverse FFT/DFT
│   └── spectrum.py     # Spectrum analysis utilities
├── examples/
│   ├── 01_signal_generation.py   # Signal generation demos
│   ├── 02_dft_fft_compare.py     # DFT vs FFT comparison
│   ├── 03_spectrum_analysis.py   # Frequency spectrum analysis
│   └── 04_mixed_signal.py        # Mixed signal decomposition
├── tests/
│   ├── __init__.py
│   ├── test_dft.py
│   ├── test_fft.py
│   ├── test_inverse.py
│   └── test_spectrum.py
├── requirements.txt
└── README.md
```

---

## How to Run / 如何运行

### Install Dependencies / 安装依赖

```bash
pip install -r requirements.txt
```

### Run Examples / 运行示例

```bash
# Signal generation demo
python examples/01_signal_generation.py

# DFT vs FFT comparison
python examples/02_dft_fft_compare.py

# Spectrum analysis
python examples/03_spectrum_analysis.py

# Mixed signal decomposition
python examples/04_mixed_signal.py
```

### Run Tests / 运行测试

```bash
pytest tests/ -v
```

---

## Mathematical Background / 数学背景

### Continuous Fourier Transform / 连续傅里叶变换

$$X(f) = \int_{-\infty}^{\infty} x(t) \cdot e^{-j2\pi ft} dt$$

### Discrete Fourier Transform (DFT) / 离散傅里叶变换

$$X[k] = \sum_{n=0}^{N-1} x[n] \cdot e^{-j2\pi kn/N}, \quad k = 0, 1, ..., N-1$$

### Inverse DFT (IDFT) / 逆离散傅里叶变换

$$x[n] = \frac{1}{N} \sum_{k=0}^{N-1} X[k] \cdot e^{j2\pi kn/N}, \quad n = 0, 1, ..., N-1$$

### FFT Complexity / FFT 复杂度

- DFT: O(N²)
- FFT (Cooley-Tukey): O(N log N)

---

## License / 许可证

MIT License
