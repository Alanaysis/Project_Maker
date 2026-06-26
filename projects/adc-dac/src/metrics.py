"""
信号质量指标模块 (Signal Quality Metrics)
==========================================

计算和分析 ADC/DAC 系统的信号质量指标。

关键指标:
- SNR (Signal-to-Noise Ratio): 信噪比
- SINAD (Signal-to-Noise and Distortion Ratio): 信纳比
- THD (Total Harmonic Distortion): 总谐波失真
- ENOB (Effective Number of Bits): 有效位数
- SFDR (Spurious-Free Dynamic Range): 无杂散动态范围
- NF (Noise Figure): 噪声系数

数学基础:
- SNR = 10*log10(P_signal / P_noise)
- THD = sqrt(V2^2 + V3^2 + ...) / V1
- ENOB = (SNR - 1.76) / 6.02
"""

import numpy as np


def calculate_snr(signal: np.ndarray, noise: np.ndarray) -> float:
    """
    计算信噪比 (SNR)

    SNR = 10 * log10(P_signal / P_noise)

    参数:
        signal: 原始信号
        noise: 噪声信号

    返回:
        SNR (dB)
    """
    signal_power = np.mean(signal ** 2)
    noise_power = np.mean(noise ** 2)

    if noise_power == 0:
        return float("inf")
    if signal_power == 0:
        return float("-inf")

    return 10.0 * np.log10(signal_power / noise_power)


def calculate_sinad(signal: np.ndarray, output: np.ndarray) -> float:
    """
    计算信纳比 (SINAD)

    SINAD = 10 * log10(P_signal / P_noise+distortion)

    参数:
        signal: 原始输入信号
        output: 系统输出信号

    返回:
        SINAD (dB)
    """
    signal_power = np.mean(signal ** 2)
    error = signal - output
    distortion_power = np.mean(error ** 2)

    if distortion_power == 0:
        return float("inf")

    return 10.0 * np.log10(signal_power / distortion_power)


def calculate_thd(signal: np.ndarray, fs: float, num_harmonics: int = 10) -> dict:
    """
    计算总谐波失真 (THD)

    THD = sqrt(V2^2 + V3^2 + ... + Vn^2) / V1

    其中 V1 是基波幅值，V2...Vn 是谐波幅值。

    参数:
        signal: 信号
        fs: 采样频率
        num_harmonics: 谐波数量

    返回:
        dict 包含:
            - thd_linear: THD (线性值)
            - thd_db: THD (dB)
            - thd_percent: THD (百分比)
            - harmonic_magnitudes: 各次谐波幅值
            - harmonic_frequencies: 各次谐波频率
    """
    n = len(signal)
    # 计算 FFT
    fft_result = np.fft.fft(signal)
    fft_magnitude = np.abs(fft_result) / n

    # 只取正频率部分
    half_n = n // 2
    freqs = np.fft.fftfreq(n, 1.0 / fs)
    positive_freqs = freqs[:half_n]
    positive_magnitudes = fft_magnitude[:half_n]

    # 找到基波频率 (最大幅值对应的频率)
    fundamental_idx = np.argmax(positive_magnitudes[1:]) + 1  # 跳过 DC 分量
    fundamental_freq = positive_freqs[fundamental_idx]
    fundamental_mag = positive_magnitudes[fundamental_idx]

    if fundamental_mag == 0:
        return {
            "thd_linear": 0,
            "thd_db": float("-inf"),
            "thd_percent": 0,
            "harmonic_magnitudes": [],
            "harmonic_frequencies": [],
            "fundamental_freq": fundamental_freq,
        }

    # 计算各次谐波幅值
    harmonic_magnitudes = []
    harmonic_frequencies = []

    for h in range(2, num_harmonics + 1):
        harmonic_freq = fundamental_freq * h
        # 找到最接近的 FFT bin
        harmonic_idx = np.argmin(np.abs(positive_freqs - harmonic_freq))

        # 使用插值提高精度
        if harmonic_idx > 0 and harmonic_idx < half_n - 1:
            # 抛物线插值
            x0, x1, x2 = positive_magnitudes[harmonic_idx - 1], positive_magnitudes[harmonic_idx], positive_magnitudes[harmonic_idx + 1]
            p = 0.5 * (x0 - x2) / (x0 - 2 * x1 + x2)
            interpolated_mag = x1 - (x0 - x2) * p / 4
        else:
            interpolated_mag = positive_magnitudes[harmonic_idx]

        harmonic_magnitudes.append(interpolated_mag)
        harmonic_frequencies.append(harmonic_freq)

    # 计算 THD
    harmonic_power = sum(m ** 2 for m in harmonic_magnitudes)
    thd_linear = np.sqrt(harmonic_power) / fundamental_mag
    thd_db = 20 * np.log10(thd_linear) if thd_linear > 0 else float("-inf")
    thd_percent = thd_linear * 100

    return {
        "thd_linear": thd_linear,
        "thd_db": thd_db,
        "thd_percent": thd_percent,
        "harmonic_magnitudes": harmonic_magnitudes,
        "harmonic_frequencies": harmonic_frequencies,
        "fundamental_freq": fundamental_freq,
    }


def calculate_enob(sinad: float) -> float:
    """
    计算有效位数 (ENOB)

    ENOB = (SINAD - 1.76) / 6.02

    理想 ADC 的 ENOB 等于其位数。
    实际 ADC 的 ENOB 通常小于其标称位数。

    参数:
        sinad: 信纳比 (dB)

    返回:
        ENOB (有效位数)
    """
    if sinad <= 1.76:
        return 0.0
    return (sinad - 1.76) / 6.02


def calculate_sfdr(signal: np.ndarray, fs: float) -> dict:
    """
    计算无杂散动态范围 (SFDR)

    SFDR = 20 * log10(V_fundamental / V_spur_max)

    其中 V_spur_max 是最大杂散成分的幅值 (不包括直流和基波)。

    参数:
        signal: 信号
        fs: 采样频率

    返回:
        dict 包含:
            - sfdr_db: SFDR (dB)
            - fundamental_freq: 基频
            - spur_freq: 最大杂散频率
            - spur_mag: 最大杂散幅值
    """
    n = len(signal)
    fft_result = np.fft.fft(signal)
    fft_magnitude = np.abs(fft_result) / n

    half_n = n // 2
    freqs = np.fft.fftfreq(n, 1.0 / fs)
    positive_freqs = freqs[1:half_n]  # 跳过 DC
    positive_magnitudes = fft_magnitude[1:half_n]

    # 找到基波
    fundamental_idx = np.argmax(positive_magnitudes)
    fundamental_mag = positive_magnitudes[fundamental_idx]

    if fundamental_mag == 0:
        return {
            "sfdr_db": 0,
            "fundamental_freq": 0,
            "spur_freq": 0,
            "spur_mag": 0,
        }

    # 找到最大的杂散 (排除基波附近)
    spur_mask = np.abs(positive_freqs - positive_freqs[fundamental_idx]) > fs / n * 2
    if np.any(spur_mask):
        spur_idx = np.argmax(positive_magnitudes[spur_mask])
        spur_mag = positive_magnitudes[spur_mask][spur_idx]
        spur_freq = positive_freqs[spur_mask][spur_idx]
    else:
        spur_mag = 0
        spur_freq = 0

    if spur_mag == 0:
        sfdr_db = float("inf")
    else:
        sfdr_db = 20 * np.log10(fundamental_mag / spur_mag)

    return {
        "sfdr_db": sfdr_db,
        "fundamental_freq": positive_freqs[fundamental_idx],
        "spur_freq": spur_freq,
        "spur_mag": spur_mag,
    }


def calculate_noise_floor(signal: np.ndarray, fs: float, window_size: int = 10) -> float:
    """
    计算噪声底 (Noise Floor)

    通过分析 FFT 中非信号频率处的功率来计算噪声底。

    参数:
        signal: 信号
        fs: 采样频率
        window_size: 频谱分辨率

    返回:
        噪声底 (dBm)
    """
    n = len(signal)
    fft_result = np.fft.fft(signal)
    power_spectrum = np.abs(fft_result) ** 2 / n

    # 排除 DC 和低频分量
    freqs = np.fft.fftfreq(n, 1.0 / fs)
    high_freq_mask = np.abs(freqs) > fs / 100

    if np.sum(high_freq_mask) == 0:
        return 0.0

    noise_power = np.mean(power_spectrum[high_freq_mask])

    # 转换为 dBm (假设 50 欧姆负载)
    noise_floor_dbm = 10 * np.log10(noise_power / 0.001) if noise_power > 0 else float("-inf")

    return noise_floor_dbm


def comprehensive_adc_analysis(original_signal: np.ndarray, reconstructed_signal: np.ndarray,
                               fs: float, num_bits: int) -> dict:
    """
    综合 ADC 分析

    计算所有关键指标并给出分析结果。

    参数:
        original_signal: 原始模拟信号
        reconstructed_signal: 重建后的信号
        fs: 采样频率
        num_bits: ADC 位数

    返回:
        dict 包含所有分析指标
    """
    error = original_signal - reconstructed_signal

    # 计算各项指标
    snr = calculate_snr(original_signal, error)
    sinad = calculate_sinad(original_signal, reconstructed_signal)
    thd_info = calculate_thd(reconstructed_signal, fs)
    enob = calculate_enob(sinad)
    sfdr_info = calculate_sfdr(reconstructed_signal, fs)
    noise_floor = calculate_noise_floor(original_signal, fs)

    # 理论 SNR
    theoretical_snr = 6.02 * num_bits + 1.76

    return {
        "snr": snr,
        "theoretical_snr": theoretical_snr,
        "sinad": sinad,
        "thd": thd_info,
        "enob": enob,
        "theoretical_enob": num_bits,
        "sfdr": sfdr_info,
        "noise_floor_dbm": noise_floor,
        "rms_error": np.sqrt(np.mean(error ** 2)),
        "max_error": np.max(np.abs(error)),
    }
