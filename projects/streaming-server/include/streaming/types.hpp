#pragma once

/**
 * @file types.hpp
 * @brief 流媒体服务器核心类型定义
 *
 * 定义流媒体服务器中使用的所有基础数据类型、枚举和常量。
 */

#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include <chrono>
#include <functional>
#include <unordered_map>

namespace streaming {

// ============================================================================
// 基础类型别名
// ============================================================================

using Timestamp = std::chrono::steady_clock::time_point;
using Duration = std::chrono::steady_clock::duration;
using Milliseconds = std::chrono::milliseconds;
using Seconds = std::chrono::seconds;

using Buffer = std::vector<uint8_t>;
using BufferPtr = std::shared_ptr<Buffer>;

// ============================================================================
// 协议类型枚举
// ============================================================================

/**
 * @brief 支持的流媒体协议类型
 */
enum class ProtocolType {
    RTMP,       // Real-Time Messaging Protocol
    RTSP,       // Real-Time Streaming Protocol
    HLS,        // HTTP Live Streaming
    DASH,       // Dynamic Adaptive Streaming over HTTP
    WebRTC,     // Web Real-Time Communication
    HTTP_FLV,   // HTTP-FLV
    WebSocket   // WebSocket
};

/**
 * @brief 媒体类型枚举
 */
enum class MediaType {
    Video,
    Audio,
    Subtitle,
    Data
};

/**
 * @brief 视频编码类型
 */
enum class VideoCodec {
    H264,
    H265,
    VP8,
    VP9,
    AV1,
    Unknown
};

/**
 * @brief 音频编码类型
 */
enum class AudioCodec {
    AAC,
    MP3,
    OPUS,
    VORBIS,
    PCM,
    Unknown
};

/**
 * @brief 容器格式
 */
enum class ContainerFormat {
    FLV,
    MP4,
    TS,     // MPEG-TS
    MKV,
    WebM,
    Unknown
};

/**
 * @brief 流状态
 */
enum class StreamState {
    Idle,
    Connecting,
    Connected,
    Streaming,
    Paused,
    Stopping,
    Stopped,
    Error
};

// ============================================================================
// 媒体参数结构
// ============================================================================

/**
 * @brief 视频参数
 */
struct VideoParams {
    VideoCodec codec = VideoCodec::Unknown;
    uint32_t width = 0;
    uint32_t height = 0;
    double framerate = 0.0;
    uint32_t bitrate = 0;       // bps
    uint32_t gop_size = 0;
    std::string profile;
    std::string level;
};

/**
 * @brief 音频参数
 */
struct AudioParams {
    AudioCodec codec = AudioCodec::Unknown;
    uint32_t sample_rate = 0;
    uint32_t channels = 0;
    uint32_t bitrate = 0;       // bps
    uint32_t bits_per_sample = 0;
};

/**
 * @brief 媒体参数
 */
struct MediaParams {
    VideoParams video;
    AudioParams audio;
    ContainerFormat format = ContainerFormat::Unknown;
    double duration = 0.0;  // 秒
};

// ============================================================================
// 帧数据结构
// ============================================================================

/**
 * @brief 媒体帧类型
 */
enum class FrameType {
    VideoKeyFrame,      // 视频关键帧 (I帧)
    VideoInterFrame,    // 视频帧间帧 (P/B帧)
    AudioFrame,         // 音频帧
    VideoConfig,        // 视频配置帧 (SPS/PPS)
    AudioConfig,        // 音频配置帧
    Unknown
};

/**
 * @brief 媒体帧
 */
struct MediaFrame {
    FrameType type = FrameType::Unknown;
    MediaType media_type = MediaType::Video;
    Buffer data;
    Timestamp timestamp;
    int64_t pts = 0;        // 显示时间戳
    int64_t dts = 0;        // 解码时间戳
    uint32_t stream_index = 0;
    bool is_keyframe = false;
    uint32_t duration = 0;
};

using MediaFramePtr = std::shared_ptr<MediaFrame>;

// ============================================================================
// 回调类型定义
// ============================================================================

/**
 * @brief 帧回调
 */
using FrameCallback = std::function<void(MediaFramePtr)>;

/**
 * @brief 连接回调
 */
using ConnectionCallback = std::function<void(uint64_t session_id, bool connected)>;

/**
 * @brief 错误回调
 */
using ErrorCallback = std::function<void(int error_code, const std::string& message)>;

// ============================================================================
// 统计信息
// ============================================================================

/**
 * @brief 流统计信息
 */
struct StreamStats {
    uint64_t bytes_sent = 0;
    uint64_t bytes_received = 0;
    uint64_t frames_sent = 0;
    uint64_t frames_received = 0;
    uint64_t frames_dropped = 0;
    double current_bitrate = 0.0;
    double current_fps = 0.0;
    uint32_t viewers = 0;
    Milliseconds latency{0};
    Timestamp start_time;
    Duration uptime{0};
};

/**
 * @brief 服务器统计信息
 */
struct ServerStats {
    uint32_t total_connections = 0;
    uint32_t active_connections = 0;
    uint32_t total_streams = 0;
    uint32_t active_streams = 0;
    uint64_t total_bytes_sent = 0;
    uint64_t total_bytes_received = 0;
    double cpu_usage = 0.0;
    double memory_usage = 0.0;
    double bandwidth_usage = 0.0;
};

// ============================================================================
// 配置结构
// ============================================================================

/**
 * @brief 服务器配置
 */
struct ServerConfig {
    std::string host = "0.0.0.0";
    uint16_t rtmp_port = 1935;
    uint16_t rtsp_port = 554;
    uint16_t http_port = 8080;
    uint16_t webrtc_port = 8443;

    uint32_t max_connections = 1000;
    uint32_t max_streams = 100;
    uint32_t worker_threads = 4;

    std::string log_level = "info";
    std::string log_file = "streaming.log";

    bool enable_hls = true;
    bool enable_dash = true;
    bool enable_recording = false;

    std::string recording_path = "./recordings";
    std::string hls_path = "./hls";
    std::string dash_path = "./dash";
};

} // namespace streaming
