#include "muxer.h"
#include <iostream>

Muxer::Muxer()
    : fmt_ctx_(nullptr), initialized_(false), header_written_(false) {
}

Muxer::~Muxer() {
    close();
}

int Muxer::init(const MuxerConfig& config) {
    if (initialized_) {
        std::cerr << "Muxer already initialized" << std::endl;
        return -1;
    }

    // 分配输出格式上下文
    int ret = avformat_alloc_output_context2(&fmt_ctx_, nullptr,
                                              config.format,
                                              config.filename);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Could not allocate output context: " << errbuf << std::endl;
        return ret;
    }

    initialized_ = true;
    return 0;
}

int Muxer::addStream(const AVCodecContext* codec_ctx) {
    if (!initialized_) {
        std::cerr << "Muxer not initialized" << std::endl;
        return -1;
    }

    // 创建新流
    AVStream* stream = avformat_new_stream(fmt_ctx_, nullptr);
    if (!stream) {
        std::cerr << "Could not create stream" << std::endl;
        return -1;
    }

    // 复制编解码器参数到流
    int ret = avcodec_parameters_from_context(stream->codecpar, codec_ctx);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Could not copy codec parameters: " << errbuf << std::endl;
        return ret;
    }

    stream->time_base = codec_ctx->time_base;

    return stream->index;
}

int Muxer::writeHeader() {
    if (!initialized_) {
        std::cerr << "Muxer not initialized" << std::endl;
        return -1;
    }

    if (header_written_) {
        std::cerr << "Header already written" << std::endl;
        return -1;
    }

    // 打开输出文件
    int ret = avio_open(&fmt_ctx_->pb, fmt_ctx_->url, AVIO_FLAG_WRITE);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Could not open output file: " << errbuf << std::endl;
        return ret;
    }

    // 写入文件头
    ret = avformat_write_header(fmt_ctx_, nullptr);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Could not write header: " << errbuf << std::endl;
        avio_closep(&fmt_ctx_->pb);
        return ret;
    }

    header_written_ = true;
    return 0;
}

int Muxer::writePacket(AVPacket* pkt) {
    if (!initialized_ || !header_written_) {
        std::cerr << "Muxer not ready" << std::endl;
        return -1;
    }

    // 写入数据包
    int ret = av_interleaved_write_frame(fmt_ctx_, pkt);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Error writing packet: " << errbuf << std::endl;
        return ret;
    }

    return 0;
}

int Muxer::writeTrailer() {
    if (!initialized_ || !header_written_) {
        std::cerr << "Muxer not ready" << std::endl;
        return -1;
    }

    // 写入文件尾
    int ret = av_write_trailer(fmt_ctx_);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Error writing trailer: " << errbuf << std::endl;
        return ret;
    }

    header_written_ = false;
    return 0;
}

void Muxer::close() {
    if (fmt_ctx_) {
        if (header_written_) {
            av_write_trailer(fmt_ctx_);
        }
        if (!(fmt_ctx_->oformat->flags & AVFMT_NOFILE)) {
            avio_closep(&fmt_ctx_->pb);
        }
        avformat_free_context(fmt_ctx_);
        fmt_ctx_ = nullptr;
    }
    initialized_ = false;
    header_written_ = false;
}
