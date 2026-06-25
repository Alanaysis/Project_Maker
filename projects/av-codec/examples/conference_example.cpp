/**
 * @file conference_example.cpp
 * @brief 视频会议示例
 *
 * 演示如何使用视频会议系统进行多人音视频通话
 */

#include <iostream>
#include <vector>
#include <cstdint>
#include <string>

/**
 * @brief 会议参与者
 */
struct Participant {
    std::string user_id;
    std::string user_name;
    bool video_enabled = true;
    bool audio_enabled = true;
};

/**
 * @brief 会议类
 */
class SimpleConference {
public:
    int join(const std::string& server, const std::string& room_id,
            const std::string& user_id) {
        std::cout << "连接服务器: " << server << std::endl;
        std::cout << "加入房间: " << room_id << std::endl;
        std::cout << "用户ID: " << user_id << std::endl;

        // 添加自己
        Participant self;
        self.user_id = user_id;
        self.user_name = "用户" + user_id;
        participants_.push_back(self);

        return 0;
    }

    int leave() {
        std::cout << "离开会议" << std::endl;
        participants_.clear();
        return 0;
    }

    void muteAudio(bool mute) {
        audio_muted_ = mute;
        std::cout << (mute ? "静音" : "取消静音") << std::endl;
    }

    void enableVideo(bool enable) {
        video_enabled_ = enable;
        std::cout << (enable ? "开启摄像头" : "关闭摄像头") << std::endl;
    }

    int startScreenShare() {
        screen_sharing_ = true;
        std::cout << "开始屏幕共享" << std::endl;
        return 0;
    }

    int stopScreenShare() {
        screen_sharing_ = false;
        std::cout << "停止屏幕共享" << std::endl;
        return 0;
    }

    void sendVideoFrame(int frame_number) {
        if (!video_enabled_) return;
        std::cout << "发送视频帧: " << frame_number << std::endl;
    }

    void sendAudioFrame(int frame_number) {
        if (audio_muted_) return;
        std::cout << "发送音频帧: " << frame_number << std::endl;
    }

    const std::vector<Participant>& getParticipants() const {
        return participants_;
    }

private:
    std::vector<Participant> participants_;
    bool audio_muted_ = false;
    bool video_enabled_ = true;
    bool screen_sharing_ = false;
};

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== 视频会议示例 ===" << std::endl;

    SimpleConference conference;

    // 加入会议
    conference.join("meeting.example.com", "room_123", "user_456");

    // 模拟会议过程
    std::cout << "\n--- 会议进行中 ---" << std::endl;

    // 发送视频和音频
    for (int i = 0; i < 5; i++) {
        conference.sendVideoFrame(i);
        conference.sendAudioFrame(i);
    }

    // 静音
    conference.muteAudio(true);

    // 关闭摄像头
    conference.enableVideo(false);

    // 屏幕共享
    conference.startScreenShare();

    // 继续发送
    for (int i = 5; i < 10; i++) {
        conference.sendVideoFrame(i);
        conference.sendAudioFrame(i);
    }

    // 停止屏幕共享
    conference.stopScreenShare();

    // 取消静音
    conference.muteAudio(false);

    // 开启摄像头
    conference.enableVideo(true);

    // 显示参与者
    std::cout << "\n--- 参与者列表 ---" << std::endl;
    for (const auto& p : conference.getParticipants()) {
        std::cout << "用户: " << p.user_name
                  << " (ID: " << p.user_id << ")" << std::endl;
    }

    // 离开会议
    conference.leave();

    std::cout << "\n视频会议示例完成!" << std::endl;

    return 0;
}
