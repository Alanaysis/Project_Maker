/**
 * @file hls_server.cpp
 * @brief HLS 服务器实现
 *
 * HLS协议特点：
 * - 基于HTTP
 * - 切片传输（.ts文件）
 * - 自适应码率
 * - 广泛兼容
 */

#include "protocol/streaming.h"
#include <cstring>
#include <string>
#include <fstream>
#include <vector>

namespace av_codec {

class HLSServerImpl : public IStreamPublisher {
public:
    int init(const StreamConfig& config) override {
        config_ = config;
        state_ = StreamState::IDLE;
        return 0;
    }

    int connect() override {
        state_ = StreamState::CONNECTED;
        return 0;
    }

    int sendVideo(const uint8_t* data, int size, int64_t pts, bool keyframe) override {
        if (state_ != StreamState::CONNECTED && state_ != StreamState::STREAMING) return -1;

        // 缓存视频数据
        current_segment_.insert(current_segment_.end(), data, data + size);

        // 检查是否需要切片
        if (keyframe && current_segment_.size() > 0) {
            // 保存当前切片
            saveSegment();

            // 开始新切片
            current_segment_.clear();
        }

        stats_.frames_sent++;
        stats_.bytes_sent += size;
        state_ = StreamState::STREAMING;

        return 0;
    }

    int sendAudio(const uint8_t* data, int size, int64_t pts) override {
        if (state_ != StreamState::CONNECTED && state_ != StreamState::STREAMING) return -1;

        // 缓存音频数据
        current_segment_.insert(current_segment_.end(), data, data + size);
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
    }

    void close() override {
        disconnect();
    }

private:
    void saveSegment() {
        // 保存TS切片
        std::string filename = "segment_" + std::to_string(segment_count_) + ".ts";
        std::ofstream file(filename, std::ios::binary);
        if (file.is_open()) {
            file.write(reinterpret_cast<const char*>(current_segment_.data()),
                      current_segment_.size());
            file.close();

            // 更新M3U8播放列表
            updatePlaylist(filename);

            segment_count_++;
        }
    }

    void updatePlaylist(const std::string& segment_name) {
        // 写入M3U8播放列表
        std::ofstream file("playlist.m3u8");
        if (file.is_open()) {
            file << "#EXTM3U\n";
            file << "#EXT-X-VERSION:3\n";
            file << "#EXT-X-TARGETDURATION:10\n";
            file << "#EXT-X-MEDIA-SEQUENCE:" << (segment_count_ - 5) << "\n";

            // 写入最近的切片
            int start = std::max(0, segment_count_ - 5);
            for (int i = start; i <= segment_count_; i++) {
                file << "#EXTINF:10.0,\n";
                file << "segment_" << i << ".ts\n";
            }

            file.close();
        }
    }

private:
    StreamConfig config_;
    StreamState state_ = StreamState::IDLE;
    StreamStats stats_;
    std::vector<uint8_t> current_segment_;
    int segment_count_ = 0;
    OnStateChangeCallback on_state_change_;
    OnErrorCallback on_error_;
};

std::unique_ptr<IStreamPublisher> createHLSServer() {
    return std::make_unique<HLSServerImpl>();
}

} // namespace av_codec
