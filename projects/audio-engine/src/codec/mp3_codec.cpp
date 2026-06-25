// mp3_codec.cpp - MP3 编码概念演示
//
// 本文件介绍 MP3 编码的基本原理（概念演示，非完整实现）：
// 1. MP3 编码流程
// 2. 心理声学模型
// 3. MDCT 变换
// 4. 熵编码
//
// 编译: g++ -std=c++17 -I../../include mp3_codec.cpp -o mp3_codec -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 演示 MP3 编码流程
void demo_mp3_encoding_flow() {
    print_separator("MP3 编码流程");

    std::cout << "\nMP3 编码流程:\n" << std::endl;

    std::cout << "输入 PCM 数据" << std::endl;
    std::cout << "     │" << std::endl;
    std::cout << "     ▼" << std::endl;
    std::cout << "┌─────────────────────────────────────┐" << std::endl;
    std::cout << "│ 1. 分析滤波器组 (Analysis Filterbank) │" << std::endl;
    std::cout << "│    - 将信号分成 32 个子带             │" << std::endl;
    std::cout << "└─────────────────────────────────────┘" << std::endl;
    std::cout << "     │" << std::endl;
    std::cout << "     ▼" << std::endl;
    std::cout << "┌─────────────────────────────────────┐" << std::endl;
    std::cout << "│ 2. MDCT 变换                         │" << std::endl;
    std::cout << "│    - 改进离散余弦变换                 │" << std::endl;
    std::cout << "│    - 提高频率分辨率                   │" << std::endl;
    std::cout << "└─────────────────────────────────────┘" << std::endl;
    std::cout << "     │" << std::endl;
    std::cout << "     ▼" << std::endl;
    std::cout << "┌─────────────────────────────────────┐" << std::endl;
    std::cout << "│ 3. 心理声学模型 (Psychoacoustic Model)│" << std::endl;
    std::cout << "│    - 计算掩蔽阈值                     │" << std::endl;
    std::cout << "│    - 确定可忽略的频率成分             │" << std::endl;
    std::cout << "└─────────────────────────────────────┘" << std::endl;
    std::cout << "     │" << std::endl;
    std::cout << "     ▼" << std::endl;
    std::cout << "┌─────────────────────────────────────┐" << std::endl;
    std::cout << "│ 4. 量化 (Quantization)               │" << std::endl;
    std::cout << "│    - 根据掩蔽阈值量化频谱系数         │" << std::endl;
    std::cout << "│    - 比特分配优化                     │" << std::endl;
    std::cout << "└─────────────────────────────────────┘" << std::endl;
    std::cout << "     │" << std::endl;
    std::cout << "     ▼" << std::endl;
    std::cout << "┌─────────────────────────────────────┐" << std::endl;
    std::cout << "│ 5. 熵编码 (Huffman Coding)           │" << std::endl;
    std::cout << "│    - 无损压缩量化系数                 │" << std::endl;
    std::cout << "└─────────────────────────────────────┘" << std::endl;
    std::cout << "     │" << std::endl;
    std::cout << "     ▼" << std::endl;
    std::cout << "输出 MP3 比特流" << std::endl;
}

// 演示心理声学模型概念
void demo_psychoacoustic_model() {
    print_separator("心理声学模型");

    std::cout << "\n心理声学模型利用人耳的特性进行压缩:\n" << std::endl;

    std::cout << "1. 绝对听阈 (Absolute Threshold of Hearing)" << std::endl;
    std::cout << "   - 人耳能听到的最小声音" << std::endl;
    std::cout << "   - 频率依赖：2-4 kHz 最敏感" << std::endl;

    std::cout << "\n2. 频率掩蔽 (Frequency Masking)" << std::endl;
    std::cout << "   - 强信号会掩蔽邻近频率的弱信号" << std::endl;
    std::cout << "   - 掩蔽范围取决于信号强度和频率" << std::endl;

    std::cout << "\n3. 时间掩蔽 (Temporal Masking)" << std::endl;
    std::cout << "   - 前掩蔽：强信号前 5-20ms" << std::endl;
    std::cout << "   - 后掩蔽：强信号后 50-200ms" << std::endl;

    std::cout << "\n4. 临界频带 (Critical Bands)" << std::endl;
    std::cout << "   - 人耳将频率分成约 25 个临界频带" << std::endl;
    std::cout << "   - 每个频带内发生掩蔽效应" << std::endl;

    // 显示临界频带示例
    std::cout << "\n临界频带示例:" << std::endl;
    std::cout << "频带 | 中心频率 | 带宽" << std::endl;
    std::cout << "-----|---------|------" << std::endl;
    std::cout << "  1  |  100 Hz | 100 Hz" << std::endl;
    std::cout << "  5  |  500 Hz | 100 Hz" << std::endl;
    std::cout << " 10  | 1500 Hz | 200 Hz" << std::endl;
    std::cout << " 15  | 3500 Hz | 700 Hz" << std::endl;
    std::cout << " 20  | 8000 Hz | 2500 Hz" << std::endl;
}

// 演示 MP3 帧结构
void demo_mp3_frame() {
    print_separator("MP3 帧结构");

    std::cout << "\nMP3 帧结构:\n" << std::endl;

    std::cout << "┌─────────────────────────────────┐" << std::endl;
    std::cout << "│ Frame Header (4 bytes)          │" << std::endl;
    std::cout << "│   - Sync word (11 bits)         │" << std::endl;
    std::cout << "│   - Version (2 bits)            │" << std::endl;
    std::cout << "│   - Layer (2 bits)              │" << std::endl;
    std::cout << "│   - Protection (1 bit)          │" << std::endl;
    std::cout << "│   - Bitrate (4 bits)            │" << std::endl;
    std::cout << "│   - Sample rate (2 bits)        │" << std::endl;
    std::cout << "│   - Padding (1 bit)             │" << std::endl;
    std::cout << "│   - Channel mode (2 bits)       │" << std::endl;
    std::cout << "├─────────────────────────────────┤" << std::endl;
    std::cout << "│ CRC (optional, 2 bytes)         │" << std::endl;
    std::cout << "├─────────────────────────────────┤" << std::endl;
    std::cout << "│ Main Data (variable)            │" << std::endl;
    std::cout << "│   - Scale factors               │" << std::endl;
    std::cout << "│   - Huffman coded data          │" << std::endl;
    std::cout << "│   - Side information             │" << std::endl;
    std::cout << "└─────────────────────────────────┘" << std::endl;

    std::cout << "\nMP3 帧特性:" << std::endl;
    std::cout << "  - 每帧 1152 采样点 (Layer III)" << std::endl;
    std::cout << "  - 44.1kHz 时约 26ms 每帧" << std::endl;
    std::cout << "  - 比特率范围: 32-320 kbps" << std::endl;
}

// 演示 MP3 比特率
void demo_mp3_bitrates() {
    print_separator("MP3 比特率");

    std::cout << "\nMP3 比特率与质量:\n" << std::endl;

    struct BitrateInfo {
        int bitrate;
        const char* quality;
        const char* application;
    };

    std::vector<BitrateInfo> bitrates = {
        {32, "低", "语音"},
        {64, "中低", "网络广播"},
        {96, "中", "普通音乐"},
        {128, "中高", "标准音乐"},
        {160, "高", "高质量音乐"},
        {192, "很高", "发烧友"},
        {256, "极好", "接近无损"},
        {320, "最佳", "MP3 最高质量"}
    };

    std::cout << "比特率 (kbps) | 质量   | 应用场景" << std::endl;
    std::cout << "--------------|--------|----------" << std::endl;

    for (const auto& info : bitrates) {
        printf("%11d   | %-6s | %s\n",
               info.bitrate, info.quality, info.application);
    }

    std::cout << "\n注意: VBR (可变比特率) 可以在不同段落使用不同比特率" << std::endl;
}

// 演示 MP3 vs 其他格式
void demo_mp3_comparison() {
    print_separator("MP3 vs 其他格式");

    std::cout << "\nMP3 与其他格式对比:\n" << std::endl;

    std::cout << "格式  | 压缩类型 | 典型比特率  | 延迟 | 专利" << std::endl;
    std::cout << "------|---------|------------|------|------" << std::endl;
    std::cout << "WAV   | 无压缩  | ~1411 kbps | 无   | 无" << std::endl;
    std::cout << "FLAC  | 无损    | ~800 kbps  | 低   | 无" << std::endl;
    std::cout << "MP3   | 有损    | 128-320k   | 中   | 已过期" << std::endl;
    std::cout << "AAC   | 有损    | 96-256k    | 中   | 部分" << std::endl;
    std::cout << "Opus  | 有损    | 32-256k    | 低   | 无" << std::endl;

    std::cout << "\nMP3 的优缺点:" << std::endl;
    std::cout << "  优点:" << std::endl;
    std::cout << "    - 兼容性最好" << std::endl;
    std::cout << "    - 硬件支持广泛" << std::endl;
    std::cout << "    - 编码器成熟" << std::endl;
    std::cout << "  缺点:" << std::endl;
    std::cout << "    - 效率不如 AAC/Opus" << std::endl;
    std::cout << "    - 高频损失明显" << std::endl;
    std::cout << "    - 不支持多声道" << std::endl;
}

// 简化的频谱分析演示
void demo_spectrum_analysis() {
    print_separator("频谱分析演示");

    std::cout << "\nMP3 编码依赖频谱分析:\n" << std::endl;

    // 生成测试信号
    float sample_rate = 44100.0f;
    float duration = 0.05f;

    // 混合多个频率
    auto samples1 = generate_sine(440.0f, sample_rate, duration);
    auto samples2 = generate_sine(880.0f, sample_rate, duration, 0.5f);
    auto samples3 = generate_sine(1760.0f, sample_rate, duration, 0.25f);

    std::vector<float> mixed(samples1.size());
    for (size_t i = 0; i < samples1.size(); ++i) {
        mixed[i] = samples1[i] + samples2[i] + samples3[i];
    }

    std::cout << "混合信号包含:" << std::endl;
    std::cout << "  440 Hz (A4) - 振幅 1.0" << std::endl;
    std::cout << "  880 Hz (A5) - 振幅 0.5" << std::endl;
    std::cout << "  1760 Hz (A6) - 振幅 0.25" << std::endl;

    std::cout << "\nMP3 编码器会:" << std::endl;
    std::cout << "  1. 分析频谱，识别这三个频率" << std::endl;
    std::cout << "  2. 根据心理声学模型决定量化精度" << std::endl;
    std::cout << "  3. 低振幅高频可能被完全丢弃" << std::endl;
}

int main() {
    std::cout << "=== MP3 Codec Concept Demo (MP3 编码概念演示) ===" << std::endl;

    demo_mp3_encoding_flow();
    demo_psychoacoustic_model();
    demo_mp3_frame();
    demo_mp3_bitrates();
    demo_mp3_comparison();
    demo_spectrum_analysis();

    std::cout << "\n=== MP3 编码总结 ===" << std::endl;
    std::cout << "1. MP3 使用心理声学模型进行有损压缩" << std::endl;
    std::cout << "2. 核心技术：MDCT + 量化 + 熵编码" << std::endl;
    std::cout << "3. 典型比特率 128-320 kbps" << std::endl;
    std::cout << "4. 兼容性最好，但效率不如新格式" << std::endl;
    std::cout << "\n注意：完整 MP3 编码器实现非常复杂，需要使用 libmp3lame 等库" << std::endl;

    return 0;
}
