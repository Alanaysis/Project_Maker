/**
 * @file transcoder_example.cpp
 * @brief 视频转码示例
 *
 * 演示如何使用视频转码器进行格式转换
 */

#include <iostream>
#include <vector>
#include <cstdint>
#include <string>

/**
 * @brief 转码参数
 */
struct TranscodeParams {
    std::string input_file;
    std::string output_file;
    int width = 1920;
    int height = 1080;
    int fps = 30;
    int video_bitrate = 2000000;
    int audio_bitrate = 128000;
    std::string video_codec = "h264";
    std::string audio_codec = "aac";
    std::string container = "mp4";
};

/**
 * @brief 模拟转码过程
 */
void transcode(const TranscodeParams& params) {
    std::cout << "输入文件: " << params.input_file << std::endl;
    std::cout << "输出文件: " << params.output_file << std::endl;
    std::cout << "视频编码: " << params.video_codec << std::endl;
    std::cout << "音频编码: " << params.audio_codec << std::endl;
    std::cout << "分辨率: " << params.width << "x" << params.height << std::endl;
    std::cout << "帧率: " << params.fps << " fps" << std::endl;
    std::cout << "视频码率: " << params.video_bitrate / 1000 << " kbps" << std::endl;
    std::cout << "音频码率: " << params.audio_bitrate / 1000 << " kbps" << std::endl;

    // 模拟转码进度
    int total_frames = 100;
    for (int i = 0; i < total_frames; i++) {
        double progress = static_cast<double>(i + 1) / total_frames * 100;
        std::cout << "\r转码进度: " << progress << "%" << std::flush;
    }
    std::cout << std::endl;
}

/**
 * @brief H.264转H.265示例
 */
void h264ToH265Example() {
    std::cout << "\n--- H.264转H.265示例 ---" << std::endl;

    TranscodeParams params;
    params.input_file = "input_h264.mp4";
    params.output_file = "output_h265.mp4";
    params.video_codec = "h265";
    params.audio_codec = "aac";

    transcode(params);
}

/**
 * @brief 分辨率转换示例
 */
void resolutionConvertExample() {
    std::cout << "\n--- 分辨率转换示例 ---" << std::endl;

    TranscodeParams params;
    params.input_file = "input_1080p.mp4";
    params.output_file = "output_720p.mp4";
    params.width = 1280;
    params.height = 720;
    params.video_bitrate = 1500000;

    transcode(params);
}

/**
 * @brief 码率调整示例
 */
void bitrateAdjustExample() {
    std::cout << "\n--- 码率调整示例 ---" << std::endl;

    TranscodeParams params;
    params.input_file = "input.mp4";
    params.output_file = "output_low_bitrate.mp4";
    params.video_bitrate = 500000;
    params.audio_bitrate = 64000;

    transcode(params);
}

/**
 * @brief 格式转换示例
 */
void formatConvertExample() {
    std::cout << "\n--- 格式转换示例 ---" << std::endl;

    // MP4转FLV
    std::cout << "MP4 -> FLV 转换" << std::endl;
    TranscodeParams params1;
    params1.input_file = "input.mp4";
    params1.output_file = "output.flv";
    params1.container = "flv";
    transcode(params1);

    // MP4转MKV
    std::cout << "\nMP4 -> MKV 转换" << std::endl;
    TranscodeParams params2;
    params2.input_file = "input.mp4";
    params2.output_file = "output.mkv";
    params2.container = "mkv";
    transcode(params2);
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== 视频转码示例 ===" << std::endl;

    h264ToH265Example();
    resolutionConvertExample();
    bitrateAdjustExample();
    formatConvertExample();

    std::cout << "\n转码示例全部完成!" << std::endl;

    return 0;
}
