/**
 * @file mp4_demuxer.cpp
 * @brief MP4 解复用器实现
 */

#include "container/container.h"
#include <cstring>
#include <fstream>
#include <vector>

namespace av_codec {

class MP4DemuxerImpl : public IDemuxer {
public:
    int init(const char* filename) override {
        filename_ = filename;
        file_.open(filename, std::ios::binary);
        if (!file_.is_open()) return -1;

        // 解析文件
        parseFile();

        initialized_ = true;
        return 0;
    }

    int getStreamCount() const override {
        return streams_.size();
    }

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

        // 读取数据
        file_.seekg(sample.offset);
        pkt.data.resize(sample.size);
        file_.read(reinterpret_cast<char*>(pkt.data.data()), sample.size);

        current_sample_++;
        return 0;
    }

    int seek(int64_t timestamp, int stream_index) override {
        // 简化实现：查找最近的关键帧
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
        // 简化的MP4解析
        // 实际实现需要解析完整的box结构
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

std::unique_ptr<IDemuxer> createMP4Demuxer() {
    return std::make_unique<MP4DemuxerImpl>();
}

} // namespace av_codec
