#include "video_encoder.h"
#include <iostream>

extern "C" {
#include <libavutil/opt.h>
}

VideoEncoder::VideoEncoder()
    : codec_ctx_(nullptr), codec_(nullptr), initialized_(false) {
}

VideoEncoder::~VideoEncoder() {
    close();
}

int VideoEncoder::init(const VideoEncoderConfig& config) {
    if (initialized_) {
        std::cerr << "Encoder already initialized" << std::endl;
        return -1;
    }

    // 查找H.264编码器
    codec_ = avcodec_find_encoder(AV_CODEC_ID_H264);
    if (!codec_) {
        std::cerr << "H.264 encoder not found" << std::endl;
        return -1;
    }

    // 创建编码器上下文
    codec_ctx_ = avcodec_alloc_context3(codec_);
    if (!codec_ctx_) {
        std::cerr << "Could not allocate codec context" << std::endl;
        return -1;
    }

    // 设置编码参数
    codec_ctx_->width = config.width;
    codec_ctx_->height = config.height;
    codec_ctx_->bit_rate = config.bitrate;
    codec_ctx_->time_base = {1, config.fps};
    codec_ctx_->framerate = {config.fps, 1};
    codec_ctx_->gop_size = config.gop_size;
    codec_ctx_->max_b_frames = config.max_b_frames;
    codec_ctx_->pix_fmt = config.pix_fmt;

    // 设置预设
    if (config.preset) {
        av_opt_set(codec_ctx_->priv_data, "preset", config.preset, 0);
    }

    // 设置档次
    if (config.profile) {
        av_opt_set(codec_ctx_->priv_data, "profile", config.profile, 0);
    }

    // 打开编码器
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

int VideoEncoder::encode(const AVFrame* frame, AVPacket* pkt) {
    if (!initialized_) {
        std::cerr << "Encoder not initialized" << std::endl;
        return -1;
    }

    // 发送帧到编码器
    int ret = avcodec_send_frame(codec_ctx_, frame);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Error sending frame: " << errbuf << std::endl;
        return ret;
    }

    // 接收编码后的数据包
    ret = avcodec_receive_packet(codec_ctx_, pkt);
    if (ret < 0) {
        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
            return ret;
        }
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Error receiving packet: " << errbuf << std::endl;
        return ret;
    }

    return 0;
}

int VideoEncoder::flush(std::vector<AVPacket*>& packets) {
    if (!initialized_) {
        return -1;
    }

    // 发送NULL帧刷新编码器
    int ret = avcodec_send_frame(codec_ctx_, nullptr);
    if (ret < 0) {
        return ret;
    }

    // 接收所有剩余的数据包
    while (true) {
        AVPacket* pkt = av_packet_alloc();
        ret = avcodec_receive_packet(codec_ctx_, pkt);
        if (ret == AVERROR_EOF || ret == AVERROR(EAGAIN)) {
            av_packet_free(&pkt);
            break;
        }
        if (ret < 0) {
            av_packet_free(&pkt);
            return ret;
        }
        packets.push_back(pkt);
    }

    return 0;
}

const char* VideoEncoder::getName() const {
    return codec_ ? codec_->name : "unknown";
}

void VideoEncoder::close() {
    if (codec_ctx_) {
        avcodec_free_context(&codec_ctx_);
        codec_ctx_ = nullptr;
    }
    codec_ = nullptr;
    initialized_ = false;
}
