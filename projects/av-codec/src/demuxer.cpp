#include "demuxer.h"
#include <iostream>

Demuxer::Demuxer()
    : fmt_ctx_(nullptr), initialized_(false) {
}

Demuxer::~Demuxer() {
    close();
}

int Demuxer::init(const DemuxerConfig& config) {
    if (initialized_) {
        std::cerr << "Demuxer already initialized" << std::endl;
        return -1;
    }

    if (!config.filename) {
        std::cerr << "Filename is null" << std::endl;
        return -1;
    }

    // 打开输入文件
    int ret = avformat_open_input(&fmt_ctx_, config.filename, nullptr, nullptr);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Could not open input file: " << errbuf << std::endl;
        return ret;
    }

    initialized_ = true;
    return 0;
}

int Demuxer::openInput(const char* filename) {
    if (initialized_) {
        std::cerr << "Demuxer already initialized" << std::endl;
        return -1;
    }

    // 打开输入文件
    int ret = avformat_open_input(&fmt_ctx_, filename, nullptr, nullptr);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Could not open input file: " << errbuf << std::endl;
        return ret;
    }

    initialized_ = true;
    return 0;
}

int Demuxer::findStreamInfo() {
    if (!initialized_) {
        std::cerr << "Demuxer not initialized" << std::endl;
        return -1;
    }

    // 查找流信息
    int ret = avformat_find_stream_info(fmt_ctx_, nullptr);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Could not find stream info: " << errbuf << std::endl;
        return ret;
    }

    return 0;
}

int Demuxer::getStreamCount() const {
    if (!initialized_) {
        return 0;
    }
    return fmt_ctx_->nb_streams;
}

const AVStream* Demuxer::getStream(int index) const {
    if (!initialized_ || index < 0 || index >= (int)fmt_ctx_->nb_streams) {
        return nullptr;
    }
    return fmt_ctx_->streams[index];
}

int Demuxer::readPacket(AVPacket* pkt) {
    if (!initialized_) {
        std::cerr << "Demuxer not initialized" << std::endl;
        return -1;
    }

    // 读取数据包
    int ret = av_read_frame(fmt_ctx_, pkt);
    if (ret < 0) {
        if (ret == AVERROR_EOF) {
            return AVERROR_EOF;
        }
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Error reading frame: " << errbuf << std::endl;
        return ret;
    }

    return 0;
}

void Demuxer::close() {
    if (fmt_ctx_) {
        avformat_close_input(&fmt_ctx_);
        fmt_ctx_ = nullptr;
    }
    initialized_ = false;
}
