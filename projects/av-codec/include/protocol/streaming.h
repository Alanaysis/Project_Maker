#pragma once

/**
 * @file streaming.h
 * @brief 流媒体协议接口定义
 *
 * 支持的协议：
 * - RTMP：实时消息协议，直播推流常用
 * - RTSP：实时流协议，监控/点播常用
 * - HLS：HTTP直播流，苹果主导
 * - DASH：动态自适应流，通用标准
 * - WebRTC：Web实时通信，浏览器原生支持
 */

#include <cstdint>
#include <vector>
#include <string>
#include <functional>

namespace av_codec {

/**
 * @brief 流媒体协议类型
 */
enum class StreamingProtocol : uint8_t {
    RTMP = 0,   ///< RTMP协议
    RTSP = 1,   ///< RTSP协议
    HLS = 2,    ///< HLS协议
    DASH = 3,   ///< DASH协议
    WEBRTC = 4  ///< WebRTC协议
};

/**
 * @brief 流状态
 */
enum class StreamState : uint8_t {
    IDLE = 0,       ///< 空闲
    CONNECTING = 1, ///< 连接中
    CONNECTED = 2,  ///< 已连接
    STREAMING = 3,  ///< 推流/拉流中
    PAUSED = 4,     ///< 暂停
    DISCONNECTED = 5, ///< 已断开
    ERROR = 6       ///< 错误
};

/**
 * @brief 媒体类型
 */
enum class MediaType : uint8_t {
    VIDEO = 0,  ///< 视频
    AUDIO = 1,  ///< 音频
    DATA = 2    ///< 数据
};

/**
 * @brief 媒体描述
 */
struct MediaDescription {
    MediaType type = MediaType::VIDEO; ///< 媒体类型
    std::string codec;              ///< 编码名称
    int width = 0;                  ///< 视频宽度
    int height = 0;                 ///< 视频高度
    int fps = 0;                    ///< 帧率
    int sample_rate = 0;            ///< 采样率
    int channels = 0;               ///< 通道数
    int bitrate = 0;                ///< 比特率
    std::string profile;            ///< 编码Profile
    std::string level;              ///< 编码Level
};

/**
 * @brief 流配置
 */
struct StreamConfig {
    StreamingProtocol protocol = StreamingProtocol::RTMP; ///< 协议类型
    std::string url;                ///< 流URL
    std::string app_name;           ///< 应用名称
    std::string stream_name;        ///< 流名称
    int timeout_ms = 5000;          ///< 超时时间（毫秒）
    int reconnect_count = 3;        ///< 重连次数
    int reconnect_interval_ms = 1000; ///< 重连间隔（毫秒）
    bool enable_audio = true;       ///< 启用音频
    bool enable_video = true;       ///< 启用视频
    std::vector<MediaDescription> media; ///< 媒体描述
};

/**
 * @brief 流统计信息
 */
struct StreamStats {
    int64_t bytes_sent = 0;         ///< 已发送字节数
    int64_t bytes_received = 0;     ///< 已接收字节数
    int64_t frames_sent = 0;        ///< 已发送帧数
    int64_t frames_received = 0;    ///< 已接收帧数
    int64_t frames_dropped = 0;     ///< 丢弃帧数
    double current_bitrate = 0.0;   ///< 当前码率
    double current_fps = 0.0;       ///< 当前帧率
    int64_t latency_ms = 0;         ///< 延迟（毫秒）
    int64_t buffer_ms = 0;          ///< 缓冲时间（毫秒）
};

/**
 * @brief 回调函数类型
 */
using OnStateChangeCallback = std::function<void(StreamState state)>;
using OnDataCallback = std::function<void(const uint8_t* data, int size)>;
using OnErrorCallback = std::function<void(int code, const char* msg)>;

/**
 * @brief 推流器接口
 */
class IStreamPublisher {
public:
    virtual ~IStreamPublisher() = default;

    /**
     * @brief 初始化推流器
     * @param config 流配置
     * @return 0成功，负数失败
     */
    virtual int init(const StreamConfig& config) = 0;

    /**
     * @brief 连接到服务器
     * @return 0成功，负数失败
     */
    virtual int connect() = 0;

    /**
     * @brief 发送视频数据
     * @param data 视频数据
     * @param size 数据大小
     * @param pts 时间戳
     * @param keyframe 是否关键帧
     * @return 0成功，负数失败
     */
    virtual int sendVideo(const uint8_t* data, int size, int64_t pts, bool keyframe) = 0;

    /**
     * @brief 发送音频数据
     * @param data 音频数据
     * @param size 数据大小
     * @param pts 时间戳
     * @return 0成功，负数失败
     */
    virtual int sendAudio(const uint8_t* data, int size, int64_t pts) = 0;

    /**
     * @brief 获取流状态
     * @return 流状态
     */
    virtual StreamState getState() const = 0;

    /**
     * @brief 获取统计信息
     * @return 统计信息
     */
    virtual StreamStats getStats() const = 0;

    /**
     * @brief 设置状态回调
     * @param callback 回调函数
     */
    virtual void setOnStateChange(OnStateChangeCallback callback) = 0;

    /**
     * @brief 设置错误回调
     * @param callback 回调函数
     */
    virtual void setOnError(OnErrorCallback callback) = 0;

    /**
     * @brief 断开连接
     */
    virtual void disconnect() = 0;

    /**
     * @brief 关闭推流器
     */
    virtual void close() = 0;
};

/**
 * @brief 拉流器接口
 */
class IStreamSubscriber {
public:
    virtual ~IStreamSubscriber() = default;

    /**
     * @brief 初始化拉流器
     * @param config 流配置
     * @return 0成功，负数失败
     */
    virtual int init(const StreamConfig& config) = 0;

    /**
     * @brief 连接到服务器
     * @return 0成功，负数失败
     */
    virtual int connect() = 0;

    /**
     * @brief 开始接收流
     * @return 0成功，负数失败
     */
    virtual int start() = 0;

    /**
     * @brief 暂停接收
     * @return 0成功，负数失败
     */
    virtual int pause() = 0;

    /**
     * @brief 恢复接收
     * @return 0成功，负数失败
     */
    virtual int resume() = 0;

    /**
     * @brief 停止接收
     * @return 0成功，负数失败
     */
    virtual int stop() = 0;

    /**
     * @brief 获取流状态
     * @return 流状态
     */
    virtual StreamState getState() const = 0;

    /**
     * @brief 获取统计信息
     * @return 统计信息
     */
    virtual StreamStats getStats() const = 0;

    /**
     * @brief 设置数据回调
     * @param callback 回调函数
     */
    virtual void setOnData(OnDataCallback callback) = 0;

    /**
     * @brief 设置状态回调
     * @param callback 回调函数
     */
    virtual void setOnStateChange(OnStateChangeCallback callback) = 0;

    /**
     * @brief 设置错误回调
     * @param callback 回调函数
     */
    virtual void setOnError(OnErrorCallback callback) = 0;

    /**
     * @brief 断开连接
     */
    virtual void disconnect() = 0;

    /**
     * @brief 关闭拉流器
     */
    virtual void close() = 0;
};

} // namespace av_codec
