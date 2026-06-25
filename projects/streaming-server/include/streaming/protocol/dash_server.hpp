#pragma once

/**
 * @file dash_server.hpp
 * @brief DASH 协议服务器
 *
 * 实现 DASH (Dynamic Adaptive Streaming over HTTP) 服务器，支持：
 * - MPD 清单生成
 * - 分段 MP4 封装
 * - 自适应码率
 * - 实时和点播模式
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

namespace streaming {

// DASH 配置类型
enum class DashProfile {
    Live,       // 直播
    OnDemand    // 点播
};

// DASH 表示类型
enum class DashRepresentationType {
    Video,
    Audio
};

// DASH 分段
struct DashSegment {
    uint32_t sequence_number = 0;
    std::string filename;
    double duration = 0.0;
    uint64_t size = 0;
    Buffer data;
    bool is_init_segment = false;
};

using DashSegmentPtr = std::shared_ptr<DashSegment>;

// DASH 表示
struct DashRepresentation {
    std::string id;
    DashRepresentationType type = DashRepresentationType::Video;
    uint32_t bandwidth = 0;
    uint32_t width = 0;
    uint32_t height = 0;
    uint32_t sample_rate = 0;
    uint32_t channels = 0;
    std::string codecs;
    std::string mime_type;
    MediaParams media_params;
    std::vector<DashSegmentPtr> segments;
    Buffer init_segment;
};

// DASH 适应集
struct DashAdaptationSet {
    std::string id;
    DashRepresentationType type = DashRepresentationType::Video;
    std::string lang;
    std::vector<DashRepresentation> representations;
};

// DASH 周期
struct DashPeriod {
    std::string id;
    double start = 0.0;
    double duration = 0.0;
    std::vector<DashAdaptationSet> adaptation_sets;
};

// DASH MPD
struct DashMpd {
    DashProfile profile = DashProfile::Live;
    std::string type = "dynamic";   // dynamic or static
    double min_buffer_time = 1.0;
    double min_update_period = 1.0;
    double suggested_presentation_delay = 10.0;
    double availability_start_time = 0.0;
    double publish_time = 0.0;
    uint64_t time_shift_buffer_depth = 30;
    std::vector<DashPeriod> periods;
};

/**
 * @brief fMP4 封装器
 */
class Fmp4Muxer {
public:
    Fmp4Muxer();
    ~Fmp4Muxer();

    // 初始化
    bool initialize(const MediaParams& params);
    void close();

    // 生成初始化分段
    Buffer create_init_segment();

    // 封装媒体帧为分段
    Buffer mux_segment(const std::vector<MediaFramePtr>& frames, double duration);

private:
    // Box 生成
    Buffer create_ftyp_box();
    Buffer create_moov_box();
    Buffer create_mvhd_box();
    Buffer create_trak_box(MediaType type);
    Buffer create_tkhd_box(MediaType type);
    Buffer create_mdia_box(MediaType type);
    Buffer create_mdhd_box(MediaType type);
    Buffer create_hdlr_box(MediaType type);
    Buffer create_minf_box(MediaType type);
    Buffer create_stbl_box(MediaType type);
    Buffer create_mvex_box();
    Buffer create_moof_box(uint32_t sequence_number, double duration);
    Buffer create_mfhd_box(uint32_t sequence_number);
    Buffer create_traf_box(MediaType type, uint32_t sequence_number, double duration);
    Buffer create_tfhd_box(MediaType type);
    Buffer create_tfdt_box(double duration);
    Buffer create_trun_box(const std::vector<MediaFramePtr>& frames, MediaType type);
    Buffer create_mdat_box(const std::vector<MediaFramePtr>& frames);

    // 辅助函数
    Buffer uint32_to_bytes(uint32_t value);
    Buffer uint64_to_bytes(uint64_t value);
    void write_box_header(Buffer& buffer, uint32_t size, const char* type);

    MediaParams params_;
    bool initialized_ = false;
    uint32_t sequence_number_ = 1;
    uint32_t timescale_ = 90000;
};

/**
 * @brief DASH 分段器
 */
class DashSegmenter {
public:
    DashSegmenter();
    ~DashSegmenter();

    // 配置
    void set_segment_duration(double duration) { segment_duration_ = duration; }
    void set_segment_count(uint32_t count) { max_segments_ = count; }

    // 初始化
    bool initialize(const MediaParams& params);
    void close();

    // 处理媒体帧
    void process_frame(const MediaFrame& frame);

    // 获取分段
    std::vector<DashSegmentPtr> get_segments() const;
    Buffer get_init_segment() const;

    // 回调
    using SegmentCallback = std::function<void(DashSegmentPtr)>;
    void set_segment_callback(SegmentCallback callback) { segment_callback_ = std::move(callback); }

private:
    void start_new_segment();
    void finish_current_segment();

    double segment_duration_ = 4.0;
    uint32_t max_segments_ = 5;

    std::unique_ptr<Fmp4Muxer> muxer_;
    std::vector<DashSegmentPtr> segments_;
    std::vector<MediaFramePtr> current_frames_;
    uint32_t next_sequence_number_ = 0;

    SegmentCallback segment_callback_;
    mutable std::mutex mutex_;
};

/**
 * @brief MPD 生成器
 */
class MpdGenerator {
public:
    /**
     * @brief 生成 MPD 文档
     * @param mpd MPD 信息
     * @return MPD XML 内容
     */
    static std::string generate(const DashMpd& mpd);

private:
    static std::string generate_period(const DashPeriod& period);
    static std::string generate_adaptation_set(const DashAdaptationSet& adaptation_set);
    static std::string generate_representation(const DashRepresentation& representation);
    static std::string get_mime_type(DashRepresentationType type, const std::string& codecs);
};

/**
 * @brief DASH 服务器
 */
class DashServer {
public:
    DashServer();
    ~DashServer();

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
    void handle_mpd_request(int client_fd, const std::string& stream_name);
    void handle_init_segment_request(int client_fd, const std::string& stream_name,
                                     const std::string& representation_id);
    void handle_segment_request(int client_fd, const std::string& stream_name,
                                const std::string& representation_id,
                                uint32_t segment_number);

    // HTTP 响应
    void send_http_response(int client_fd, int status_code,
                           const std::string& content_type, const std::string& body);
    void send_http_error(int client_fd, int status_code, const std::string& message);

    // 流信息
    struct StreamInfo {
        MediaParams params;
        std::unique_ptr<DashSegmenter> video_segmenter;
        std::unique_ptr<DashSegmenter> audio_segmenter;
        DashMpd mpd;
        uint32_t viewer_count = 0;
    };

    std::string host_;
    uint16_t port_ = 8080;
    int listen_fd_ = -1;
    std::atomic<bool> running_{false};

    double segment_duration_ = 4.0;
    uint32_t segment_count_ = 5;
    std::string output_path_ = "./dash";

    std::thread http_thread_;
    std::unordered_map<std::string, std::unique_ptr<StreamInfo>> streams_;
    mutable std::mutex streams_mutex_;
};

} // namespace streaming
