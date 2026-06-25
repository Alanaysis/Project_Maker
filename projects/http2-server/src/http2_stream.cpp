/**
 * @file http2_stream.cpp
 * @brief HTTP/2 流管理实现
 */

#include "http2_stream.h"
#include <algorithm>
#include <stdexcept>

namespace http2 {

Stream::Stream(uint32_t stream_id, uint32_t initial_window_size)
    : id_(stream_id),
      state_(StreamState::IDLE),
      send_window_(initial_window_size),
      recv_window_(initial_window_size) {}

bool Stream::consume_send_window(int32_t bytes) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (send_window_ < bytes) {
        return false;
    }
    send_window_ -= bytes;
    return true;
}

bool Stream::consume_recv_window(int32_t bytes) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (recv_window_ < bytes) {
        return false;
    }
    recv_window_ -= bytes;
    return true;
}

void Stream::add_send_data(const std::vector<uint8_t>& data) {
    std::lock_guard<std::mutex> lock(mutex_);
    send_buffer_.push(data);
}

std::vector<uint8_t> Stream::get_send_data(size_t max_size) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<uint8_t> result;

    while (!send_buffer_.empty() && result.size() < max_size) {
        auto& front = send_buffer_.front();
        size_t remaining = max_size - result.size();

        if (front.size() <= remaining) {
            result.insert(result.end(), front.begin(), front.end());
            send_buffer_.pop();
        } else {
            result.insert(result.end(), front.begin(), front.begin() + remaining);
            front.erase(front.begin(), front.begin() + remaining);
        }
    }

    return result;
}

void Stream::send_headers(bool end_stream) {
    switch (state_) {
        case StreamState::IDLE:
            state_ = end_stream ? StreamState::HALF_CLOSED_LOCAL : StreamState::OPEN;
            break;
        case StreamState::OPEN:
            if (end_stream) state_ = StreamState::HALF_CLOSED_LOCAL;
            break;
        case StreamState::HALF_CLOSED_REMOTE:
            if (end_stream) state_ = StreamState::CLOSED;
            break;
        default:
            break;
    }
}

void Stream::recv_headers(bool end_stream) {
    switch (state_) {
        case StreamState::IDLE:
            state_ = end_stream ? StreamState::HALF_CLOSED_REMOTE : StreamState::OPEN;
            break;
        case StreamState::OPEN:
            if (end_stream) state_ = StreamState::HALF_CLOSED_REMOTE;
            break;
        case StreamState::HALF_CLOSED_LOCAL:
            if (end_stream) state_ = StreamState::CLOSED;
            break;
        default:
            break;
    }
}

void Stream::send_data(bool end_stream) {
    if (end_stream && state_ == StreamState::OPEN) {
        state_ = StreamState::HALF_CLOSED_LOCAL;
    } else if (end_stream && state_ == StreamState::HALF_CLOSED_REMOTE) {
        state_ = StreamState::CLOSED;
    }
}

void Stream::recv_data(bool end_stream) {
    if (end_stream && state_ == StreamState::OPEN) {
        state_ = StreamState::HALF_CLOSED_REMOTE;
    } else if (end_stream && state_ == StreamState::HALF_CLOSED_LOCAL) {
        state_ = StreamState::CLOSED;
    }
}

void Stream::send_rst_stream() {
    state_ = StreamState::CLOSED;
}

void Stream::recv_rst_stream() {
    state_ = StreamState::CLOSED;
}

// StreamManager 实现

StreamManager::StreamManager(uint32_t initial_window_size)
    : initial_window_size_(initial_window_size) {}

std::shared_ptr<Stream> StreamManager::create_stream(uint32_t stream_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (streams_.size() >= max_concurrent_streams_) {
        return nullptr;
    }

    auto stream = std::make_shared<Stream>(stream_id, initial_window_size_);
    streams_[stream_id] = stream;
    return stream;
}

std::shared_ptr<Stream> StreamManager::get_stream(uint32_t stream_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = streams_.find(stream_id);
    if (it != streams_.end()) {
        return it->second;
    }
    return nullptr;
}

void StreamManager::close_stream(uint32_t stream_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    streams_.erase(stream_id);
}

std::vector<std::shared_ptr<Stream>> StreamManager::get_active_streams() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::shared_ptr<Stream>> result;
    for (const auto& pair : streams_) {
        if (pair.second->get_state() != StreamState::CLOSED) {
            result.push_back(pair.second);
        }
    }
    return result;
}

size_t StreamManager::get_active_stream_count() const {
    std::lock_guard<std::mutex> lock(mutex_);
    size_t count = 0;
    for (const auto& pair : streams_) {
        if (pair.second->get_state() != StreamState::CLOSED) {
            ++count;
        }
    }
    return count;
}

bool StreamManager::can_create_stream() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return streams_.size() < max_concurrent_streams_;
}

void StreamManager::update_all_windows(int32_t delta) {
    std::lock_guard<std::mutex> lock(mutex_);
    for (auto& pair : streams_) {
        pair.second->update_send_window(delta);
    }
}

} // namespace http2
