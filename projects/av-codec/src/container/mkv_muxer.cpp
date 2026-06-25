/**
 * @file mkv_muxer.cpp
 * @brief MKV 复用器实现
 *
 * MKV容器格式结构：
 * - EBML Header
 * - Segment
 *   - SegmentInfo
 *   - Tracks
 *   - Cluster
 *     - Timecode
 *     - SimpleBlock/Block
 */

#include "container/container.h"
#include <cstring>
#include <fstream>
#include <vector>

namespace av_codec {

class MKVMuxerImpl : public IMuxer {
public:
    int init(const char* filename, ContainerFormat format) override {
        filename_ = filename;
        file_.open(filename, std::ios::binary);
        if (!file_.is_open()) return -1;
        initialized_ = true;
        return 0;
    }

    int addVideoStream(const VideoStreamInfo& info) override {
        StreamInfo stream;
        stream.index = streams_.size();
        stream.type = StreamType::VIDEO;
        stream.video = info;
        streams_.push_back(stream);
        return stream.index;
    }

    int addAudioStream(const AudioStreamInfo& info) override {
        StreamInfo stream;
        stream.index = streams_.size();
        stream.type = StreamType::AUDIO;
        stream.audio = info;
        streams_.push_back(stream);
        return stream.index;
    }

    int writeHeader() override {
        if (!initialized_) return -1;

        // 写入EBML头
        writeEBMLHeader();

        // 写入Segment
        writeSegmentHeader();

        // 写入SegmentInfo
        writeSegmentInfo();

        // 写入Tracks
        writeTracks();

        header_written_ = true;
        return 0;
    }

    int writePacket(const AVPacketData& pkt) override {
        if (!header_written_) return -1;

        // 写入SimpleBlock
        writeSimpleBlock(pkt);

        return 0;
    }

    int writeTrailer() override {
        if (!header_written_) return -1;

        // 写入Cues（可选）
        writeCues();

        file_.close();
        return 0;
    }

    void close() override {
        if (file_.is_open()) file_.close();
        initialized_ = false;
    }

private:
    void writeEBMLHeader() {
        // EBML Header
        writeElementID(0x1A45DFA3);  // EBML
        writeElementSize(31);

        // EBMLVersion
        writeElementID(0x4286);
        writeElementSize(1);
        writeUInt8(1);

        // EBMLReadVersion
        writeElementID(0x42F7);
        writeElementSize(1);
        writeUInt8(1);

        // EBMLMaxIDLength
        writeElementID(0x42F2);
        writeElementSize(1);
        writeUInt8(4);

        // EBMLMaxSizeLength
        writeElementID(0x42F3);
        writeElementSize(1);
        writeUInt8(8);

        // DocType
        writeElementID(0x4282);
        writeElementSize(8);
        writeString("matroska");

        // DocTypeVersion
        writeElementID(0x4287);
        writeElementSize(1);
        writeUInt8(4);

        // DocTypeReadVersion
        writeElementID(0x4285);
        writeElementSize(1);
        writeUInt8(2);
    }

    void writeSegmentHeader() {
        // Segment
        writeElementID(0x18538067);
        writeElementSize(0xFFFFFFFFFFFFFF);  // 未知大小
    }

    void writeSegmentInfo() {
        // SegmentInfo
        writeElementID(0x1549A966);
        writeElementSize(0);  // 简化

        // TimecodeScale
        writeElementID(0x2AD7B1);
        writeElementSize(4);
        writeUInt32(1000000);  // 1ms

        // MuxingApp
        writeElementID(0x4D80);
        writeElementSize(10);
        writeString("av-codec");

        // WritingApp
        writeElementID(0x5741);
        writeElementSize(10);
        writeString("av-codec");
    }

    void writeTracks() {
        // Tracks
        writeElementID(0x1654AE6B);
        writeElementSize(0);  // 简化

        for (const auto& stream : streams_) {
            writeTrackEntry(stream);
        }
    }

    void writeTrackEntry(const StreamInfo& stream) {
        // TrackEntry
        writeElementID(0xAE);
        writeElementSize(0);  // 简化

        // TrackNumber
        writeElementID(0xD7);
        writeElementSize(1);
        writeUInt8(stream.index + 1);

        // TrackUID
        writeElementID(0x73C5);
        writeElementSize(4);
        writeUInt32(stream.index + 1);

        // CodecID
        writeElementID(0x86);
        if (stream.type == StreamType::VIDEO) {
            writeElementSize(5);
            writeString("V_MPEG4/ISO/AVC");
        } else {
            writeElementSize(5);
            writeString("A_AAC");
        }
    }

    void writeSimpleBlock(const AVPacketData& pkt) {
        // SimpleBlock
        writeElementID(0xA3);
        writeElementSize(pkt.data.size() + 4);

        // Track number
        writeElementSize(pkt.stream_index + 1);

        // Timecode (relative to cluster)
        int16_t timecode = static_cast<int16_t>(pkt.pts - cluster_timecode_);
        writeUInt8((timecode >> 8) & 0xFF);
        writeUInt8(timecode & 0xFF);

        // Flags
        writeUInt8(pkt.keyframe ? 0x80 : 0x00);

        // Data
        file_.write(reinterpret_cast<const char*>(pkt.data.data()), pkt.data.size());
    }

    void writeCues() {
        // Cues（索引）
        writeElementID(0x1C53BB6B);
        writeElementSize(0);
    }

    void writeElementID(uint32_t id) {
        if (id < 0x100) {
            writeUInt8(static_cast<uint8_t>(id));
        } else if (id < 0x10000) {
            writeUInt8(static_cast<uint8_t>((id >> 8) & 0xFF));
            writeUInt8(static_cast<uint8_t>(id & 0xFF));
        } else if (id < 0x1000000) {
            writeUInt8(static_cast<uint8_t>((id >> 16) & 0xFF));
            writeUInt8(static_cast<uint8_t>((id >> 8) & 0xFF));
            writeUInt8(static_cast<uint8_t>(id & 0xFF));
        } else {
            writeUInt8(static_cast<uint8_t>((id >> 24) & 0xFF));
            writeUInt8(static_cast<uint8_t>((id >> 16) & 0xFF));
            writeUInt8(static_cast<uint8_t>((id >> 8) & 0xFF));
            writeUInt8(static_cast<uint8_t>(id & 0xFF));
        }
    }

    void writeElementSize(uint64_t size) {
        // 简化：写入8字节
        for (int i = 7; i >= 0; i--) {
            writeUInt8(static_cast<uint8_t>((size >> (i * 8)) & 0xFF));
        }
    }

    void writeUInt8(uint8_t value) {
        file_.write(reinterpret_cast<const char*>(&value), 1);
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
    int64_t cluster_timecode_ = 0;
    std::vector<StreamInfo> streams_;
};

std::unique_ptr<IMuxer> createMKVMuxer() {
    return std::make_unique<MKVMuxerImpl>();
}

} // namespace av_codec
