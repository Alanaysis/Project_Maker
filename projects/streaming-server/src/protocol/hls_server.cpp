/**
 * @file hls_server.cpp
 * @brief HLS 服务器实现
 */

#include "streaming/protocol/hls_server.hpp"
#include "streaming/monitor/logger.hpp"

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>
#include <sstream>
#include <iomanip>
#include <filesystem>

namespace streaming {

// ============================================================================
// TS 封装器实现
// ============================================================================

TsMuxer::TsMuxer() = default;
TsMuxer::~TsMuxer() { close(); }

bool TsMuxer::initialize(const MediaParams& params) {
    params_ = params;
    initialized_ = true;
    return true;
}

void TsMuxer::close() {
    initialized_ = false;
}

Buffer TsMuxer::mux_frame(const MediaFrame& frame) {
    if (!initialized_) return {};

    Buffer result;
    auto pes = create_pes_packet(frame);

    // 分割成 188 字节的 TS 包
    uint16_t pid = (frame.media_type == MediaType::Video) ? video_pid_ : audio_pid_;
    uint8_t& cc = (frame.media_type == MediaType::Video) ? video_cc_ : audio_cc_;

    size_t offset = 0;
    bool first = true;

    while (offset < pes.size()) {
        size_t payload_size = std::min(static_cast<size_t>(184), pes.size() - offset);
        Buffer payload(pes.begin() + offset, pes.begin() + offset + payload_size);

        auto packet = create_ts_packet(pid, first, cc, payload);
        result.insert(result.end(), packet.begin(), packet.end());

        cc = (cc + 1) & 0x0F;
        offset += payload_size;
        first = false;
    }

    return result;
}

Buffer TsMuxer::create_ts_packet(uint16_t pid, bool payload_unit_start,
                                  uint8_t continuity_counter, const Buffer& payload) {
    Buffer packet(188, 0xFF);

    // 同步字节
    packet[0] = 0x47;

    // PID 和标志
    packet[1] = (payload_unit_start ? 0x40 : 0x00) | ((pid >> 8) & 0x1F);
    packet[2] = pid & 0xFF;

    // 适应场控制和计数器
    packet[3] = 0x10 | (continuity_counter & 0x0F);

    // 负载
    size_t copy_size = std::min(payload.size(), static_cast<size_t>(184));
    std::memcpy(packet.data() + 4, payload.data(), copy_size);

    return packet;
}

Buffer TsMuxer::create_pes_packet(const MediaFrame& frame) {
    Buffer pes;

    // PES 开始码
    pes.push_back(0x00);
    pes.push_back(0x00);
    pes.push_back(0x01);

    // 流类型
    if (frame.media_type == MediaType::Video) {
        pes.push_back(0xE0); // 视频流
    } else {
        pes.push_back(0xC0); // 音频流
    }

    // PES 长度
    uint16_t pes_length = static_cast<uint16_t>(frame.data.size() + 8);
    pes.push_back((pes_length >> 8) & 0xFF);
    pes.push_back(pes_length & 0xFF);

    // 标志
    pes.push_back(0x80); // 固定标志
    pes.push_back(0x80); // PTS 标志

    // PTS
    pes.push_back(0x05); // PTS 长度
    uint64_t pts = static_cast<uint64_t>(frame.pts);
    pes.push_back(0x21 | ((pts >> 29) & 0x0E));
    pes.push_back((pts >> 22) & 0xFF);
    pes.push_back(0x01 | ((pts >> 14) & 0xFE));
    pes.push_back((pts >> 7) & 0xFF);
    pes.push_back(0x01 | ((pts << 1) & 0xFE));

    // 负载
    pes.insert(pes.end(), frame.data.begin(), frame.data.end());

    return pes;
}

Buffer TsMuxer::get_pat() {
    Buffer pat;

    // PAT 包
    pat.push_back(0x47);
    pat.push_back(0x40); // 起始
    pat.push_back(0x00); // PID 0
    pat.push_back(0x10);
    pat.push_back(0x00); // 指针

    // 表头
    pat.push_back(0x00); // 表类型
    pat.push_back(0xB0);
    pat.push_back(0x0D); // 表长度
    pat.push_back(0x00);
    pat.push_back(0x01); // 传输流ID
    pat.push_back(0xC1);
    pat.push_back(0x00);
    pat.push_back(0x00);
    pat.push_back(0x00);
    pat.push_back(0x00);
    pat.push_back(0xE0);
    pat.push_back(0x10); // PMT PID
    pat.push_back(0x00);

    // CRC32 (简化)
    pat.push_back(0x00);
    pat.push_back(0x00);
    pat.push_back(0x00);
    pat.push_back(0x00);

    // 填充到 188 字节
    pat.resize(188, 0xFF);

    return pat;
}

Buffer TsMuxer::get_pmt() {
    Buffer pmt;

    // PMT 包
    pmt.push_back(0x47);
    pmt.push_back(0x40 | ((pmt_pid_ >> 8) & 0x1F));
    pmt.push_back(pmt_pid_ & 0xFF);
    pmt.push_back(0x10);
    pmt.push_back(0x00);

    // 表头
    pmt.push_back(0x02); // 表类型
    pmt.push_back(0xB0);
    pmt.push_back(0x17); // 表长度
    pmt.push_back(0x00);
    pmt.push_back(0x01); // 服务ID
    pmt.push_back(0xC1);
    pmt.push_back(0x00);
    pmt.push_back(0x00);
    pmt.push_back(0xE0 | ((video_pid_ >> 8) & 0x1F));
    pmt.push_back(video_pid_ & 0xFF);
    pmt.push_back(0xF0);

    // 视频流描述
    pmt.push_back(0x1B); // H.264
    pmt.push_back(0xE0 | ((video_pid_ >> 8) & 0x1F));
    pmt.push_back(video_pid_ & 0xFF);
    pmt.push_back(0xF0);

    // 音频流描述
    pmt.push_back(0x0F); // AAC
    pmt.push_back(0xE0 | ((audio_pid_ >> 8) & 0x1F));
    pmt.push_back(audio_pid_ & 0xFF);
    pmt.push_back(0xF0);

    // CRC32 (简化)
    pmt.push_back(0x00);
    pmt.push_back(0x00);
    pmt.push_back(0x00);
    pmt.push_back(0x00);

    // 填充到 188 字节
    pmt.resize(188, 0xFF);

    return pmt;
}

// ============================================================================
// HLS 切片器实现
// ============================================================================

HlsSegmenter::HlsSegmenter() = default;
HlsSegmenter::~HlsSegmenter() { close(); }

bool HlsSegmenter::initialize(const MediaParams& params) {
    muxer_ = std::make_unique<TsMuxer>();
    if (!muxer_->initialize(params)) {
        LOG_ERROR("Failed to initialize TS muxer");
        return false;
    }

    start_new_segment();
    return true;
}

void HlsSegmenter::close() {
    if (current_segment_) {
        finish_current_segment();
    }
    if (muxer_) {
        muxer_->close();
    }
}

void HlsSegmenter::process_frame(const MediaFrame& frame) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (!muxer_) return;

    // 检查是否需要开始新切片
    if (should_start_new_segment(frame)) {
        finish_current_segment();
        start_new_segment();
    }

    // 封装帧
    auto ts_data = muxer_->mux_frame(frame);
    current_segment_data_.insert(current_segment_data_.end(), ts_data.begin(), ts_data.end());

    // 更新时长
    if (segment_start_pts_ < 0) {
        segment_start_pts_ = frame.pts;
    }
    current_segment_duration_ = (frame.pts - segment_start_pts_) / 90000.0;
}

bool HlsSegmenter::should_start_new_segment(const MediaFrame& frame) const {
    if (!current_segment_) return false;

    // 基于时长判断
    if (current_segment_duration_ >= target_duration_ && frame.is_keyframe) {
        return true;
    }

    return false;
}

void HlsSegmenter::start_new_segment() {
    current_segment_ = std::make_shared<HlsSegment>();
    current_segment_->sequence_number = next_sequence_number_++;
    current_segment_->start_time = std::chrono::steady_clock::now();
    current_segment_data_.clear();
    current_segment_duration_ = 0.0;
    segment_start_pts_ = -1;

    // 添加 PAT/PMT
    auto pat = muxer_->get_pat();
    auto pmt = muxer_->get_pmt();
    current_segment_data_.insert(current_segment_data_.end(), pat.begin(), pat.end());
    current_segment_data_.insert(current_segment_data_.end(), pmt.begin(), pmt.end());
}

void HlsSegmenter::finish_current_segment() {
    if (!current_segment_) return;

    current_segment_->data = std::move(current_segment_data_);
    current_segment_->size = current_segment_->data.size();
    current_segment_->duration = current_segment_duration_;
    current_segment_->end_time = std::chrono::steady_clock::now();

    segments_.push_back(current_segment_);

    // 限制切片数量
    while (segments_.size() > max_segments_) {
        segments_.erase(segments_.begin());
    }

    // 回调通知
    if (segment_callback_) {
        segment_callback_(current_segment_);
    }

    current_segment_.reset();
}

std::vector<HlsSegmentPtr> HlsSegmenter::get_segments() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return segments_;
}

HlsSegmentPtr HlsSegmenter::get_latest_segment() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return segments_.empty() ? nullptr : segments_.back();
}

// ============================================================================
// M3U8 生成器实现
// ============================================================================

std::string M3u8Generator::generate_media_playlist(const HlsPlaylist& playlist) {
    std::ostringstream ss;

    ss << "#EXTM3U\n";
    ss << "#EXT-X-VERSION:" << playlist.version << "\n";
    ss << "#EXT-X-TARGETDURATION:" << playlist.target_duration << "\n";
    ss << "#EXT-X-MEDIA-SEQUENCE:" << playlist.media_sequence << "\n";

    if (!playlist.allow_cache) {
        ss << "#EXT-X-ALLOW-CACHE:NO\n";
    }

    if (playlist.type == HlsPlaylistType::VOD) {
        ss << "#EXT-X-PLAYLIST-TYPE:VOD\n";
    }

    // 加密信息
    if (playlist.encryption != HlsEncryptionMethod::None) {
        ss << get_encryption_tag(playlist);
    }

    // 切片列表
    for (const auto& segment : playlist.segments) {
        ss << "#EXTINF:" << std::fixed << std::setprecision(3) << segment->duration << ",\n";
        ss << segment->filename << "\n";
    }

    if (playlist.type == HlsPlaylistType::VOD) {
        ss << "#EXT-X-ENDLIST\n";
    }

    return ss.str();
}

std::string M3u8Generator::generate_master_playlist(const std::vector<HlsVariantStream>& variants) {
    std::ostringstream ss;

    ss << "#EXTM3U\n";
    ss << "#EXT-X-VERSION:3\n";

    for (const auto& variant : variants) {
        ss << "#EXT-X-STREAM-INF:BANDWIDTH=" << variant.bandwidth;
        if (variant.width > 0 && variant.height > 0) {
            ss << ",RESOLUTION=" << variant.width << "x" << variant.height;
        }
        if (!variant.codecs.empty()) {
            ss << ",CODECS=\"" << variant.codecs << "\"";
        }
        ss << "\n";
        ss << variant.playlist_url << "\n";
    }

    return ss.str();
}

std::string M3u8Generator::get_encryption_tag(const HlsPlaylist& playlist) {
    std::ostringstream ss;

    switch (playlist.encryption) {
        case HlsEncryptionMethod::AES_128:
            ss << "#EXT-X-KEY:METHOD=AES-128";
            break;
        case HlsEncryptionMethod::SampleAES:
            ss << "#EXT-X-KEY:METHOD=SAMPLE-AES";
            break;
        default:
            return "";
    }

    ss << ",URI=\"" << playlist.encryption_key_uri << "\"";
    if (!playlist.encryption_iv.empty()) {
        ss << ",IV=" << playlist.encryption_iv;
    }
    ss << "\n";

    return ss.str();
}

// ============================================================================
// HLS 服务器实现
// ============================================================================

HlsServer::HlsServer() = default;
HlsServer::~HlsServer() { stop(); }

bool HlsServer::start(const std::string& host, uint16_t port) {
    host_ = host;
    port_ = port;

    // 创建输出目录
    std::filesystem::create_directories(output_path_);

    // 创建 socket
    listen_fd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd_ < 0) {
        LOG_ERROR("Failed to create HLS socket");
        return false;
    }

    int opt = 1;
    setsockopt(listen_fd_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr;
    std::memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);

    if (host == "0.0.0.0") {
        addr.sin_addr.s_addr = INADDR_ANY;
    } else {
        inet_pton(AF_INET, host.c_str(), &addr.sin_addr);
    }

    if (bind(listen_fd_, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        LOG_ERROR("Failed to bind HLS socket");
        ::close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    if (listen(listen_fd_, 128) < 0) {
        LOG_ERROR("Failed to listen on HLS socket");
        ::close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    running_ = true;
    http_thread_ = std::thread(&HlsServer::http_loop, this);

    LOG_INFO("HLS server started on " + host + ":" + std::to_string(port));
    return true;
}

void HlsServer::stop() {
    running_ = false;

    if (listen_fd_ >= 0) {
        ::close(listen_fd_);
        listen_fd_ = -1;
    }

    if (http_thread_.joinable()) {
        http_thread_.join();
    }

    std::lock_guard<std::mutex> lock(streams_mutex_);
    streams_.clear();

    LOG_INFO("HLS server stopped");
}

void HlsServer::add_stream(const std::string& stream_name, const MediaParams& params) {
    std::lock_guard<std::mutex> lock(streams_mutex_);

    auto info = std::make_unique<StreamInfo>();
    info->params = params;

    info->segmenter = std::make_unique<HlsSegmenter>();
    info->segmenter->set_target_duration(segment_duration_);
    info->segmenter->set_segment_count(segment_count_);
    info->segmenter->set_output_path(output_path_ + "/" + stream_name);
    info->segmenter->set_segment_callback([this, stream_name](HlsSegmentPtr segment) {
        std::lock_guard<std::mutex> lock(streams_mutex_);
        auto it = streams_.find(stream_name);
        if (it != streams_.end()) {
            it->second->playlist.segments.push_back(segment);
            while (it->second->playlist.segments.size() > segment_count_) {
                it->second->playlist.segments.erase(it->second->playlist.segments.begin());
            }
            it->second->playlist.target_duration = static_cast<uint32_t>(segment_duration_);
        }
    });
    info->segmenter->initialize(params);

    info->playlist.type = HlsPlaylistType::Live;
    info->playlist.version = 3;
    info->playlist.allow_cache = false;

    streams_[stream_name] = std::move(info);
    LOG_INFO("HLS stream added: " + stream_name);
}

void HlsServer::remove_stream(const std::string& stream_name) {
    std::lock_guard<std::mutex> lock(streams_mutex_);
    streams_.erase(stream_name);
    LOG_INFO("HLS stream removed: " + stream_name);
}

void HlsServer::push_frame(const std::string& stream_name, const MediaFrame& frame) {
    std::lock_guard<std::mutex> lock(streams_mutex_);
    auto it = streams_.find(stream_name);
    if (it != streams_.end() && it->second->segmenter) {
        it->second->segmenter->process_frame(frame);
    }
}

uint32_t HlsServer::get_viewer_count(const std::string& stream_name) const {
    std::lock_guard<std::mutex> lock(streams_mutex_);
    auto it = streams_.find(stream_name);
    return (it != streams_.end()) ? it->second->viewer_count : 0;
}

void HlsServer::http_loop() {
    while (running_) {
        struct sockaddr_in client_addr;
        socklen_t addr_len = sizeof(client_addr);

        int client_fd = accept(listen_fd_, (struct sockaddr*)&client_addr, &addr_len);
        if (client_fd < 0) {
            if (running_) {
                LOG_ERROR("Failed to accept HLS connection");
            }
            continue;
        }

        // 接收请求
        char buffer[4096];
        ssize_t n = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
        if (n > 0) {
            buffer[n] = '\0';
            handle_http_request(client_fd, std::string(buffer, n));
        }

        ::close(client_fd);
    }
}

void HlsServer::handle_http_request(int client_fd, const std::string& request) {
    // 解析请求行
    std::istringstream iss(request);
    std::string method, path, version;
    iss >> method >> path >> version;

    if (method != "GET") {
        send_http_error(client_fd, 405, "Method Not Allowed");
        return;
    }

    // 解析路径
    // 格式: /{stream_name}/playlist.m3u8 或 /{stream_name}/{segment}.ts
    if (path.find(".m3u8") != std::string::npos) {
        // 播放列表请求
        size_t start = path.find('/') + 1;
        size_t end = path.find('/', start);
        std::string stream_name = path.substr(start, end - start);
        handle_playlist_request(client_fd, stream_name);
    } else if (path.find(".ts") != std::string::npos) {
        // 切片请求
        size_t start = path.find('/') + 1;
        size_t end = path.find('/', start);
        std::string stream_name = path.substr(start, end - start);
        std::string segment_name = path.substr(end + 1);
        handle_segment_request(client_fd, stream_name, segment_name);
    } else if (path == "/" || path == "/index.m3u8") {
        // 主播放列表
        handle_master_playlist_request(client_fd);
    } else {
        send_http_error(client_fd, 404, "Not Found");
    }
}

void HlsServer::handle_playlist_request(int client_fd, const std::string& stream_name) {
    std::lock_guard<std::mutex> lock(streams_mutex_);
    auto it = streams_.find(stream_name);
    if (it == streams_.end()) {
        send_http_error(client_fd, 404, "Stream not found");
        return;
    }

    // 更新观看者计数
    it->second->viewer_count++;

    // 生成 M3U8
    std::string m3u8 = M3u8Generator::generate_media_playlist(it->second->playlist);
    send_http_response(client_fd, 200, "application/vnd.apple.mpegurl", m3u8);
}

void HlsServer::handle_segment_request(int client_fd, const std::string& stream_name,
                                        const std::string& segment_name) {
    std::lock_guard<std::mutex> lock(streams_mutex_);
    auto it = streams_.find(stream_name);
    if (it == streams_.end()) {
        send_http_error(client_fd, 404, "Stream not found");
        return;
    }

    // 查找切片
    for (const auto& segment : it->second->playlist.segments) {
        if (segment->filename == segment_name) {
            send_http_response(client_fd, 200, "video/MP2T",
                             std::string(segment->data.begin(), segment->data.end()));
            return;
        }
    }

    send_http_error(client_fd, 404, "Segment not found");
}

void HlsServer::handle_master_playlist_request(int client_fd) {
    std::lock_guard<std::mutex> lock(streams_mutex_);

    std::vector<HlsVariantStream> variants;
    for (const auto& [name, info] : streams_) {
        HlsVariantStream variant;
        variant.bandwidth = info->params.video.bitrate;
        variant.width = info->params.video.width;
        variant.height = info->params.video.height;
        variant.playlist_url = "/" + name + "/playlist.m3u8";
        variants.push_back(variant);
    }

    std::string m3u8 = M3u8Generator::generate_master_playlist(variants);
    send_http_response(client_fd, 200, "application/vnd.apple.mpegurl", m3u8);
}

void HlsServer::send_http_response(int client_fd, int status_code,
                                    const std::string& content_type, const std::string& body) {
    std::ostringstream ss;
    ss << "HTTP/1.1 " << status_code << " ";
    switch (status_code) {
        case 200: ss << "OK"; break;
        case 404: ss << "Not Found"; break;
        case 405: ss << "Method Not Allowed"; break;
        default: ss << "Error"; break;
    }
    ss << "\r\n";
    ss << "Content-Type: " << content_type << "\r\n";
    ss << "Content-Length: " << body.size() << "\r\n";
    ss << "Access-Control-Allow-Origin: *\r\n";
    ss << "Cache-Control: no-cache\r\n";
    ss << "\r\n";
    ss << body;

    std::string response = ss.str();
    ::send(client_fd, response.c_str(), response.size(), 0);
}

void HlsServer::send_http_error(int client_fd, int status_code, const std::string& message) {
    std::string body = "<html><body><h1>" + std::to_string(status_code) + "</h1><p>" + message + "</p></body></html>";
    send_http_response(client_fd, status_code, "text/html", body);
}

} // namespace streaming
