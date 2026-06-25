"""
滤波器设计示例

演示各种滤波器的设计和特性分析。
"""

import numpy as np
import matplotlib.pyplot as plt
from src.applications import RCFilter, RLCFilter


def compare_filters():
    """比较不同类型的滤波器"""
    print("=" * 60)
    print("滤波器比较")
    print("=" * 60)

    # RC低通滤波器
    rclp = RCFilter(r=1000, c=1e-6, filter_type='low')
    print(f"RC低通: f_c = {rclp.cutoff_frequency():.2f} Hz")

    # RC高通滤波器
    rchp = RCFilter(r=1000, c=1e-6, filter_type='high')
    print(f"RC高通: f_c = {rchp.cutoff_frequency():.2f} Hz")

    # RLC带通滤波器
    rlcbp = RLCFilter(r=100, l=1e-3, c=1e-6, filter_type='bandpass')
    print(f"RLC带通: f_r = {rlcbp.resonance_freq():.2f} Hz, Q = {rlcbp.quality_factor():.2f}")

    # RLC带阻滤波器
    rlcbn = RLCFilter(r=100, l=1e-3, c=1e-6, filter_type='bandstop')
    print(f"RLC带阻: f_r = {rlcbn.resonance_freq():.2f} Hz")

    # 绘制比较图
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    f_start = 10
    f_stop = 1e6

    # RC低通
    fr = rclp.frequency_response(f_start, f_stop)
    axes[0, 0].semilogx(fr.frequencies, 20 * np.log10(fr.magnitude), 'b-', linewidth=2)
    axes[0, 0].axvline(rclp.cutoff_frequency(), color='r', linestyle='--', alpha=0.5)
    axes[0, 0].axhline(-3, color='g', linestyle=':', alpha=0.5)
    axes[0, 0].set_title('RC低通滤波器')
    axes[0, 0].set_xlabel('频率 (Hz)')
    axes[0, 0].set_ylabel('增益 (dB)')
    axes[0, 0].grid(True, which='both', alpha=0.3)
    axes[0, 0].set_ylim(-40, 5)

    # RC高通
    fr = rchp.frequency_response(f_start, f_stop)
    axes[0, 1].semilogx(fr.frequencies, 20 * np.log10(fr.magnitude), 'r-', linewidth=2)
    axes[0, 1].axvline(rchp.cutoff_frequency(), color='b', linestyle='--', alpha=0.5)
    axes[0, 1].axhline(-3, color='g', linestyle=':', alpha=0.5)
    axes[0, 1].set_title('RC高通滤波器')
    axes[0, 1].set_xlabel('频率 (Hz)')
    axes[0, 1].set_ylabel('增益 (dB)')
    axes[0, 1].grid(True, which='both', alpha=0.3)
    axes[0, 1].set_ylim(-40, 5)

    # RLC带通
    fr = rlcbp.frequency_response(f_start, f_stop)
    axes[1, 0].semilogx(fr.frequencies, 20 * np.log10(np.maximum(fr.magnitude, 1e-10)), 'g-', linewidth=2)
    axes[1, 0].axvline(rlcbp.resonance_freq(), color='r', linestyle='--', alpha=0.5)
    axes[1, 0].set_title('RLC带通滤波器')
    axes[1, 0].set_xlabel('频率 (Hz)')
    axes[1, 0].set_ylabel('增益 (dB)')
    axes[1, 0].grid(True, which='both', alpha=0.3)

    # RLC带阻
    fr = rlcbn.frequency_response(f_start, f_stop)
    axes[1, 1].semilogx(fr.frequencies, 20 * np.log10(np.maximum(fr.magnitude, 1e-10)), 'm-', linewidth=2)
    axes[1, 1].axvline(rlcbn.resonance_freq(), color='r', linestyle='--', alpha=0.5)
    axes[1, 1].set_title('RLC带阻滤波器')
    axes[1, 1].set_xlabel('频率 (Hz)')
    axes[1, 1].set_ylabel('增益 (dB)')
    axes[1, 1].grid(True, which='both', alpha=0.3)

    plt.tight_layout()
    plt.savefig('filter_comparison.png', dpi=150)
    plt.close()
    print("\n已保存: filter_comparison.png")


def design_butterworth_lp():
    """设计巴特沃斯低通滤波器 (简化版)"""
    print("\n" + "=" * 60)
    print("巴特沃斯低通滤波器设计")
    print("=" * 60)

    # 设计参数
    f_c = 1000  # 截止频率 1kHz

    # 一阶RC低通
    r1 = 1000
    c1 = 1.0 / (2 * np.pi * f_c * r1)
    filter_1 = RCFilter(r=r1, c=c1, filter_type='low')
    print(f"一阶: R={r1}Ω, C={c1*1e6:.4f}μF")

    # 绘制不同阶数的响应
    fig, ax = plt.subplots(figsize=(10, 6))

    f = np.logspace(1, 6, 1000)

    # 一阶
    h1 = np.array([abs(filter_1.transfer_function(fi)) for fi in f])
    ax.semilogx(f, 20 * np.log10(h1), 'b-', linewidth=2, label='一阶 (-20dB/dec)')

    # 二阶 (级联)
    h2 = h1 ** 2
    ax.semilogx(f, 20 * np.log10(h2), 'r-', linewidth=2, label='二阶 (-40dB/dec)')

    # 三阶
    h3 = h1 ** 3
    ax.semilogx(f, 20 * np.log10(h3), 'g-', linewidth=2, label='三阶 (-60dB/dec)')

    ax.axvline(f_c, color='k', linestyle='--', alpha=0.5, label=f'f_c = {f_c} Hz')
    ax.axhline(-3, color='gray', linestyle=':', alpha=0.5)

    ax.set_xlabel('频率 (Hz)')
    ax.set_ylabel('增益 (dB)')
    ax.set_title('巴特沃斯低通滤波器阶数比较')
    ax.legend()
    ax.grid(True, which='both', alpha=0.3)
    ax.set_xlim(10, 1e6)
    ax.set_ylim(-60, 5)

    plt.tight_layout()
    plt.savefig('butterworth_comparison.png', dpi=150)
    plt.close()
    print("已保存: butterworth_comparison.png")


if __name__ == "__main__":
    compare_filters()
    design_butterworth_lp()
