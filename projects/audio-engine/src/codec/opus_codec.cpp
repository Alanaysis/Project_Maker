// opus_codec.cpp - Opus 编码概念演示
//
// 本文件介绍 Opus 编码的基本原理（概念演示，非完整实现）：
// 1. Opus 编码架构
// 2. SILK 编码器（语音）
// 3. CELT 编码器（音乐）
// 4. 混合模式
//
// 编译: g++ -std=c++17 -I../../include opus_codec.cpp -o opus_codec -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 演示 Opus 架构
void demo_opus_architecture() {
    print_separator("Opus 编码架构");

    std::cout << "\nOpus 是一个混合音频编解码器:\n" << std::endl;

    std::cout << "┌─────────────────────────────────────────┐" << std::endl;
    std::cout << "│              Opus 编码器                 │" << std::endl;
    std::cout << "├─────────────────────────────────────────┤" << std::endl;
    std::cout << "│                                         │" << std::endl;
    std::cout << "│  ┌─────────────┐   ┌─────────────┐     │" << std::endl;
    std::cout << "│  │   SILK      │   │    CELT     │     │" << std::endl;
    std::cout << "│  │  (语音)     │   │   (音乐)    │     │" << std::endl;
    std::cout << "│  └─────────────┘   └─────────────┘     │" << std::endl;
    std::cout << "│         │                 │              │" << std::endl;
    std::cout << "│         └────────┬────────┘              │" << std::endl;
    std::cout << "│                  │                       │" << std::endl;
    std::cout << "│           ┌──────┴──────┐                │" << std::endl;
    std::cout << "│           │   混合模式   │                │" << std::endl;
    std::cout << "│           └─────────────┘                │" << std::endl;
    std::cout << "│                  │                       │" << std::endl;
    std::cout << "│                  ▼                       │" << std::endl;
    std::cout << "│           Opus 比特流                    │" << std::endl;
    std::cout << "└─────────────────────────────────────────┘" << std::endl;

    std::cout << "\nOpus 根据输入信号自动选择编码模式:" << std::endl;
    std::cout << "  - 纯语音: 使用 SILK" << std::endl;
    std::cout << "  - 纯音乐: 使用 CELT" << std::endl;
    std::cout << "  - 混合: 使用混合模式" << std::endl;
}

// 演示 SILK 编码器
void demo_silk() {
    print_separator("SILK 编码器");

    std::cout << "\nSILK 是 Opus 的语音编码组件:\n" << std::endl;

    std::cout << "SILK 特性:" << std::endl;
    std::cout << "  - 基于线性预测 (LP)" << std::endl;
    std::cout << "  - 采样率: 8-24 kHz" << std::endl;
    std::cout << "  - 帧长: 10-60 ms" << std::endl;
    std::cout << "  - 比特率: 6-40 kbps" << std::endl;

    std::cout << "\nSILK 编码流程:" << std::endl;
    std::cout << "  1. 预处理 (高通滤波、增益控制)" << std::endl;
    std::cout << "  2. 线性预测分析" << std::endl;
    std::cout << "  3. 长期预测 (LTP)" << std::endl;
    std::cout << "  4. 噪声整形" << std::endl;
    std::cout << "  5. 量化与编码" << std::endl;

    std::cout << "\nSILK 优势:" << std::endl;
    std::cout << "  - 低比特率下语音质量好" << std::endl;
    std::cout << "  - 支持语音活动检测 (VAD)" << std::endl;
    std::cout << "  - 支持不连续传输 (DTX)" << std::endl;
}

// 演示 CELT 编码器
void demo_celt() {
    print_separator("CELT 编码器");

    std::cout << "\nCELT 是 Opus 的音乐编码组件:\n" << std::endl;

    std::cout << "CELT 特性:" << std::endl;
    std::cout << "  - 基于 MDCT 变换" << std::endl;
    std::cout << "  - 采样率: 32-48 kHz" << std::endl;
    std::cout << "  - 帧长: 2.5-20 ms" << std::endl;
    std::cout << "  - 比特率: 32-640 kbps" << std::endl;

    std::cout << "\nCELT 编码流程:" << std::endl;
    std::cout << "  1. 预加重滤波" << std::endl;
    std::cout << "  2. MDCT 变换" << std::endl;
    std::cout << "  3. 能量量化" << std::endl;
    std::cout << "  4. 稀疏编码" << std::endl;
    std::cout << "  5. 残差编码" << std::endl;

    std::cout << "\nCELT 优势:" << std::endl;
    std::cout << "  - 极低延迟" << std::endl;
    std::cout << "  - 音乐质量好" << std::endl;
    std::cout << "  - 支持多声道" << std::endl;
}

// 演示 Opus 关键特性
void demo_opus_features() {
    print_separator("Opus 关键特性");

    std::cout << "\nOpus 的关键特性:\n" << std::endl;

    std::cout << "1. 自适应比特率" << std::endl;
    std::cout << "   - 范围: 6 kbps - 510 kbps" << std::endl;
    std::cout << "   - 可实时调整" << std::endl;
    std::cout << "   - 无需重新初始化" << std::endl;

    std::cout << "\n2. 自适应帧长" << std::endl;
    std::cout << "   - 支持: 2.5, 5, 10, 20, 40, 60 ms" << std::endl;
    std::cout << "   - 可逐帧改变" << std::endl;
    std::cout << "   - 短帧 = 低延迟" << std::endl;

    std::cout << "\n3. 多声道支持" << std::endl;
    std::cout << "   - 最多 255 声道" << std::endl;
    std::cout << "   - 支持立体声" << std::endl;
    std::cout << "   - 支持环绕声" << std::endl;

    std::cout << "\n4. 采样率支持" << std::endl;
    std::cout << "   - 8, 12, 16, 24, 48 kHz" << std::endl;
    std::cout << "   - 内部重采样" << std::endl;

    std::cout << "\n5. 前向纠错 (FEC)" << std::endl;
    std::cout << "   - 丢包补偿" << std::endl;
    std::cout << "   - 适用于网络传输" << std::endl;
}

// 演示 Opus vs 其他编解码器
void demo_opus_comparison() {
    print_separator("Opus vs 其他编解码器");

    std::cout << "\nOpus 与其他编解码器对比:\n" << std::endl;

    std::cout << "特性       | Opus    | MP3     | AAC     | Vorbis  | Speex" << std::endl;
    std::cout << "-----------|---------|---------|---------|---------|-------" << std::endl;
    std::cout << "语音质量   | 极好    | 差      | 好      | 好      | 极好" << std::endl;
    std::cout << "音乐质量   | 极好    | 好      | 极好    | 好      | 差" << std::endl;
    std::cout << "延迟       | 极低    | 高      | 中      | 中      | 低" << std::endl;
    std::cout << "比特率范围 | 6-510k  | 32-320k | 8-529k  | 32-500k | 2-44k" << std::endl;
    std::cout << "多声道     | 255     | 2       | 48      | 255     | 1" << std::endl;
    std::cout << "专利       | 无      | 已过期  | 部分    | 无      | 无" << std::endl;

    std::cout << "\nOpus 的独特优势:" << std::endl;
    std::cout << "  1. 语音和音乐都优秀" << std::endl;
    std::cout << "  2. 极低延迟（适合实时通信）" << std::endl;
    std::cout << "  3. 自适应比特率" << std::endl;
    std::cout << "  4. 完全免费开放" << std::endl;
}

// 演示 Opus 应用场景
void demo_opus_applications() {
    print_separator("Opus 应用场景");

    std::cout << "\nOpus 的主要应用场景:\n" << std::endl;

    std::cout << "1. WebRTC (网页实时通信)" << std::endl;
    std::cout << "   - Google Hangouts, Meet" << std::endl;
    std::cout << "   - Mozilla Firefox" << std::endl;
    std::cout << "   - Microsoft Edge" << std::endl;

    std::cout << "\n2. VoIP 应用" << std::endl;
    std::cout << "   - Discord" << std::endl;
    std::cout << "   - WhatsApp" << std::endl;
    std::cout << "   - Zoom" << std::endl;

    std::cout << "\n3. 流媒体" << std::endl;
    std::cout << "   - YouTube (部分)" << std::endl;
    std::cout << "   - Twitch" << std::endl;
    std::cout << "   - Spotify (内部)" << std::endl;

    std::cout << "\n4. 游戏" << std::endl;
    std::cout << "   - 游戏内语音聊天" << std::endl;
    std::cout << "   - 实时语音通信" << std::endl;

    std::cout << "\n5. 广播" << std::endl;
    std::cout << "   - 数字广播" << std::endl;
    std::cout << "   - 播客" << std::endl;
}

// 演示 Opus 帧结构
void demo_opus_frame() {
    print_separator("Opus 帧结构");

    std::cout << "\nOpus 帧结构:\n" << std::endl;

    std::cout << "┌─────────────────────────────────┐" << std::endl;
    std::cout << "│ TOC Byte (1 byte)               │" << std::endl;
    std::cout << "│   - 配置 (5 bits)               │" << std::endl;
    std::cout << "│   - 立体声标志 (1 bit)          │" << std::endl;
    std::cout << "│   - 帧数编码 (2 bits)           │" << std::endl;
    std::cout << "├─────────────────────────────────┤" << std::endl;
    std::cout << "│ Frame Size (可选, 1-2 bytes)    │" << std::endl;
    std::cout << "├─────────────────────────────────┤" << std::endl;
    std::cout << "│ Frame Data (variable)           │" << std::endl;
    std::cout << "│   - SILK 数据 或                │" << std::endl;
    std::cout << "│   - CELT 数据 或                │" << std::endl;
    std::cout << "│   - 混合数据                    │" << std::endl;
    std::cout << "└─────────────────────────────────┘" << std::endl;

    std::cout << "\n帧长选项:" << std::endl;
    std::cout << "  2.5 ms - 超低延迟" << std::endl;
    std::cout << "  5 ms   - 低延迟" << std::endl;
    std::cout << "  10 ms  - 标准" << std::endl;
    std::cout << "  20 ms  - 默认" << std::endl;
    std::cout << "  40 ms  - 高效率" << std::endl;
    std::cout << "  60 ms  - 最高效率" << std::endl;
}

// 演示 Opus 比特率配置
void demo_opus_bitrates() {
    print_separator("Opus 比特率配置");

    std::cout << "\nOpus 推荐比特率:\n" << std::endl;

    struct BitrateConfig {
        const char* application;
        int mono_bitrate;
        int stereo_bitrate;
        const char* note;
    };

    std::vector<BitrateConfig> configs = {
        {"语音 (窄带)", 8000, 16000, "电话质量"},
        {"语音 (宽带)", 16000, 32000, "清晰语音"},
        {"音乐 (低)", 32000, 64000, "背景音乐"},
        {"音乐 (中)", 64000, 128000, "标准音乐"},
        {"音乐 (高)", 128000, 256000, "高质量音乐"},
        {"广播", 96000, 192000, "广播质量"}
    };

    std::cout << "应用场景       | 单声道 (bps) | 立体声 (bps) | 备注" << std::endl;
    std::cout << "---------------|-------------|-------------|------" << std::endl;

    for (const auto& config : configs) {
        printf("%-14s | %11d | %11d | %s\n",
               config.application, config.mono_bitrate,
               config.stereo_bitrate, config.note);
    }

    std::cout << "\n注意：Opus 可以使用任意比特率，以上仅为推荐值" << std::endl;
}

int main() {
    std::cout << "=== Opus Codec Concept Demo (Opus 编码概念演示) ===" << std::endl;

    demo_opus_architecture();
    demo_silk();
    demo_celt();
    demo_opus_features();
    demo_opus_comparison();
    demo_opus_applications();
    demo_opus_frame();
    demo_opus_bitrates();

    std::cout << "\n=== Opus 编码总结 ===" << std::endl;
    std::cout << "1. Opus 是最先进的音频编解码器" << std::endl;
    std::cout << "2. 融合 SILK (语音) 和 CELT (音乐)" << std::endl;
    std::cout << "3. 自适应比特率和帧长" << std::endl;
    std::cout << "4. 极低延迟，适合实时通信" << std::endl;
    std::cout << "5. 完全免费开放，无专利限制" << std::endl;
    std::cout << "\n注意：完整 Opus 实现需要使用 libopus 库" << std::endl;

    return 0;
}
