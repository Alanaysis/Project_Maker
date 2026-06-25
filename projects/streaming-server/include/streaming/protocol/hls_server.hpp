#pragma once

/**
 * @file hls_server.hpp
 * @brief HLS 协议服务器
 *
 * 实现 HLS (HTTP Live Streaming) 服务器，支持：
 * - M3U8 播放列表生成
 * - TS 切片生成
 * - 自适应码率切换
 * - 实时切片和点播切片
 * - 加密支持
 */

#include "streaming/types.hpp"
#include <string>
#include <memory>
#include <vector>
#include <functional>
#include <unordered_map>
#include <mutex>
#include <thread>
#include <atomic>
#include <filesystem>

namespace streaming {

// HLS 播放列表类型
enum class HlsPlaylistType {
    Live,       // 直播
    VOD,        // 点播
    Event       // 事件
};

// HLS 加密方法
enum class HlsEncryptionMethod {
    None,
    AES_128,
    SampleAES
};

// HLS 切片信息
struct HlsSegment {
    uint32_t sequence_number = 0;
    std::string filename;
    double duration = 0.0;      // 秒
    uint64_t size = 0;          // 字节
    Timestamp start_time;
    Timestamp end_time;
    bool is_keyframe_aligned = true;
    Buffer data;
};

using HlsSegmentPtr = std::shared_ptr<HlsSegment>;

// HLS 变体流
struct HlsVariantStream {
    uint32_t bandwidth = 0;     // bps
    uint32_t width = 0;
    uint32_t height = 0;
    std::string codecs;
    std::string playlist_url;
    MediaParams media_params;
};

// HLS 播放列表
struct HlsPlaylist {
    HlsPlaylistType type = HlsPlaylistType::Live;
    uint32_t version = 3;
    uint32_t target_duration = 0;   // 秒
    uint32_t media_sequence = 0;
    double target_segment_duration = 6.0;  // 秒
    bool allow_cache = false;
    std::string playlist_type;      // "VOD" or "EVENT"
    std::vector<HlsSegmentPtr> segments;
    std::vector<HlsVariantStream> variants;

    // 加密信息
    HlsEncryptionMethod encryption = HlsEncryptionMethod::None;
    std::string encryption_key_uri;
    std::string encryption_iv;
};

/**
 * @brief TS 封装器
 */
class TsMuxer {
public:
    TsMuxer();
    ~TsMuxer();

    // 初始化
    bool initialize(const MediaParams& params);
    void close();

    // 封装媒体帧
    Buffer mux_frame(const MediaFrame& frame);

    // 获取 PAT/PMT
    Buffer get_pat();
    Buffer get_pmt();

private:
    // TS 包生成
    Buffer create_ts_packet(uint8_t pid, bool payload_unit_start,
                            uint8_t continuity_counter, const Buffer& payload);
    Buffer create_pat_packet();
    Buffer create_pmt_packet();

    // PES 封装
    Buffer create_pes_packet(const MediaFrame& frame);

    // 成员变量
    MediaParams params_;
    bool initialized_ = false;

    uint16_t pmt_pid_ = 0x100;
    uint16_t video_pid_ = 0x100;
    uint16_t audio_pid_ = 0x101;
    uint8_t video_cc_ = 0;
    uint8_t audio_cc_ = 0;

    uint32_t pcr_base_ = 0;
    uint32_t pcr_ext_ = 0;
};

/**
 * @brief HLS 切片器
 */
class HlsSegmenter {
public:
    HlsSegmenter();
    ~HlsSegmenter();

    // 配置
    void set_target_duration(double duration) { target_duration_ = duration; }
    void set_segment_count(uint32_t count) { max_segments_ = count; }
    void set_output_path(const std::string& path) { output_path_ = path; }

    // 初始化
    bool initialize(const MediaParams& params);
    void close();

    // 处理媒体帧
    void process_frame(const MediaFrame& frame);

    // 获取切片
    std::vector<HlsSegmentPtr> get_segments() const;
    HlsSegmentPtr get_latest_segment() const;

    // 回调
    using SegmentCallback = std::function<void(HlsSegmentPtr)>;
    void set_segment_callback(SegmentCallback callback) { segment_callback_ = std::move(callback); }

private:
    void start_new_segment();
    void finish_current_segment();
    bool should_start_new_segment(const MediaFrame& frame) const;

    double target_duration_ = 6.0;
    uint32_t max_segments_ = 5;
    std::string output_path_;

    std::unique_ptr<TsMuxer> muxer_;
    std::vector<HlsSegmentPtr> segments_;
    HlsSegmentPtr current_segment_;
    uint32_t next_sequence_number_ = 0;

    Buffer current_segment_data_;
    double current_segment_duration_ = 0.0;
    int64_t segment_start_pts_ = -1;

    SegmentCallback segment_callback_;
    mutable std::mutex mutex_;
};

/**
 * @brief M3U8 生成器
 */
class M3u8Generator {
public:
    /**
     * @brief 生成媒体播放列表
     * @param playlist 播放列表信息
     * @return M3U8 内容
     */
    static std::string generate_media_playlist(const HlsPlaylist& playlist);

    /**
     * @brief 生成多码率播放列表
     * @param variants 变体流列表
     * @return M3U8 内容
     */
    static std::string generate_master_playlist(const std::vector<HlsVariantStream>& variants);

private:
    static std::string get_encryption_tag(const HlsPlaylist& playlist);
};

/**
 * @brief HLS 服务器
 */
class HlsServer {
public:
    HlsServer();
    ~HlsServer();

    // 服务器控制
    bool start(const std::string& host, uint16_t port);
    void stop();
    bool is_running() const { return running_; }

    // 配置
    void set_segment_duration(double duration) { segment_duration_ = duration; }
    void set_segment_count(uint32_t count) { segment_count_ = count; }
    void set_output_path(const std::string& path) { output_path_ = path; }

    // 流管理
    void add_stream(const std::string& stream_name, const MediaParams& params);
    void remove_stream(const std::string& stream_name);

    // 接收媒体数据
    void push_frame(const std::string& stream_name, const MediaFrame& frame);

    // 统计
    uint32_t get_viewer_count(const std::string& stream_name) const;

private:
    void http_loop();
    void handle_http_request(int client_fd, const std::string& request);

    // 请求处理
    void handle_playlist_request(int client_fd, const std::string& stream_name);
    void handle_segment_request(int client_fd, const std::string& stream_name,
                                const std::string& segment_name);
    void handle_master_playlist_request(int client_fd);

    // HTTP 响应
    void send_http_response(int client_fd, int status_code,
                           const std::string& content_type, const std::string& body);
    void send_http_error(int client_fd, int status_code, const std::string& message);

    // 流信息
    struct StreamInfo {
        MediaParams params;
        std::unique_ptr<HlsSegmenter> segmenter;
        HlsPlaylist playlist;
        uint32_t viewer_count = 0;
    };

    std::string host_;
    uint16_t port_ = 8080;
    int listen_fd_ = -1;
    std::atomic<bool> running_{false};

    double segment_duration_ = 6.0;
    uint32_t segment_count_ = 5;
    std::string output_path_ = "./hls";

    std::thread http_thread_;
    std::unordered_map<std::string, std::unique_ptr<StreamInfo>> streams_;
    mutable std::mutex streams_mutex_;
};

} // namespace streaming
