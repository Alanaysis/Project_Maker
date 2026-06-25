/**
 * @file flv_demuxer.cpp
 * @brief FLV 解复用器实现
 */

#include "container/container.h"
#include <cstring>
#include <fstream>
#include <vector>

namespace av_codec {

class FLVDemuxerImpl : public IDemuxer {
public:
    int init(const char* filename) override {
        filename_ = filename;
        file_.open(filename, std::ios::binary);
        if (!file_.is_open()) return -1;

        parseHeader();
        initialized_ = true;
        return 0;
    }

    int getStreamCount() const override { return 2; }  // 视频 + 音频

    const StreamInfo* getStreamInfo(int index) const override {
        if (index < 0 || index >= 2) return nullptr;
        return (index == 0) ? &video_stream_ : &audio_stream_;
    }

    int readPacket(AVPacketData& pkt) override {
        if (!initialized_) return -1;

        // 读取Tag
        if (!readTag(pkt)) return -1;

        return 0;
    }

    int seek(int64_t timestamp, int stream_index) override {
        // 简化实现
        return 0;
    }

    void close() override {
        if (file_.is_open()) file_.close();
        initialized_ = false;
    }

private:
    void parseHeader() {
        // 读取FLV Header
        char signature[4];
        file_.read(signature, 3);
        signature[3] = '\0';

        uint8_t version = readUInt8();
        uint8_t flags = readUInt8();
        uint32_t offset = readUInt32();

        has_video_ = (flags & 0x01) != 0;
        has_audio_ = (flags & 0x04) != 0;

        // PreviousTagSize0
        readUInt32();

        // 初始化流信息
        if (has_video_) {
            video_stream_.type = StreamType::VIDEO;
            video_stream_.video.codec_id = 7;  // AVC
        }
        if (has_audio_) {
            audio_stream_.type = StreamType::AUDIO;
            audio_stream_.audio.codec_id = 10;  // AAC
            audio_stream_.audio.sample_rate = 44100;
            audio_stream_.audio.channels = 2;
        }
    }

    bool readTag(AVPacketData& pkt) {
        // 读取Tag Header
        uint8_t tag_type = readUInt8();
        if (file_.eof()) return false;

        uint32_t data_size = readUInt24();
        uint32_t timestamp = readUInt24();
        uint8_t timestamp_ext = readUInt8();
        uint32_t stream_id = readUInt24();

        int64_t pts = timestamp | (static_cast<int64_t>(timestamp_ext) << 24);
        pkt.pts = pts;
        pkt.dts = pts;

        // 读取Tag Data
        if (tag_type == 9) {
            // Video tag
            pkt.stream_index = 0;
            pkt.keyframe = (readUInt8() & 0xF0) == 0x10;
            readUInt8();  // AVC packet type
            readUInt24();  // Composition time
            pkt.data.resize(data_size - 5);
        } else if (tag_type == 8) {
            // Audio tag
            pkt.stream_index = 1;
            readUInt8();  // Sound info
            readUInt8();  // AAC packet type
            pkt.data.resize(data_size - 2);
        } else {
            // 跳过
            file_.seekg(data_size, std::ios::cur);
            readUInt32();  // PreviousTagSize
            return readTag(pkt);
        }

        file_.read(reinterpret_cast<char*>(pkt.data.data()), pkt.data.size());

        // PreviousTagSize
        readUInt32();

        return true;
    }

    uint8_t readUInt8() {
        uint8_t value;
        file_.read(reinterpret_cast<char*>(&value), 1);
        return value;
    }

    uint32_t readUInt24() {
        uint8_t bytes[3];
        file_.read(reinterpret_cast<char*>(bytes), 3);
        return (bytes[0] << 16) | (bytes[1] << 8) | bytes[2];
    }

    uint32_t readUInt32() {
        uint8_t bytes[4];
        file_.read(reinterpret_cast<char*>(bytes), 4);
        return (bytes[0] << 24) | (bytes[1] << 16) | (bytes[2] << 8) | bytes[3];
    }

private:
    std::string filename_;
    std::ifstream file_;
    bool initialized_ = false;
    bool has_video_ = false;
    bool has_audio_ = false;
    StreamInfo video_stream_;
    StreamInfo audio_stream_;
};

std::unique_ptr<IDemuxer> createFLVDemuxer() {
    return std::make_unique<FLVDemuxerImpl>();
}

} // namespace av_codec
