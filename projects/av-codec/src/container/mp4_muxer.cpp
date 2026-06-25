/**
 * @file mp4_muxer.cpp
 * @brief MP4 复用器实现
 *
 * MP4容器格式结构：
 * - ftyp：文件类型
 * - moov：电影元数据
 *   - mvhd：电影头
 *   - trak：轨道
 *     - tkhd：轨道头
 *     - mdia：媒体数据
 *       - mdhd：媒体头
 *       - hdlr：处理器引用
 *       - minf：媒体信息
 *         - stbl：采样表
 * - mdat：媒体数据
 */

#include "container/container.h"
#include <cstring>
#include <fstream>
#include <vector>

namespace av_codec {

class MP4MuxerImpl : public IMuxer {
public:
    int init(const char* filename, ContainerFormat format) override {
        filename_ = filename;
        format_ = format;
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

        // 写入ftyp box
        writeFTYP();

        // 保存moov位置
        moov_offset_ = file_.tellp();

        // 写入moov box（占位）
        writeMOOV();

        // 保存mdat位置
        mdat_offset_ = file_.tellp();

        // 写入mdat box头
        writeUInt32(0);  // size（稍后更新）
        writeString("mdat");

        header_written_ = true;
        return 0;
    }

    int writePacket(const AVPacketData& pkt) override {
        if (!header_written_) return -1;

        // 写入数据
        file_.write(reinterpret_cast<const char*>(pkt.data.data()), pkt.data.size());

        // 记录采样信息
        SampleInfo sample;
        sample.offset = current_offset_;
        sample.size = pkt.data.size();
        sample.pts = pkt.pts;
        sample.keyframe = pkt.keyframe;
        samples_[pkt.stream_index].push_back(sample);

        current_offset_ += pkt.data.size();
        return 0;
    }

    int writeTrailer() override {
        if (!header_written_) return -1;

        // 更新mdat大小
        int64_t mdat_size = current_offset_ - mdat_offset_ + 8;
        file_.seekp(mdat_offset_);
        writeUInt32(static_cast<uint32_t>(mdat_size));

        // 更新moov
        file_.seekp(moov_offset_);
        writeMOOV();

        file_.close();
        return 0;
    }

    void close() override {
        if (file_.is_open()) file_.close();
        initialized_ = false;
    }

private:
    void writeFTYP() {
        // ftyp box
        writeUInt32(20);  // size
        writeString("ftyp");
        writeString("isom");  // major brand
        writeUInt32(0x200);   // minor version
        writeString("isom");  // compatible brands
    }

    void writeMOOV() {
        // moov box
        writeUInt32(0);  // size（占位）
        writeString("moov");

        // mvhd
        writeMVHD();

        // trak（每个流一个）
        for (const auto& stream : streams_) {
            writeTRAK(stream);
        }
    }

    void writeMVHD() {
        writeUInt32(108);  // size
        writeString("mvhd");
        writeUInt32(0);    // version + flags
        writeUInt32(0);    // creation time
        writeUInt32(0);    // modification time
        writeUInt32(1000); // timescale
        writeUInt32(0);    // duration

        // 矩阵
        for (int i = 0; i < 9; i++) {
            writeUInt32(i == 0 || i == 4 || i == 8 ? 0x00010000 : 0);
        }

        writeUInt32(0);  // pre-defined
        writeUInt32(0);  // pre-defined
        writeUInt32(0);  // pre-defined
        writeUInt32(0);  // pre-defined
        writeUInt32(0);  // pre-defined
        writeUInt32(0);  // next track ID
    }

    void writeTRAK(const StreamInfo& stream) {
        writeUInt32(0);  // size（占位）
        writeString("trak");

        // tkhd
        writeTKHD(stream);

        // mdia
        writeMDIA(stream);
    }

    void writeTKHD(const StreamInfo& stream) {
        writeUInt32(92);  // size
        writeString("tkhd");
        writeUInt32(0x00000003);  // version + flags (enabled + in-movie)
        writeUInt32(0);  // creation time
        writeUInt32(0);  // modification time
        writeUInt32(stream.index);  // track ID
        writeUInt32(0);  // reserved
        writeUInt32(0);  // duration

        for (int i = 0; i < 6; i++) writeUInt32(0);  // reserved

        if (stream.type == StreamType::VIDEO) {
            writeUInt16(stream.video.width << 16);   // width
            writeUInt16(stream.video.height << 16);  // height
        } else {
            writeUInt32(0);
            writeUInt32(0);
        }
    }

    void writeMDIA(const StreamInfo& stream) {
        writeUInt32(0);  // size（占位）
        writeString("mdia");

        // mdhd
        writeMDHD(stream);

        // hdlr
        writeHDLR(stream);
    }

    void writeMDHD(const StreamInfo& stream) {
        writeUInt32(32);  // size
        writeString("mdhd");
        writeUInt32(0);  // version + flags
        writeUInt32(0);  // creation time
        writeUInt32(0);  // modification time

        if (stream.type == StreamType::VIDEO) {
            writeUInt32(stream.video.fps_num);  // timescale
        } else {
            writeUInt32(stream.audio.sample_rate);
        }

        writeUInt32(0);  // duration
        writeUInt16(0x55C4);  // language (und)
        writeUInt16(0);  // pre-defined
    }

    void writeHDLR(const StreamInfo& stream) {
        writeUInt32(45);  // size
        writeString("hdlr");
        writeUInt32(0);  // version + flags

        if (stream.type == StreamType::VIDEO) {
            writeString("vide");  // handler type
            writeString("VideoHandler");
        } else {
            writeString("soun");  // handler type
            writeString("SoundHandler");
        }
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

    void writeUInt16(uint16_t value) {
        uint8_t bytes[2] = {
            static_cast<uint8_t>((value >> 8) & 0xFF),
            static_cast<uint8_t>(value & 0xFF)
        };
        file_.write(reinterpret_cast<const char*>(bytes), 2);
    }

    void writeString(const char* str) {
        file_.write(str, strlen(str));
    }

private:
    struct SampleInfo {
        int64_t offset = 0;
        int size = 0;
        int64_t pts = 0;
        bool keyframe = false;
    };

    std::string filename_;
    ContainerFormat format_;
    std::ofstream file_;
    bool initialized_ = false;
    bool header_written_ = false;
    int64_t moov_offset_ = 0;
    int64_t mdat_offset_ = 0;
    int64_t current_offset_ = 0;
    std::vector<StreamInfo> streams_;
    std::vector<std::vector<SampleInfo>> samples_;
};

std::unique_ptr<IMuxer> createMP4Muxer() {
    return std::make_unique<MP4MuxerImpl>();
}

} // namespace av_codec
