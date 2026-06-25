/**
 * @file dash_server.cpp
 * @brief DASH 服务器实现
 *
 * DASH协议特点：
 * - 基于HTTP
 * - 自适应码率
 * - MPD描述文件
 * - 国际标准
 */

#include "protocol/streaming.h"
#include <cstring>
#include <string>
#include <fstream>
#include <vector>

namespace av_codec {

class DASHServerImpl : public IStreamPublisher {
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
            saveSegment();
            current_segment_.clear();
        }

        stats_.frames_sent++;
        stats_.bytes_sent += size;
        state_ = StreamState::STREAMING;

        return 0;
    }

    int sendAudio(const uint8_t* data, int size, int64_t pts) override {
        if (state_ != StreamState::CONNECTED && state_ != StreamState::STREAMING) return -1;

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
        // 保存MP4切片
        std::string filename = "segment_" + std::to_string(segment_count_) + ".m4s";
        std::ofstream file(filename, std::ios::binary);
        if (file.is_open()) {
            file.write(reinterpret_cast<const char*>(current_segment_.data()),
                      current_segment_.size());
            file.close();

            // 更新MPD描述文件
            updateMPD();

            segment_count_++;
        }
    }

    void updateMPD() {
        // 写入MPD描述文件
        std::ofstream file("manifest.mpd");
        if (file.is_open()) {
            file << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
            file << "<MPD xmlns=\"urn:mpeg:dash:schema:mpd:2011\"\n";
            file << "     type=\"dynamic\"\n";
            file << "     minimumUpdatePeriod=\"PT10S\"\n";
            file << "     minBufferTime=\"PT2S\">\n";
            file << "  <Period>\n";
            file << "    <AdaptationSet mimeType=\"video/mp4\">\n";
            file << "      <Representation bandwidth=\"2000000\" width=\"1920\" height=\"1080\">\n";
            file << "        <SegmentTemplate timescale=\"30\" media=\"segment_$Number$.m4s\"\n";
            file << "                          startNumber=\"1\"/>\n";
            file << "        <SegmentTimeline>\n";

            for (int i = 0; i < segment_count_; i++) {
                file << "          <S t=\"" << i * 300 << "\" d=\"300\"/>\n";
            }

            file << "        </SegmentTimeline>\n";
            file << "      </Representation>\n";
            file << "    </AdaptationSet>\n";
            file << "  </Period>\n";
            file << "</MPD>\n";

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

std::unique_ptr<IStreamPublisher> createDASHServer() {
    return std::make_unique<DASHServerImpl>();
}

} // namespace av_codec
