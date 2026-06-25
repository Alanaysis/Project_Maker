// audio_editor.cpp - 音频编辑器演示
//
// 本文件演示音频编辑器的基本功能：
// 1. 音频裁剪
// 2. 音频拼接
// 3. 音量归一化
// 4. 淡入淡出
//
// 编译: g++ -std=c++17 -I../../include audio_editor.cpp -o audio_editor -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 音频编辑器类
class AudioEditor {
public:
    AudioEditor() {}

    bool load(const std::string& filename) {
        try {
            buffer_ = read_wav(filename);
            std::cout << "Loaded: " << filename << std::endl;
            return true;
        } catch (const std::exception& e) {
            std::cerr << "Error: " << e.what() << std::endl;
            return false;
        }
    }

    bool save(const std::string& filename) {
        if (write_wav(filename, buffer_)) {
            std::cout << "Saved: " << filename << std::endl;
            return true;
        }
        return false;
    }

    // 裁剪
    AudioBuffer trim(double start_sec, double end_sec) {
        size_t start_sample = static_cast<size_t>(start_sec * buffer_.sample_rate) * buffer_.channels;
        size_t end_sample = static_cast<size_t>(end_sec * buffer_.sample_rate) * buffer_.channels;

        start_sample = std::min(start_sample, buffer_.samples.size());
        end_sample = std::min(end_sample, buffer_.samples.size());

        AudioBuffer trimmed;
        trimmed.sample_rate = buffer_.sample_rate;
        trimmed.channels = buffer_.channels;
        trimmed.bit_depth = buffer_.bit_depth;
        trimmed.samples.assign(buffer_.samples.begin() + start_sample,
                               buffer_.samples.begin() + end_sample);

        return trimmed;
    }

    // 拼接
    static AudioBuffer concatenate(const AudioBuffer& a, const AudioBuffer& b) {
        AudioBuffer result;
        result.sample_rate = a.sample_rate;
        result.channels = a.channels;
        result.bit_depth = a.bit_depth;

        result.samples = a.samples;
        result.samples.insert(result.samples.end(), b.samples.begin(), b.samples.end());

        return result;
    }

    // 音量归一化
    void normalize(float target_db = 0.0f) {
        float peak = buffer_.peak();
        if (peak == 0.0f) return;

        float target_linear = db_to_linear(target_db);
        float gain = target_linear / peak;

        for (auto& sample : buffer_.samples) {
            sample *= gain;
        }
    }

    // 淡入
    void fade_in(double duration_sec) {
        size_t num_samples = static_cast<size_t>(duration_sec * buffer_.sample_rate) * buffer_.channels;
        num_samples = std::min(num_samples, buffer_.samples.size());

        for (size_t i = 0; i < num_samples; ++i) {
            float gain = static_cast<float>(i) / num_samples;
            buffer_.samples[i] *= gain;
        }
    }

    // 淡出
    void fade_out(double duration_sec) {
        size_t num_samples = static_cast<size_t>(duration_sec * buffer_.sample_rate) * buffer_.channels;
        num_samples = std::min(num_samples, buffer_.samples.size());

        size_t start = buffer_.samples.size() - num_samples;
        for (size_t i = 0; i < num_samples; ++i) {
            float gain = 1.0f - static_cast<float>(i) / num_samples;
            buffer_.samples[start + i] *= gain;
        }
    }

    AudioBuffer& get_buffer() { return buffer_; }

private:
    AudioBuffer buffer_;
};

// 演示裁剪功能
void demo_trim() {
    print_separator("音频裁剪");

    std::cout << "\n裁剪：提取音频的指定部分\n" << std::endl;

    float sample_rate = 44100.0f;

    // 创建测试音频
    auto samples = generate_sine(440.0f, sample_rate, 5.0f);
    AudioBuffer original = make_buffer(samples, static_cast<uint32_t>(sample_rate));
    write_wav("editor_original.wav", original);

    AudioEditor editor;
    editor.load("editor_original.wav");

    // 裁剪 1-3 秒
    AudioBuffer trimmed = editor.trim(1.0, 3.0);
    write_wav("editor_trimmed.wav", trimmed);

    std::cout << "原始时长: " << original.duration() << " 秒" << std::endl;
    std::cout << "裁剪后时长: " << trimmed.duration() << " 秒" << std::endl;
}

// 演示拼接功能
void demo_concatenate() {
    print_separator("音频拼接");

    std::cout << "\n拼接：将多个音频连接在一起\n" << std::endl;

    float sample_rate = 44100.0f;

    auto samples1 = generate_sine(261.63f, sample_rate, 1.0f);  // C4
    auto samples2 = generate_sine(329.63f, sample_rate, 1.0f);  // E4
    auto samples3 = generate_sine(392.00f, sample_rate, 1.0f);  // G4

    AudioBuffer buf1 = make_buffer(samples1, static_cast<uint32_t>(sample_rate));
    AudioBuffer buf2 = make_buffer(samples2, static_cast<uint32_t>(sample_rate));
    AudioBuffer buf3 = make_buffer(samples3, static_cast<uint32_t>(sample_rate));

    AudioBuffer concatenated = AudioEditor::concatenate(AudioEditor::concatenate(buf1, buf2), buf3);
    write_wav("editor_concatenated.wav", concatenated);

    std::cout << "拼接 C4 + E4 + G4" << std::endl;
    std::cout << "总时长: " << concatenated.duration() << " 秒" << std::endl;
}

// 演示归一化
void demo_normalize() {
    print_separator("音量归一化");

    std::cout << "\n归一化：调整音量到目标电平\n" << std::endl;

    float sample_rate = 44100.0f;

    // 创建低音量音频
    auto samples = generate_sine(440.0f, sample_rate, 2.0f, 0.3f);
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    std::cout << "归一化前:" << std::endl;
    std::cout << "  峰值: " << buffer.peak() << " (" << linear_to_db(buffer.peak()) << " dB)" << std::endl;

    write_wav("editor_before_normalize.wav", buffer);

    // 归一化到 0 dB
    AudioEditor editor;
    editor.get_buffer() = buffer;
    editor.normalize(0.0f);

    std::cout << "\n归一化后 (0 dB):" << std::endl;
    std::cout << "  峰值: " << editor.get_buffer().peak() << " dB" << std::endl;

    editor.save("editor_after_normalize.wav");
}

// 演示淡入淡出
void demo_fade() {
    print_separator("淡入淡出");

    std::cout << "\n淡入淡出：平滑的音量过渡\n" << std::endl;

    float sample_rate = 44100.0f;

    auto samples = generate_sine(440.0f, sample_rate, 3.0f);
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    AudioEditor editor;
    editor.get_buffer() = buffer;

    editor.fade_in(0.5);
    editor.fade_out(1.0);

    editor.save("editor_fade.wav");

    std::cout << "淡入: 0.5 秒" << std::endl;
    std::cout << "淡出: 1.0 秒" << std::endl;
}

// 演示编辑器应用
void demo_editor_applications() {
    print_separator("编辑器应用");

    std::cout << "\n音频编辑器的应用:\n" << std::endl;

    std::cout << "1. 音乐制作" << std::endl;
    std::cout << "   - 录音剪辑" << std::endl;
    std::cout << "   - 段落拼接" << std::endl;
    std::cout << "   - 母带处理" << std::endl;

    std::cout << "\n2. 播客编辑" << std::endl;
    std::cout << "   - 去除错误部分" << std::endl;
    std::cout << "   - 添加背景音乐" << std::endl;
    std::cout << "   - 音量标准化" << std::endl;

    std::cout << "\n3. 音效设计" << std::endl;
    std::cout << "   - 音效裁剪" << std::endl;
    std::cout << "   - 音效拼接" << std::endl;
    std::cout << "   - 淡入淡出" << std::endl;

    std::cout << "\n4. 语音处理" << std::endl;
    std::cout << "   - 语音消息编辑" << std::endl;
    std::cout << "   - 录音整理" << std::endl;
}

int main() {
    std::cout << "=== Audio Editor Demo (音频编辑器演示) ===" << std::endl;

    demo_trim();
    demo_concatenate();
    demo_normalize();
    demo_fade();
    demo_editor_applications();

    std::cout << "\n=== 音频编辑器总结 ===" << std::endl;
    std::cout << "1. 裁剪：提取音频片段" << std::endl;
    std::cout << "2. 拼接：连接多个音频" << std::endl;
    std::cout << "3. 归一化：调整到目标电平" << std::endl;
    std::cout << "4. 淡入淡出：平滑过渡" << std::endl;

    return 0;
}
