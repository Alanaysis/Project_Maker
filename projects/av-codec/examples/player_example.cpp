/**
 * @file player_example.cpp
 * @brief 视频播放器示例
 *
 * 演示如何使用视频播放器播放音视频文件
 */

#include <iostream>
#include <vector>
#include <cstdint>
#include <string>

/**
 * @brief 播放器状态
 */
enum class PlayerState {
    IDLE,
    LOADING,
    READY,
    PLAYING,
    PAUSED,
    STOPPED
};

/**
 * @brief 播放器类
 */
class SimplePlayer {
public:
    int load(const std::string& url) {
        std::cout << "加载文件: " << url << std::endl;
        state_ = PlayerState::READY;
        duration_ = 120000;  // 120秒
        return 0;
    }

    int play() {
        if (state_ != PlayerState::READY && state_ != PlayerState::PAUSED) return -1;
        state_ = PlayerState::PLAYING;
        std::cout << "开始播放" << std::endl;
        return 0;
    }

    int pause() {
        if (state_ != PlayerState::PLAYING) return -1;
        state_ = PlayerState::PAUSED;
        std::cout << "暂停播放" << std::endl;
        return 0;
    }

    int stop() {
        state_ = PlayerState::STOPPED;
        position_ = 0;
        std::cout << "停止播放" << std::endl;
        return 0;
    }

    int seek(int64_t position) {
        position_ = position;
        std::cout << "定位到: " << position_ << " ms" << std::endl;
        return 0;
    }

    void setVolume(float volume) {
        volume_ = volume;
        std::cout << "设置音量: " << volume_ << std::endl;
    }

    void setSpeed(float speed) {
        speed_ = speed;
        std::cout << "设置播放速度: " << speed_ << "x" << std::endl;
    }

    PlayerState getState() const { return state_; }
    int64_t getPosition() const { return position_; }
    int64_t getDuration() const { return duration_; }

private:
    PlayerState state_ = PlayerState::IDLE;
    int64_t position_ = 0;
    int64_t duration_ = 0;
    float volume_ = 1.0f;
    float speed_ = 1.0f;
};

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== 视频播放器示例 ===" << std::endl;

    SimplePlayer player;

    // 加载文件
    player.load("test.mp4");
    std::cout << "时长: " << player.getDuration() / 1000 << " 秒" << std::endl;

    // 播放
    player.play();
    std::cout << "状态: 播放中" << std::endl;

    // 设置音量
    player.setVolume(0.8f);

    // 设置播放速度
    player.setSpeed(1.5f);

    // 定位
    player.seek(30000);  // 30秒
    std::cout << "当前位置: " << player.getPosition() / 1000 << " 秒" << std::endl;

    // 暂停
    player.pause();
    std::cout << "状态: 暂停" << std::endl;

    // 继续播放
    player.play();
    std::cout << "状态: 继续播放" << std::endl;

    // 停止
    player.stop();
    std::cout << "状态: 停止" << std::endl;

    std::cout << "\n播放器示例完成!" << std::endl;

    return 0;
}
