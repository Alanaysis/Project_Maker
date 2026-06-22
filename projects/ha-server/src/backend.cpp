/**
 * @file backend.cpp
 * @brief 后端服务器管理实现
 */

#include "../include/backend.h"
#include <algorithm>

namespace ha_server {

Backend* BackendManager::add_backend(const std::string& host, int port, int weight) {
    std::lock_guard<std::mutex> lock(mutex_);

    // 检查是否已存在
    for (auto& backend : backends_) {
        if (backend->host == host && backend->port == port) {
            backend->weight = weight;
            return backend.get();
        }
    }

    // 创建新的后端
    auto backend = std::make_unique<Backend>(host, port, weight);
    Backend* ptr = backend.get();
    backends_.push_back(std::move(backend));

    log_message(LogLevel::INFO, "Added backend: " + ptr->address() +
                " weight=" + std::to_string(weight));
    return ptr;
}

bool BackendManager::remove_backend(const std::string& id) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = std::find_if(backends_.begin(), backends_.end(),
        [&id](const std::unique_ptr<Backend>& b) {
            return b->id == id;
        });

    if (it != backends_.end()) {
        log_message(LogLevel::INFO, "Removed backend: " + (*it)->address());
        backends_.erase(it);
        return true;
    }
    return false;
}

std::vector<Backend*> BackendManager::get_all_backends() {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<Backend*> result;
    result.reserve(backends_.size());
    for (auto& backend : backends_) {
        result.push_back(backend.get());
    }
    return result;
}

std::vector<Backend*> BackendManager::get_healthy_backends() {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<Backend*> result;
    for (auto& backend : backends_) {
        if (backend->is_healthy()) {
            result.push_back(backend.get());
        }
    }
    return result;
}

Backend* BackendManager::get_backend(const std::string& id) {
    std::lock_guard<std::mutex> lock(mutex_);

    for (auto& backend : backends_) {
        if (backend->id == id) {
            return backend.get();
        }
    }
    return nullptr;
}

size_t BackendManager::size() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return backends_.size();
}

size_t BackendManager::healthy_count() const {
    std::lock_guard<std::mutex> lock(mutex_);

    size_t count = 0;
    for (const auto& backend : backends_) {
        if (backend->is_healthy()) {
            count++;
        }
    }
    return count;
}

} // namespace ha_server
