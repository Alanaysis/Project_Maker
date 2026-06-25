/**
 * @file flv_muxer.cpp
 * @brief FLV 复用器实现
 *
 * FLV容器格式结构：
 * - FLV Header (9 bytes)
 * - PreviousTagSize0 (4 bytes, always 0)
 * - Tag 1
 *   - TagHeader (11 bytes)
 *   - TagData
 * - PreviousTagSize1
 * - Tag 2
 * - ...
 */

#include "container/container.h"
#include <cstring>
#include <fstream>
#include <vector>

namespace av_codec {

class FLVMuxerImpl : public IMuxer {
public:
    int init(const char* filename, ContainerFormat format) override {
        filename_ = filename;
        file_.open(filename, std::ios::binary);
        if (!file_.is_open()) return -1;
        initialized_ = true;
        return 0;
    }

    int addVideoStream(const VideoStreamInfo& info) override {
        video_info_ = info;
        has_video_ = true;
        return 0;
    }

    int addAudioStream(const AudioStreamInfo& info) override {
        audio_info_ = info;
        has_audio_ = true;
        return 1;
    }

    int writeHeader() override {
        if (!initialized_) return -1;

        // FLV Header
        writeString("FLV");  // Signature
        writeUInt8(1);       // Version
        uint8_t flags = 0;
        if (has_audio_) flags |= 0x04;
        if (has_video_) flags |= 0x01;
        writeUInt8(flags);   // Flags
        writeUInt32(9);      // Data offset

        // PreviousTagSize0
        writeUInt32(0);

        header_written_ = true;
        return 0;
    }

    int writePacket(const AVPacketData& pkt) override {
        if (!header_written_) return -1;

        // 计算时间戳
        uint32_t timestamp = static_cast<uint32_t>(pkt.pts & 0xFFFFFF);
        uint8_t timestamp_ext = static_cast<uint8_t>((pkt.pts >> 24) & 0xFF);

        // Tag Header
        uint8_t tag_type = (pkt.stream_index == 0) ? 9 : 8;  // 9=video, 8=audio
        uint32_t data_size = pkt.data.size() + (pkt.stream_index == 0 ? 5 : 0);

        writeUInt8(tag_type);           // Tag type
        writeUInt24(data_size);         // Data size
        writeUInt24(timestamp);         // Timestamp
        writeUInt8(timestamp_ext);      // Timestamp extended
        writeUInt24(0);                 // Stream ID

        // Tag Data
        if (pkt.stream_index == 0) {
            // Video tag
            writeVideoTag(pkt);
        } else {
            // Audio tag
            writeAudioTag(pkt);
        }

        // PreviousTagSize
        writeUInt32(11 + data_size);

        return 0;
    }

    int writeTrailer() override {
        if (!header_written_) return -1;
        file_.close();
        return 0;
    }

    void close() override {
        if (file_.is_open()) file_.close();
        initialized_ = false;
    }

private:
    void writeVideoTag(const AVPacketData& pkt) {
        // Frame type (4 bits) | Codec ID (4 bits)
        uint8_t frame_type = pkt.keyframe ? 0x10 : 0x20;
        uint8_t codec_id = 7;  // AVC (H.264)
        writeUInt8(frame_type | codec_id);

        // AVC packet type
        writeUInt8(1);  // 1=NALU

        // Composition time
        writeUInt24(0);

        // Data
        file_.write(reinterpret_cast<const char*>(pkt.data.data()), pkt.data.size());
    }

    void writeAudioTag(const AVPacketData& pkt) {
        // Sound format (4 bits) | Rate (2 bits) | Size (1 bit) | Type (1 bit)
        uint8_t sound_info = 0xA0;  // AAC, 44kHz, 16bit, Stereo
        writeUInt8(sound_info);

        // AAC packet type
        writeUInt8(1);  // 1=Raw

        // Data
        file_.write(reinterpret_cast<const char*>(pkt.data.data()), pkt.data.size());
    }

    void writeUInt8(uint8_t value) {
        file_.write(reinterpret_cast<const char*>(&value), 1);
    }

    void writeUInt24(uint32_t value) {
        uint8_t bytes[3] = {
            static_cast<uint8_t>((value >> 16) & 0xFF),
            static_cast<uint8_t>((value >> 8) & 0xFF),
            static_cast<uint8_t>(value & 0xFF)
        };
        file_.write(reinterpret_cast<const char*>(bytes), 3);
    }

    void writeUInt32(uint32_t value) {
        uint8_t bytes[4] = {
            static_cast<uint8_t>((value >> 24) & 0xFF),
            static_cast<uint8_t>((value >> 16) & 0xFF),
            static_cast<uint8_t>((value >> 8) & 0xFF),
            static_cast<uint8_t>(value & 0xFF)
        };
        file_.write(reinterpret_cast<const char*>(bytes), 4);
    }

    void writeString(const char* str) {
        file_.write(str, strlen(str));
    }

private:
    std::string filename_;
    std::ofstream file_;
    bool initialized_ = false;
    bool header_written_ = false;
    bool has_video_ = false;
    bool has_audio_ = false;
    VideoStreamInfo video_info_;
    AudioStreamInfo audio_info_;
};

std::unique_ptr<IMuxer> createFLVMuxer() {
    return std::make_unique<FLVMuxerImpl>();
}

} // namespace av_codec
