"""
频谱分析工具

提供幅度谱、功率谱、相位谱、频率轴生成、峰值检测等频谱分析功能。
"""

import numpy as np


def magnitude_spectrum(X: np.ndarray) -> np.ndarray:
    """
    计算幅度谱 (Magnitude Spectrum)

    |X[k]| = sqrt(Re(X[k])^2 + Im(X[k])^2)

    参数:
        X: 频域信号（FFT 输出）

    返回:
        幅度谱，实数数组
    """
    return np.abs(X)


def power_spectrum(X: np.ndarray, normalize: bool = False) -> np.ndarray:
    """
    计算功率谱 (Power Spectrum)

    P[k] = |X[k]|^2

    参数:
        X: 频域信号
        normalize: 是否归一化到 [0, 1]

    返回:
        功率谱
    """
    power = np.abs(X) ** 2
    if normalize and np.max(power) > 0:
        power = power / np.max(power)
    return power


def power_spectrum_db(X: np.ndarray, reference: float = 1.0) -> np.ndarray:
    """
    计算功率谱密度 (dB)

    P_dB[k] = 10 * log10(|X[k]|^2 / reference^2)

    参数:
        X: 频域信号
        reference: 参考值

    返回:
        功率谱密度，单位 dB
    """
    power = np.abs(X) ** 2
    # 避免 log(0)
    power = np.maximum(power, 1e-10)
    return 10 * np.log10(power / (reference ** 2))


def phase_spectrum(X: np.ndarray, unwrap: bool = False) -> np.ndarray:
    """
    计算相位谱 (Phase Spectrum)

    φ[k] = arctan(Im(X[k]) / Re(X[k]))

    参数:
        X: 频域信号
        unwrap: 是否展开相位（去除 2π 跳变）

    返回:
        相位谱，单位弧度
    """
    phase = np.angle(X)
    if unwrap:
        phase = np.unwrap(phase)
    return phase


def frequency_bins(N: int, sample_rate: float) -> np.ndarray:
    """
    生成频率轴

    对于 N 点 FFT，频率范围为 [0, sample_rate/2]（单边谱）
    或 [-sample_rate/2, sample_rate/2]（双边谱）

    参数:
        N: FFT 点数
        sample_rate: 采样率 (Hz)

    返回:
        频率轴数组，长度 N

    示例:
        >>> freqs = frequency_bins(1024, 44100)
        >>> freqs[0]  # DC 分量
        0.0
    """
    return np.fft.fftfreq(N, d=1.0 / sample_rate)


def frequency_bins_positive(N: int, sample_rate: float) -> np.ndarray:
    """
    生成正频率轴（单边谱）

    只包含 [0, sample_rate/2] 的正频率分量。

    参数:
        N: FFT 点数
        sample_rate: 采样率 (Hz)

    返回:
        正频率轴数组，长度 N//2 + 1
    """
    return np.fft.rfftfreq(N, d=1.0 / sample_rate)


def one_sided_spectrum(X: np.ndarray) -> np.ndarray:
    """
    提取单边谱（正频率部分）

    对于实数信号，频谱关于 N/2 对称，只需保留前半部分并乘以 2。

    参数:
        X: FFT 输出

    返回:
        单边频谱
    """
    N = len(X)
    half = N // 2 + 1
    one_sided = X[:half].copy()
    # 除 DC 和 Nyquist 外，幅度乘以 2
    if N % 2 == 0:
        one_sided[1:-1] *= 2
    else:
        one_sided[1:] *= 2
    return one_sided


def find_peaks(
    spectrum: np.ndarray,
    threshold: float = 0.1,
    min_distance: int = 5,
) -> list:
    """
    在频谱中检测峰值

    参数:
        spectrum: 幅度谱或功率谱
        threshold: 相对阈值（相对于最大值的比例）
        min_distance: 峰值之间的最小距离（采样点数）

    返回:
        峰值索引列表

    示例:
        >>> peaks = find_peaks(magnitude, threshold=0.2, min_distance=10)
    """
    if len(spectrum) < 3:
        return list(range(len(spectrum)))

    max_val = np.max(spectrum)
    if max_val == 0:
        return []

    abs_threshold = max_val * threshold
    peaks = []

    for i in range(1, len(spectrum) - 1):
        if (
            spectrum[i] > spectrum[i - 1]
            and spectrum[i] > spectrum[i + 1]
            and spectrum[i] >= abs_threshold
        ):
            # 检查与已有峰值的最小距离
            if not peaks or (i - peaks[-1]) >= min_distance:
                peaks.append(i)

    return peaks


def peak_frequencies(
    X: np.ndarray,
    sample_rate: float,
    threshold: float = 0.1,
    min_distance: int = 5,
) -> list:
    """
    检测频谱峰值并返回对应的频率和幅度

    只返回正频率部分的峰值。

    参数:
        X: FFT 输出
        sample_rate: 采样率
        threshold: 相对阈值
        min_distance: 最小距离

    返回:
        [(频率, 幅度), ...] 列表，按幅度降序排列
    """
    N = len(X)
    half = N // 2
    mag = magnitude_spectrum(X[:half])
    freqs = np.abs(frequency_bins(N, sample_rate)[:half])
    peaks = find_peaks(mag, threshold, min_distance)

    result = [(freqs[p], mag[p]) for p in peaks]
    result.sort(key=lambda x: x[1], reverse=True)
    return result


def spectral_centroid(X: np.ndarray, sample_rate: float) -> float:
    """
    计算频谱质心 (Spectral Centroid)

    频谱质心表示频谱的"重心"，反映信号的频率分布特征。
    高频成分越多，质心越高。

    C = Σ(|f[k]| * |X[k]|) / Σ|X[k]|

    使用正频率部分计算。

    参数:
        X: FFT 输出
        sample_rate: 采样率

    返回:
        频谱质心 (Hz)
    """
    N = len(X)
    half = N // 2
    mag = magnitude_spectrum(X[:half])
    freqs = np.abs(frequency_bins(N, sample_rate)[:half])

    total_magnitude = np.sum(mag)
    if total_magnitude == 0:
        return 0.0

    return np.sum(freqs * mag) / total_magnitude


def bandwidth(X: np.ndarray, sample_rate: float, threshold: float = 0.5) -> float:
    """
    计算信号带宽

    带宽定义为功率超过最大功率 threshold 比例的频率范围。
    使用正频率部分计算。

    参数:
        X: FFT 输出
        sample_rate: 采样率
        threshold: 功率阈值比例

    返回:
        带宽 (Hz)
    """
    N = len(X)
    half = N // 2
    power = power_spectrum(X[:half], normalize=True)
    freqs = np.abs(frequency_bins(N, sample_rate)[:half])

    # 找到功率超过阈值的频率范围
    above_threshold = np.where(power >= threshold)[0]

    if len(above_threshold) == 0:
        return 0.0

    return freqs[above_threshold[-1]] - freqs[above_threshold[0]]


def signal_to_noise_ratio(
    X: np.ndarray, signal_band: tuple, noise_band: tuple
) -> float:
    """
    计算信噪比 (SNR)

    参数:
        X: FFT 输出
        signal_band: 信号频带 (start_index, end_index)
        noise_band: 噪声频带 (start_index, end_index)

    返回:
        SNR (dB)
    """
    power = np.abs(X) ** 2

    signal_power = np.mean(power[signal_band[0]:signal_band[1]])
    noise_power = np.mean(power[noise_band[0]:noise_band[1]])

    if noise_power == 0:
        return float("inf")

    return 10 * np.log10(signal_power / noise_power)
