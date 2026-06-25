/**
 * @file dns_forwarder.cpp
 * @brief DNS 转发器和负载均衡器实现
 *
 * 实现 DNS 转发器功能：
 * - 接收客户端查询
 * - 转发到上游服务器
 * - 缓存响应
 * - 负载均衡
 */

#include "application/dns_forwarder.h"
#include "resolver/dns_resolver.h"
#include "monitoring/dns_monitor.h"

#include <algorithm>

namespace dns {

// ============================================================================
// DnsForwarder 实现
// ============================================================================

DnsForwarder::DnsForwarder(const ForwarderConfig& config)
    : config_(config) {

    if (config_.enable_cache) {
        cache_ = std::make_unique<DnsCache>(config_.cache_config);
    }
}

DnsForwarder::~DnsForwarder() {
    stop();
}

bool DnsForwarder::start() {
    // 配置查询日志
    if (!config_.query_log_file.empty()) {
        query_log_ = std::make_unique<QueryLog>(config_.query_log_file);
    }

    // 设置请求处理器
    server_.set_handler([this](const DnsMessage& request,
                                const std::string& client_addr,
                                uint16_t client_port) {
        return handle_query(request, client_addr, client_port);
    });

    // 启动服务器
    if (!server_.start()) {
        DNS_LOG_ERROR("DnsForwarder", "Failed to start server");
        return false;
    }

    DNS_LOG_INFO("DnsForwarder", "DNS forwarder started with " +
                 std::to_string(config_.upstream_servers.size()) +
                 " upstream servers");
    return true;
}

void DnsForwarder::stop() {
    server_.stop();
    DNS_LOG_INFO("DnsForwarder", "DNS forwarder stopped");
}

bool DnsForwarder::is_running() const {
    return server_.is_running();
}

DnsServer::Stats DnsForwarder::get_stats() const {
    return server_.get_stats();
}

void DnsForwarder::clear_cache() {
    if (cache_) {
        cache_->clear();
    }
}

DnsMessage DnsForwarder::handle_query(
    const DnsMessage& request,
    const std::string& client_addr,
    uint16_t client_port) {

    // 检查 ACL
    if (!acl_.check_query(client_addr, RecordType::ANY)) {
        DNS_LOG_WARN("DnsForwarder", "Access denied for " + client_addr);
        return DnsMessage::create_response(request, ResponseCode::REFUSED);
    }

    // 检查查询
    if (request.questions().empty()) {
        return DnsMessage::create_response(request,
                                            ResponseCode::FORMAT_ERROR);
    }

    const auto& question = request.questions()[0];
    auto name = question.name.to_string();
    auto type = question.type;

    DNS_LOG_DEBUG("DnsForwarder",
                  "Query: " + name + " " + record_type_to_string(type));

    // 检查缓存
    if (cache_) {
        auto cached = cache_->get(name, type);
        if (cached) {
            auto response = DnsMessage::create_response(request, ResponseCode::NO_ERROR);
            for (const auto& rr : cached->records) {
                response.add_answer(rr);
            }
            DNS_LOG_DEBUG("DnsForwarder", "Cache hit for " + name);
            return response;
        }
    }

    // 转发查询
    auto response = forward_query(select_upstream(), request);

    if (response) {
        // 缓存响应
        if (cache_ && response->header().rcode == ResponseCode::NO_ERROR &&
            !response->answers().empty()) {
            uint32_t min_ttl = UINT32_MAX;
            for (const auto& rr : response->answers()) {
                min_ttl = std::min(min_ttl, rr.ttl);
            }
            cache_->put(name, type, response->answers(), min_ttl);
        }

        // 记录查询日志
        if (query_log_) {
            query_log_->log_query(client_addr, name, type,
                                  response->header().rcode,
                                  response->answers().size(), 0.0);
        }

        return *response;
    }

    // 所有上游服务器都失败
    DNS_LOG_ERROR("DnsForwarder", "All upstream servers failed for " + name);
    return DnsMessage::create_response(request, ResponseCode::SERVER_FAILURE);
}

std::string DnsForwarder::select_upstream() {
    if (config_.upstream_servers.empty()) {
        return "";
    }

    switch (config_.strategy) {
        case ForwardStrategy::FIRST:
            return config_.upstream_servers[0];

        case ForwardStrategy::ROUND_ROBIN: {
            size_t index = round_robin_index_++ % config_.upstream_servers.size();
            return config_.upstream_servers[index];
        }

        case ForwardStrategy::RANDOM: {
            std::uniform_int_distribution<size_t> dist(
                0, config_.upstream_servers.size() - 1);
            return config_.upstream_servers[dist(rng_)];
        }

        case ForwardStrategy::FASTEST:
            // 简化实现：使用第一个服务器
            return config_.upstream_servers[0];

        default:
            return config_.upstream_servers[0];
    }
}

std::optional<DnsMessage> DnsForwarder::forward_query(
    const std::string& server,
    const DnsMessage& query) {

    DnsQuerier querier;
    return querier.query(server, query, config_.query_timeout);
}

// ============================================================================
// DnsLoadBalancer 实现
// ============================================================================

DnsLoadBalancer::DnsLoadBalancer(const LoadBalancerConfig& config)
    : config_(config) {}

DnsLoadBalancer::~DnsLoadBalancer() {
    stop();
}

bool DnsLoadBalancer::start() {
    // 初始化后端
    for (const auto& [address, weight] : config_.backends) {
        auto backend = std::make_unique<Backend>();
        backend->address = address;
        backend->weight = weight;
        backend->healthy = true;
        backends_.push_back(std::move(backend));
    }

    // 启动健康检查
    health_check_running_ = true;
    health_check_thread_ = std::thread(&DnsLoadBalancer::health_check_loop,
                                        this);

    // 设置请求处理器
    server_.set_handler([this](const DnsMessage& request,
                                const std::string& client_addr,
                                uint16_t client_port) {
        return handle_query(request, client_addr, client_port);
    });

    // 启动服务器
    if (!server_.start()) {
        DNS_LOG_ERROR("DnsLoadBalancer", "Failed to start server");
        return false;
    }

    DNS_LOG_INFO("DnsLoadBalancer", "DNS load balancer started with " +
                 std::to_string(backends_.size()) + " backends");
    return true;
}

void DnsLoadBalancer::stop() {
    health_check_running_ = false;
    if (health_check_thread_.joinable()) {
        health_check_thread_.join();
    }
    server_.stop();
    DNS_LOG_INFO("DnsLoadBalancer", "DNS load balancer stopped");
}

bool DnsLoadBalancer::is_running() const {
    return server_.is_running();
}

std::vector<DnsLoadBalancer::BackendStatus>
DnsLoadBalancer::get_backend_status() const {
    std::vector<BackendStatus> status;

    for (const auto& backend : backends_) {
        BackendStatus s;
        s.address = backend->address;
        s.weight = backend->weight;
        s.healthy = backend->healthy.load();
        s.requests = backend->requests.load();

        uint64_t total_time = backend->total_response_time_us.load();
        uint64_t req_count = backend->requests.load();
        s.avg_response_time_ms = req_count > 0 ?
            static_cast<double>(total_time) / req_count / 1000.0 : 0.0;

        status.push_back(s);
    }

    return status;
}

DnsMessage DnsLoadBalancer::handle_query(
    const DnsMessage& request,
    const std::string& client_addr,
    uint16_t client_port) {

    if (request.questions().empty()) {
        return DnsMessage::create_response(request,
                                            ResponseCode::FORMAT_ERROR);
    }

    const auto& question = request.questions()[0];
    auto name = question.name.to_string();
    auto type = question.type;

    // 健康检查查询
    if (name == config_.health_check_domain) {
        auto response = DnsMessage::create_response(request, ResponseCode::NO_ERROR);

        ResourceRecord rr;
        rr.name = DnsName(name);
        rr.type = RecordType::A;
        rr.rclass = QueryClass::IN;
        rr.ttl = 0;

        // 返回健康后端的数量
        size_t healthy_count = 0;
        for (const auto& backend : backends_) {
            if (backend->healthy) healthy_count++;
        }

        std::array<uint8_t, 4> addr = {127, 0, 0,
                                         static_cast<uint8_t>(healthy_count)};
        rr.rdata = addr;
        response.add_answer(rr);

        return response;
    }

    // 选择后端
    auto backend_addr = select_backend();
    if (backend_addr.empty()) {
        DNS_LOG_ERROR("DnsLoadBalancer", "No healthy backend available");
        return DnsMessage::create_response(request, ResponseCode::SERVER_FAILURE);
    }

    // 找到后端
    Backend* backend = nullptr;
    for (auto& b : backends_) {
        if (b->address == backend_addr) {
            backend = b.get();
            break;
        }
    }

    if (!backend) {
        return DnsMessage::create_response(request, ResponseCode::SERVER_FAILURE);
    }

    // 转发查询
    auto start = std::chrono::steady_clock::now();

    DnsQuerier querier;
    auto response = querier.query(backend_addr, request,
                                   std::chrono::seconds(5));

    auto end = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(
        end - start);

    // 更新统计
    backend->requests++;
    backend->total_response_time_us += duration.count();

    if (response) {
        return *response;
    }

    // 标记后端不健康
    backend->healthy = false;
    DNS_LOG_WARN("DnsLoadBalancer",
                 "Backend " + backend_addr + " failed, marking unhealthy");

    return DnsMessage::create_response(request, ResponseCode::SERVER_FAILURE);
}

std::string DnsLoadBalancer::select_backend() {
    if (backends_.empty()) return "";

    if (config_.enable_weighted) {
        // 加权轮询
        size_t total_weight = 0;
        for (const auto& backend : backends_) {
            if (backend->healthy) {
                total_weight += backend->weight;
            }
        }

        if (total_weight == 0) return "";

        size_t target = current_index_++ % total_weight;
        size_t cumulative = 0;

        for (const auto& backend : backends_) {
            if (!backend->healthy) continue;
            cumulative += backend->weight;
            if (target < cumulative) {
                return backend->address;
            }
        }
    } else {
        // 简单轮询
        size_t healthy_count = 0;
        for (const auto& backend : backends_) {
            if (backend->healthy) healthy_count++;
        }

        if (healthy_count == 0) return "";

        size_t index = current_index_++ % healthy_count;
        size_t current = 0;

        for (const auto& backend : backends_) {
            if (!backend->healthy) continue;
            if (current == index) {
                return backend->address;
            }
            current++;
        }
    }

    return backends_[0]->address;
}

void DnsLoadBalancer::health_check_loop() {
    while (health_check_running_) {
        std::this_thread::sleep_for(config_.health_check_interval);

        DNS_LOG_DEBUG("DnsLoadBalancer", "Running health check");

        for (auto& backend : backends_) {
            // 构造健康检查查询
            auto query = DnsMessage::create_query(
                config_.health_check_domain, RecordType::A);

            DnsQuerier querier;
            auto response = querier.query(backend->address, query,
                                           std::chrono::seconds(3));

            bool was_healthy = backend->healthy.load();
            backend->healthy = response.has_value();

            if (was_healthy && !backend->healthy) {
                DNS_LOG_WARN("DnsLoadBalancer",
                             "Backend " + backend->address + " is down");
            } else if (!was_healthy && backend->healthy) {
                DNS_LOG_INFO("DnsLoadBalancer",
                             "Backend " + backend->address + " is back up");
            }
        }
    }
}

} // namespace dns
