/**
 * @file dash_server.cpp
 * @brief DASH 服务器实现
 */

#include "streaming/protocol/dash_server.hpp"
#include "streaming/monitor/logger.hpp"

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>
#include <sstream>
#include <iomanip>

namespace streaming {

// ============================================================================
// fMP4 封装器实现（简化）
// ============================================================================

Fmp4Muxer::Fmp4Muxer() = default;
Fmp4Muxer::~Fmp4Muxer() { close(); }

bool Fmp4Muxer::initialize(const MediaParams& params) {
    params_ = params;
    initialized_ = true;
    return true;
}

void Fmp4Muxer::close() {
    initialized_ = false;
}

Buffer Fmp4Muxer::create_init_segment() {
    Buffer result;

    // ftyp box
    auto ftyp = create_ftyp_box();
    result.insert(result.end(), ftyp.begin(), ftyp.end());

    // moov box
    auto moov = create_moov_box();
    result.insert(result.end(), moov.begin(), moov.end());

    return result;
}

Buffer Fmp4Muxer::mux_segment(const std::vector<MediaFramePtr>& frames, double duration) {
    if (!initialized_ || frames.empty()) return {};

    Buffer result;

    // moof box
    auto moof = create_moof_box(sequence_number_, duration);
    result.insert(result.end(), moof.begin(), moof.end());

    // mdat box
    auto mdat = create_mdat_box(frames);
    result.insert(result.end(), mdat.begin(), mdat.end());

    sequence_number_++;
    return result;
}

Buffer Fmp4Muxer::create_ftyp_box() {
    Buffer box;
    write_box_header(box, 24, "ftyp");
    box.insert(box.end(), {'i', 's', 'o', 'm'});   // major brand
    box.insert(box.end(), {0, 0, 0, 0});            // minor version
    box.insert(box.end(), {'i', 's', 'o', 'm'});   // compatible brands
    return box;
}

Buffer Fmp4Muxer::create_moov_box() {
    Buffer box;
    write_box_header(box, 8, "moov");
    return box;
}

Buffer Fmp4Muxer::create_moof_box(uint32_t sequence_number, double duration) {
    Buffer box;
    write_box_header(box, 16, "moof");

    // mfhd
    auto mfhd = create_mfhd_box(sequence_number);
    box.insert(box.end(), mfhd.begin(), mfhd.end());

    return box;
}

Buffer Fmp4Muxer::create_mfhd_box(uint32_t sequence_number) {
    Buffer box;
    write_box_header(box, 16, "mfhd");
    auto bytes = uint32_to_bytes(sequence_number);
    box.insert(box.end(), bytes.begin(), bytes.end());
    return box;
}

Buffer Fmp4Muxer::create_mdat_box(const std::vector<MediaFramePtr>& frames) {
    Buffer box;

    uint64_t total_size = 8;
    for (const auto& frame : frames) {
        total_size += frame->data.size();
    }

    // 使用 large size
    box.push_back(0x00);
    box.insert(box.end(), {'m', 'd', 'a', 't'});
    auto size_bytes = uint64_to_bytes(total_size);
    box.insert(box.end(), size_bytes.begin(), size_bytes.end());

    for (const auto& frame : frames) {
        box.insert(box.end(), frame->data.begin(), frame->data.end());
    }

    return box;
}

void Fmp4Muxer::write_box_header(Buffer& buffer, uint32_t size, const char* type) {
    auto size_bytes = uint32_to_bytes(size);
    buffer.insert(buffer.end(), size_bytes.begin(), size_bytes.end());
    buffer.insert(buffer.end(), type, type + 4);
}

Buffer Fmp4Muxer::uint32_to_bytes(uint32_t value) {
    return {
        static_cast<uint8_t>((value >> 24) & 0xFF),
        static_cast<uint8_t>((value >> 16) & 0xFF),
        static_cast<uint8_t>((value >> 8) & 0xFF),
        static_cast<uint8_t>(value & 0xFF)
    };
}

Buffer Fmp4Muxer::uint64_to_bytes(uint64_t value) {
    return {
        static_cast<uint8_t>((value >> 56) & 0xFF),
        static_cast<uint8_t>((value >> 48) & 0xFF),
        static_cast<uint8_t>((value >> 40) & 0xFF),
        static_cast<uint8_t>((value >> 32) & 0xFF),
        static_cast<uint8_t>((value >> 24) & 0xFF),
        static_cast<uint8_t>((value >> 16) & 0xFF),
        static_cast<uint8_t>((value >> 8) & 0xFF),
        static_cast<uint8_t>(value & 0xFF)
    };
}

// 其他 box 创建函数的简化实现
Buffer Fmp4Muxer::create_mvhd_box() { return {}; }
Buffer Fmp4Muxer::create_trak_box(MediaType type) { return {}; }
Buffer Fmp4Muxer::create_tkhd_box(MediaType type) { return {}; }
Buffer Fmp4Muxer::create_mdia_box(MediaType type) { return {}; }
Buffer Fmp4Muxer::create_mdhd_box(MediaType type) { return {}; }
Buffer Fmp4Muxer::create_hdlr_box(MediaType type) { return {}; }
Buffer Fmp4Muxer::create_minf_box(MediaType type) { return {}; }
Buffer Fmp4Muxer::create_stbl_box(MediaType type) { return {}; }
Buffer Fmp4Muxer::create_mvex_box() { return {}; }
Buffer Fmp4Muxer::create_traf_box(MediaType type, uint32_t seq, double dur) { return {}; }
Buffer Fmp4Muxer::create_tfhd_box(MediaType type) { return {}; }
Buffer Fmp4Muxer::create_tfdt_box(double duration) { return {}; }
Buffer Fmp4Muxer::create_trun_box(const std::vector<MediaFramePtr>& frames, MediaType type) { return {}; }

// ============================================================================
// DASH 分段器实现
// ============================================================================

DashSegmenter::DashSegmenter() = default;
DashSegmenter::~DashSegmenter() { close(); }

bool DashSegmenter::initialize(const MediaParams& params) {
    muxer_ = std::make_unique<Fmp4Muxer>();
    if (!muxer_->initialize(params)) {
        LOG_ERROR("Failed to initialize fMP4 muxer");
        return false;
    }
    return true;
}

void DashSegmenter::close() {
    if (muxer_) {
        muxer_->close();
    }
}

void DashSegmenter::process_frame(const MediaFrame& frame) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto frame_ptr = std::make_shared<MediaFrame>(frame);
    current_frames_.push_back(frame_ptr);

    // 检查是否需要完成当前分段
    if (current_frames_.size() >= 100) {  // 简化的分段条件
        finish_current_segment();
        start_new_segment();
    }
}

void DashSegmenter::start_new_segment() {
    current_frames_.clear();
}

void DashSegmenter::finish_current_segment() {
    if (current_frames_.empty() || !muxer_) return;

    auto segment_data = muxer_->mux_segment(current_frames_, segment_duration_);

    auto segment = std::make_shared<DashSegment>();
    segment->sequence_number = next_sequence_number_++;
    segment->data = segment_data;
    segment->size = segment_data.size();
    segment->duration = segment_duration_;
    segment->filename = "segment_" + std::to_string(segment->sequence_number) + ".m4s";

    segments_.push_back(segment);

    while (segments_.size() > max_segments_) {
        segments_.erase(segments_.begin());
    }

    if (segment_callback_) {
        segment_callback_(segment);
    }
}

std::vector<DashSegmentPtr> DashSegmenter::get_segments() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return segments_;
}

Buffer DashSegmenter::get_init_segment() const {
    if (!muxer_) return {};
    return muxer_->create_init_segment();
}

// ============================================================================
// MPD 生成器实现
// ============================================================================

std::string MpdGenerator::generate(const DashMpd& mpd) {
    std::ostringstream xml;

    xml << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
    xml << "<MPD xmlns=\"urn:mpeg:dash:schema:mpd:2011\"\n";
    xml << "     type=\"" << mpd.type << "\"\n";
    xml << "     minBufferTime=\"PT" << mpd.min_buffer_time << "S\"\n";
    xml << "     minUpdatePeriod=\"PT" << mpd.min_update_period << "S\"\n";
    xml << "     suggestedPresentationDelay=\"PT" << mpd.suggested_presentation_delay << "S\">\n";

    for (const auto& period : mpd.periods) {
        xml << generate_period(period);
    }

    xml << "</MPD>\n";
    return xml.str();
}

std::string MpdGenerator::generate_period(const DashPeriod& period) {
    std::ostringstream xml;

    xml << "  <Period id=\"" << period.id << "\"";
    if (period.start > 0) {
        xml << " start=\"PT" << period.start << "S\"";
    }
    xml << ">\n";

    for (const auto& as : period.adaptation_sets) {
        xml << generate_adaptation_set(as);
    }

    xml << "  </Period>\n";
    return xml.str();
}

std::string MpdGenerator::generate_adaptation_set(const DashAdaptationSet& adaptation_set) {
    std::ostringstream xml;

    xml << "    <AdaptationSet id=\"" << adaptation_set.id << "\"";
    xml << " mimeType=\"" << get_mime_type(adaptation_set.type, "") << "\"";
    xml << ">\n";

    for (const auto& rep : adaptation_set.representations) {
        xml << generate_representation(rep);
    }

    xml << "    </AdaptationSet>\n";
    return xml.str();
}

std::string MpdGenerator::generate_representation(const DashRepresentation& representation) {
    std::ostringstream xml;

    xml << "      <Representation id=\"" << representation.id << "\"";
    xml << " bandwidth=\"" << representation.bandwidth << "\"";
    if (representation.width > 0 && representation.height > 0) {
        xml << " width=\"" << representation.width << "\"";
        xml << " height=\"" << representation.height << "\"";
    }
    xml << ">\n";
    xml << "      </Representation>\n";

    return xml.str();
}

std::string MpdGenerator::get_mime_type(DashRepresentationType type, const std::string& codecs) {
    switch (type) {
        case DashRepresentationType::Video: return "video/mp4";
        case DashRepresentationType::Audio: return "audio/mp4";
        default: return "application/octet-stream";
    }
}

// ============================================================================
// DASH 服务器实现
// ============================================================================

DashServer::DashServer() = default;
DashServer::~DashServer() { stop(); }

bool DashServer::start(const std::string& host, uint16_t port) {
    host_ = host;
    port_ = port;

    listen_fd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd_ < 0) {
        LOG_ERROR("Failed to create DASH socket");
        return false;
    }

    int opt = 1;
    setsockopt(listen_fd_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr;
    std::memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(listen_fd_, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        LOG_ERROR("Failed to bind DASH socket");
        ::close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    if (listen(listen_fd_, 128) < 0) {
        LOG_ERROR("Failed to listen on DASH socket");
        ::close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    running_ = true;
    http_thread_ = std::thread(&DashServer::http_loop, this);

    LOG_INFO("DASH server started on " + host + ":" + std::to_string(port));
    return true;
}

void DashServer::stop() {
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

    LOG_INFO("DASH server stopped");
}

void DashServer::add_stream(const std::string& stream_name, const MediaParams& params) {
    std::lock_guard<std::mutex> lock(streams_mutex_);

    auto info = std::make_unique<StreamInfo>();
    info->params = params;
    info->video_segmenter = std::make_unique<DashSegmenter>();
    info->video_segmenter->set_segment_duration(segment_duration_);
    info->video_segmenter->set_segment_count(segment_count_);
    info->video_segmenter->initialize(params);

    streams_[stream_name] = std::move(info);
    LOG_INFO("DASH stream added: " + stream_name);
}

void DashServer::remove_stream(const std::string& stream_name) {
    std::lock_guard<std::mutex> lock(streams_mutex_);
    streams_.erase(stream_name);
    LOG_INFO("DASH stream removed: " + stream_name);
}

void DashServer::push_frame(const std::string& stream_name, const MediaFrame& frame) {
    std::lock_guard<std::mutex> lock(streams_mutex_);
    auto it = streams_.find(stream_name);
    if (it != streams_.end()) {
        if (frame.media_type == MediaType::Video && it->second->video_segmenter) {
            it->second->video_segmenter->process_frame(frame);
        }
    }
}

uint32_t DashServer::get_viewer_count(const std::string& stream_name) const {
    std::lock_guard<std::mutex> lock(streams_mutex_);
    auto it = streams_.find(stream_name);
    return (it != streams_.end()) ? it->second->viewer_count : 0;
}

void DashServer::http_loop() {
    while (running_) {
        struct sockaddr_in client_addr;
        socklen_t addr_len = sizeof(client_addr);

        int client_fd = accept(listen_fd_, (struct sockaddr*)&client_addr, &addr_len);
        if (client_fd < 0) {
            if (running_) {
                LOG_ERROR("Failed to accept DASH connection");
            }
            continue;
        }

        char buffer[4096];
        ssize_t n = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
        if (n > 0) {
            buffer[n] = '\0';
            handle_http_request(client_fd, std::string(buffer, n));
        }

        ::close(client_fd);
    }
}

void DashServer::handle_http_request(int client_fd, const std::string& request) {
    std::istringstream iss(request);
    std::string method, path, version;
    iss >> method >> path >> version;

    if (method != "GET") {
        send_http_error(client_fd, 405, "Method Not Allowed");
        return;
    }

    // 路由请求
    if (path.find(".mpd") != std::string::npos) {
        size_t start = path.find('/') + 1;
        size_t end = path.find('/', start);
        std::string stream_name = path.substr(start, end - start);
        handle_mpd_request(client_fd, stream_name);
    } else if (path.find("init.mp4") != std::string::npos) {
        // 初始化分段
        send_http_error(client_fd, 200, "OK");
    } else if (path.find(".m4s") != std::string::npos) {
        // 媒体分段
        send_http_error(client_fd, 200, "OK");
    } else {
        send_http_error(client_fd, 404, "Not Found");
    }
}

void DashServer::handle_mpd_request(int client_fd, const std::string& stream_name) {
    std::lock_guard<std::mutex> lock(streams_mutex_);
    auto it = streams_.find(stream_name);
    if (it == streams_.end()) {
        send_http_error(client_fd, 404, "Stream not found");
        return;
    }

    DashMpd mpd;
    mpd.type = "dynamic";
    mpd.min_buffer_time = 1.0;

    DashPeriod period;
    period.id = "0";

    // 简化实现
    DashAdaptationSet video_as;
    video_as.id = "0";
    video_as.type = DashRepresentationType::Video;

    DashRepresentation rep;
    rep.id = "video_0";
    rep.bandwidth = 2000000;
    rep.width = 1280;
    rep.height = 720;
    video_as.representations.push_back(rep);

    period.adaptation_sets.push_back(video_as);
    mpd.periods.push_back(period);

    std::string mpd_content = MpdGenerator::generate(mpd);
    send_http_response(client_fd, 200, "application/dash+xml", mpd_content);

    it->second->viewer_count++;
}

void DashServer::handle_init_segment_request(int client_fd, const std::string& stream_name,
                                              const std::string& representation_id) {
    // 简化实现
    send_http_error(client_fd, 200, "OK");
}

void DashServer::handle_segment_request(int client_fd, const std::string& stream_name,
                                         const std::string& representation_id,
                                         uint32_t segment_number) {
    // 简化实现
    send_http_error(client_fd, 200, "OK");
}

void DashServer::send_http_response(int client_fd, int status_code,
                                     const std::string& content_type, const std::string& body) {
    std::ostringstream ss;
    ss << "HTTP/1.1 " << status_code << " OK\r\n";
    ss << "Content-Type: " << content_type << "\r\n";
    ss << "Content-Length: " << body.size() << "\r\n";
    ss << "Access-Control-Allow-Origin: *\r\n";
    ss << "\r\n";
    ss << body;

    std::string response = ss.str();
    ::send(client_fd, response.c_str(), response.size(), 0);
}

void DashServer::send_http_error(int client_fd, int status_code, const std::string& message) {
    send_http_response(client_fd, status_code, "text/plain", message);
}

} // namespace streaming
