/**
 * @file mkv_demuxer.cpp
 * @brief MKV 解复用器实现
 */

#include "container/container.h"
#include <cstring>
#include <fstream>
#include <vector>

namespace av_codec {

class MKVDemuxerImpl : public IDemuxer {
public:
    int init(const char* filename) override {
        filename_ = filename;
        file_.open(filename, std::ios::binary);
        if (!file_.is_open()) return -1;

        parseFile();
        initialized_ = true;
        return 0;
    }

    int getStreamCount() const override { return streams_.size(); }

    const StreamInfo* getStreamInfo(int index) const override {
        if (index < 0 || index >= streams_.size()) return nullptr;
        return &streams_[index];
    }

    int readPacket(AVPacketData& pkt) override {
        if (!initialized_ || current_sample_ >= samples_.size()) return -1;

        const auto& sample = samples_[current_sample_];
        pkt.stream_index = sample.stream_index;
        pkt.pts = sample.pts;
        pkt.dts = sample.pts;
        pkt.keyframe = sample.keyframe;

        file_.seekg(sample.offset);
        pkt.data.resize(sample.size);
        file_.read(reinterpret_cast<char*>(pkt.data.data()), sample.size);

        current_sample_++;
        return 0;
    }

    int seek(int64_t timestamp, int stream_index) override {
        for (size_t i = 0; i < samples_.size(); i++) {
            if (samples_[i].pts >= timestamp && samples_[i].keyframe) {
                current_sample_ = i;
                return 0;
            }
        }
        return -1;
    }

    void close() override {
        if (file_.is_open()) file_.close();
        initialized_ = false;
    }

private:
    void parseFile() {
        // 简化的MKV解析
    }

    struct SampleInfo {
        int stream_index = 0;
        int64_t offset = 0;
        int size = 0;
        int64_t pts = 0;
        bool keyframe = false;
    };

    std::string filename_;
    std::ifstream file_;
    bool initialized_ = false;
    std::vector<StreamInfo> streams_;
    std::vector<SampleInfo> samples_;
    size_t current_sample_ = 0;
};

std::unique_ptr<IDemuxer> createMKVDemuxer() {
    return std::make_unique<MKVDemuxerImpl>();
}

} // namespace av_codec
