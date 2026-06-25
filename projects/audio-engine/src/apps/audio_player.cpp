// audio_player.cpp - 音频播放器演示
//
// 本文件演示音频播放器的基本功能：
// 1. WAV 文件播放
// 2. 播放控制
// 3. 进度显示
// 4. 音量控制
//
// 编译: g++ -std=c++17 -I../../include audio_player.cpp -o audio_player -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>
#include <thread>
#include <chrono>

using namespace audio;

// 音频播放器类
class AudioPlayer {
public:
    AudioPlayer() : playing_(false), paused_(false), volume_(1.0f),
                    position_(0), loop_(false) {}

    bool load(const std::string& filename) {
        try {
            buffer_ = read_wav(filename);
            position_ = 0;
            std::cout << "Loaded: " << filename << std::endl;
            print_buffer_info(buffer_, "  ");
            return true;
        } catch (const std::exception& e) {
            std::cerr << "Error loading file: " << e.what() << std::endl;
            return false;
        }
    }

    void play() {
        if (buffer_.samples.empty()) {
            std::cout << "No audio loaded" << std::endl;
            return;
        }
        playing_ = true;
        paused_ = false;
        std::cout << "Playing..." << std::endl;
    }

    void pause() {
        paused_ = !paused_;
        std::cout << (paused_ ? "Paused" : "Resumed") << std::endl;
    }

    void stop() {
        playing_ = false;
        paused_ = false;
        position_ = 0;
        std::cout << "Stopped" << std::endl;
    }

    void set_volume(float volume) {
        volume_ = clamp(volume, 0.0f, 2.0f);
        std::cout << "Volume: " << volume_ << std::endl;
    }

    void set_loop(bool loop) {
        loop_ = loop;
        std::cout << "Loop: " << (loop ? "On" : "Off") << std::endl;
    }

    // 模拟播放处理
    void process_chunk(size_t chunk_size = 1024) {
        if (!playing_ || paused_) return;

        // 处理音频块
        for (size_t i = 0; i < chunk_size && position_ < buffer_.samples.size(); ++i) {
            buffer_.samples[position_] *= volume_;
            position_++;
        }

        // 检查是否播放完毕
        if (position_ >= buffer_.samples.size()) {
            if (loop_) {
                position_ = 0;
            } else {
                stop();
            }
        }
    }

    float get_progress() const {
        if (buffer_.samples.empty()) return 0.0f;
        return static_cast<float>(position_) / buffer_.samples.size();
    }

    double get_position_seconds() const {
        return static_cast<double>(position_) / (buffer_.sample_rate * buffer_.channels);
    }

    double get_duration_seconds() const {
        return buffer_.duration();
    }

    bool is_playing() const { return playing_ && !paused_; }
    bool is_paused() const { return paused_; }

private:
    AudioBuffer buffer_;
    bool playing_;
    bool paused_;
    float volume_;
    size_t position_;
    bool loop_;
};

// 演示播放器功能
void demo_player_functionality() {
    print_separator("播放器功能");

    std::cout << "\n音频播放器的基本功能:\n" << std::endl;

    // 创建测试文件
    float sample_rate = 44100.0f;
    auto samples = generate_sine(440.0f, sample_rate, 5.0f);
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));
    write_wav("player_test.wav", buffer);

    // 创建播放器
    AudioPlayer player;

    // 加载文件
    std::cout << "1. 加载文件:" << std::endl;
    player.load("player_test.wav");

    // 播放
    std::cout << "\n2. 播放:" << std::endl;
    player.play();

    // 模拟播放过程
    for (int i = 0; i < 10; ++i) {
        player.process_chunk(4410); // 0.1 秒
        std::cout << "  Progress: " << (player.get_progress() * 100) << "%" << std::endl;
    }

    // 暂停
    std::cout << "\n3. 暂停:" << std::endl;
    player.pause();

    // 恢复
    std::cout << "\n4. 恢复:" << std::endl;
    player.pause();

    // 停止
    std::cout << "\n5. 停止:" << std::endl;
    player.stop();
}

// 演示音量控制
void demo_volume_control() {
    print_separator("音量控制");

    std::cout << "\n播放器音量控制:\n" << std::endl;

    AudioPlayer player;

    std::vector<float> volumes = {0.0f, 0.25f, 0.5f, 0.75f, 1.0f, 1.5f};

    for (float vol : volumes) {
        player.set_volume(vol);
    }

    std::cout << "\n音量范围: 0.0 (静音) 到 2.0 (增益)" << std::endl;
}

// 演示播放模式
void demo_playback_modes() {
    print_separator("播放模式");

    std::cout << "\n播放模式:\n" << std::endl;

    std::cout << "1. 单次播放" << std::endl;
    std::cout << "   - 播放一次后停止" << std::endl;

    std::cout << "\n2. 循环播放" << std::endl;
    std::cout << "   - 播放完毕后重新开始" << std::endl;

    std::cout << "\n3. 随机播放" << std::endl;
    std::cout << "   - 随机顺序播放" << std::endl;

    std::cout << "\n4. 进度显示" << std::endl;
    std::cout << "   - 显示当前播放位置" << std::endl;
    std::cout << "   - 显示总时长" << std::endl;
}

// 演示播放器应用
void demo_player_applications() {
    print_separator("播放器应用");

    std::cout << "\n音频播放器的应用:\n" << std::endl;

    std::cout << "1. 音乐播放器" << std::endl;
    std::cout << "   - 播放音乐文件" << std::endl;
    std::cout << "   - 播放列表管理" << std::endl;
    std::cout << "   - 音量控制" << std::endl;

    std::cout << "\n2. 播客播放器" << std::endl;
    std::cout << "   - 播放播客节目" << std::endl;
    std::cout << "   - 播放速度调节" << std::endl;
    std::cout << "   - 书签功能" << std::endl;

    std::cout << "\n3. 游戏音频" << std::endl;
    std::cout << "   - 背景音乐播放" << std::endl;
    std::cout << "   - 音效触发" << std::endl;
    std::cout << "   - 3D 音效" << std::endl;

    std::cout << "\n4. 语音播放" << std::endl;
    std::cout << "   - 语音消息播放" << std::endl;
    std::cout << "   - 有声读物" << std::endl;
}

int main() {
    std::cout << "=== Audio Player Demo (音频播放器演示) ===" << std::endl;

    demo_player_functionality();
    demo_volume_control();
    demo_playback_modes();
    demo_player_applications();

    std::cout << "\n=== 音频播放器总结 ===" << std::endl;
    std::cout << "1. 加载和播放音频文件" << std::endl;
    std::cout << "2. 播放控制：播放/暂停/停止" << std::endl;
    std::cout << "3. 音量控制" << std::endl;
    std::cout << "4. 进度显示和播放模式" << std::endl;

    return 0;
}
