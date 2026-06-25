/**
 * @file rtmp_client.cpp
 * @brief RTMP 客户端实现
 *
 * RTMP协议特点：
 * - 基于TCP
 * - 低延迟（1-3秒）
 * - 推流/拉流
 * - 广泛用于直播
 */

#include "protocol/streaming.h"
#include <cstring>
#include <string>
#include <functional>

namespace av_codec {

class RTMPClientImpl : public IStreamPublisher {
public:
    int init(const StreamConfig& config) override {
        config_ = config;
        state_ = StreamState::IDLE;
        return 0;
    }

    int connect() override {
        state_ = StreamState::CONNECTING;

        // 解析URL
        if (!parseURL(config_.url)) {
            state_ = StreamState::ERROR;
            return -1;
        }

        // 建立TCP连接
        if (!tcpConnect()) {
            state_ = StreamState::ERROR;
            return -2;
        }

        // RTMP握手
        if (!rtmpHandshake()) {
            state_ = StreamState::ERROR;
            return -3;
        }

        // 发送连接命令
        if (!sendConnect()) {
            state_ = StreamState::ERROR;
            return -4;
        }

        state_ = StreamState::CONNECTED;
        return 0;
    }

    int sendVideo(const uint8_t* data, int size, int64_t pts, bool keyframe) override {
        if (state_ != StreamState::CONNECTED && state_ != StreamState::STREAMING) return -1;

        // 构建视频消息
        std::vector<uint8_t> message;
        message.push_back(keyframe ? 0x17 : 0x27);  // Frame type + Codec ID
        message.push_back(0x01);  // AVC NALU
        message.push_back(0x00);  // Composition time
        message.push_back(0x00);
        message.push_back(0x00);
        message.insert(message.end(), data, data + size);

        // 发送RTMP消息
        sendRTMPMessage(0x09, message.data(), message.size(), pts);

        stats_.frames_sent++;
        stats_.bytes_sent += size;
        state_ = StreamState::STREAMING;

        return 0;
    }

    int sendAudio(const uint8_t* data, int size, int64_t pts) override {
        if (state_ != StreamState::CONNECTED && state_ != StreamState::STREAMING) return -1;

        // 构建音频消息
        std::vector<uint8_t> message;
        message.push_back(0xAF);  // AAC, 44kHz, 16bit, Stereo
        message.push_back(0x01);  // AAC Raw
        message.insert(message.end(), data, data + size);

        // 发送RTMP消息
        sendRTMPMessage(0x08, message.data(), message.size(), pts);

        stats_.frames_sent++;
        stats_.bytes_sent += size;

        return 0;
    }

    StreamState getState() const override { return state_; }
    StreamStats getStats() const override { return stats_; }

    void setOnStateChange(OnStateChangeCallback callback) override {
        on_state_change_ = callback;
    }

    void setOnError(OnErrorCallback callback) override {
        on_error_ = callback;
    }

    void disconnect() override {
        state_ = StreamState::DISCONNECTED;
        if (on_state_change_) on_state_change_(state_);
    }

    void close() override {
        disconnect();
    }

private:
    bool parseURL(const std::string& url) {
        // 解析 rtmp://host:port/app/stream
        if (url.substr(0, 7) != "rtmp://") return false;

        size_t host_start = 7;
        size_t host_end = url.find(':', host_start);
        if (host_end == std::string::npos) {
            host_end = url.find('/', host_start);
            port_ = 1935;
        } else {
            port_ = std::stoi(url.substr(host_end + 1, url.find('/', host_end) - host_end - 1));
        }

        host_ = url.substr(host_start, host_end - host_start);

        size_t app_start = url.find('/', host_start) + 1;
        size_t app_end = url.find('/', app_start);
        app_ = url.substr(app_start, app_end - app_start);

        stream_ = url.substr(app_end + 1);

        return true;
    }

    bool tcpConnect() {
        // 简化：模拟TCP连接
        return true;
    }

    bool rtmpHandshake() {
        // 简化：RTMP握手
        return true;
    }

    bool sendConnect() {
        // 简化：发送connect命令
        return true;
    }

    void sendRTMPMessage(uint8_t type, const uint8_t* data, int size, int64_t timestamp) {
        // 简化：发送RTMP消息
    }

private:
    StreamConfig config_;
    StreamState state_ = StreamState::IDLE;
    StreamStats stats_;
    std::string host_;
    int port_ = 1935;
    std::string app_;
    std::string stream_;
    OnStateChangeCallback on_state_change_;
    OnErrorCallback on_error_;
};

std::unique_ptr<IStreamPublisher> createRTMPClient() {
    return std::make_unique<RTMPClientImpl>();
}

} // namespace av_codec
