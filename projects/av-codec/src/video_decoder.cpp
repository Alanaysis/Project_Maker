#include "video_decoder.h"
#include <iostream>

VideoDecoder::VideoDecoder()
    : codec_ctx_(nullptr), codec_(nullptr), initialized_(false) {
}

VideoDecoder::~VideoDecoder() {
    close();
}

int VideoDecoder::init(const VideoDecoderConfig& config) {
    if (initialized_) {
        std::cerr << "Decoder already initialized" << std::endl;
        return -1;
    }

    // 查找解码器
    codec_ = avcodec_find_decoder(config.codec_id);
    if (!codec_) {
        std::cerr << "Decoder not found" << std::endl;
        return -1;
    }

    // 创建解码器上下文
    codec_ctx_ = avcodec_alloc_context3(codec_);
    if (!codec_ctx_) {
        std::cerr << "Could not allocate codec context" << std::endl;
        return -1;
    }

    // 设置解码参数
    if (config.width > 0) {
        codec_ctx_->width = config.width;
    }
    if (config.height > 0) {
        codec_ctx_->height = config.height;
    }
    codec_ctx_->pix_fmt = config.pix_fmt;

    // 打开解码器
    int ret = avcodec_open2(codec_ctx_, codec_, nullptr);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Could not open codec: " << errbuf << std::endl;
        avcodec_free_context(&codec_ctx_);
        return ret;
    }

    initialized_ = true;
    return 0;
}

int VideoDecoder::decode(const AVPacket* pkt, AVFrame* frame) {
    if (!initialized_) {
        std::cerr << "Decoder not initialized" << std::endl;
        return -1;
    }

    // 发送数据包到解码器
    int ret = avcodec_send_packet(codec_ctx_, pkt);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Error sending packet: " << errbuf << std::endl;
        return ret;
    }

    // 接收解码后的帧
    ret = avcodec_receive_frame(codec_ctx_, frame);
    if (ret < 0) {
        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
            return ret;
        }
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Error receiving frame: " << errbuf << std::endl;
        return ret;
    }

    return 0;
}

int VideoDecoder::flush(AVFrame* frame) {
    if (!initialized_) {
        return -1;
    }

    // 发送NULL数据包刷新解码器
    int ret = avcodec_send_packet(codec_ctx_, nullptr);
    if (ret < 0) {
        return ret;
    }

    // 接收剩余的帧
    ret = avcodec_receive_frame(codec_ctx_, frame);
    return ret;
}

const char* VideoDecoder::getName() const {
    return codec_ ? codec_->name : "unknown";
}

void VideoDecoder::close() {
    if (codec_ctx_) {
        avcodec_free_context(&codec_ctx_);
        codec_ctx_ = nullptr;
    }
    codec_ = nullptr;
    initialized_ = false;
}
