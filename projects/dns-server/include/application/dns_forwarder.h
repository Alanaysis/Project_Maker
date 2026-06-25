#pragma once

/**
 * @file dns_forwarder.h
 * @brief DNS 转发器
 *
 * 实现 DNS 转发器功能：
 * - 接收客户端查询
 * - 转发到上游服务器
 * - 缓存响应
 * - 负载均衡
 */

#include "../protocol/dns_server.h"
#include "../resolver/dns_cache.h"
#include "../security/access_control.h"
#include "../monitoring/dns_monitor.h"

#include <string>
#include <vector>
#include <memory>
#include <random>

namespace dns {

// ============================================================================
// 转发器配置
// ============================================================================

enum class ForwardStrategy {
    FIRST,      // 使用第一个可用服务器
    ROUND_ROBIN, // 轮询
    RANDOM,     // 随机
    FASTEST,    // 最快响应
};

struct ForwarderConfig {
    DnsServerConfig server_config;      // 服务器配置
    CacheConfig cache_config;           // 缓存配置
    std::vector<std::string> upstream_servers;  // 上游服务器
    ForwardStrategy strategy = ForwardStrategy::FIRST;
    bool enable_cache = true;           // 启用缓存
    std::chrono::seconds query_timeout{5};  // 查询超时
    std::string query_log_file;         // 查询日志文件
};

// ============================================================================
// DNS 转发器
// ============================================================================

class DnsForwarder {
public:
    explicit DnsForwarder(const ForwarderConfig& config);
    ~DnsForwarder();

    // 启动转发器
    bool start();

    // 停止转发器
    void stop();

    // 是否运行中
    bool is_running() const;

    // 获取统计信息
    DnsServer::Stats get_stats() const;

    // 清除缓存
    void clear_cache();

private:
    // 处理 DNS 查询
    DnsMessage handle_query(const DnsMessage& request,
                            const std::string& client_addr,
                            uint16_t client_port);

    // 选择上游服务器
    std::string select_upstream();

    // 转发查询
    std::optional<DnsMessage> forward_query(const std::string& server,
                                             const DnsMessage& query);

    ForwarderConfig config_;
    DnsServer server_;
    std::unique_ptr<DnsCache> cache_;
    AccessControlList acl_;
    std::unique_ptr<QueryLog> query_log_;

    // 负载均衡状态
    std::atomic<size_t> round_robin_index_{0};
    std::mt19937 rng_{std::random_device{}()};
};

// ============================================================================
// DNS 负载均衡器
// ============================================================================

struct LoadBalancerConfig {
    DnsServerConfig server_config;
    std::vector<std::pair<std::string, uint32_t>> backends;  // (IP, 权重)
    std::string health_check_domain = "health.example.com";
    std::chrono::seconds health_check_interval{30};
    bool enable_weighted = true;
};

class DnsLoadBalancer {
public:
    explicit DnsLoadBalancer(const LoadBalancerConfig& config);
    ~DnsLoadBalancer();

    // 启动负载均衡器
    bool start();

    // 停止负载均衡器
    void stop();

    // 是否运行中
    bool is_running() const;

    // 获取后端状态
    struct BackendStatus {
        std::string address;
        uint32_t weight;
        bool healthy;
        uint64_t requests;
        double avg_response_time_ms;
    };
    std::vector<BackendStatus> get_backend_status() const;

private:
    // 处理 DNS 查询
    DnsMessage handle_query(const DnsMessage& request,
                            const std::string& client_addr,
                            uint16_t client_port);

    // 加权轮询选择后端
    std::string select_backend();

    // 健康检查
    void health_check_loop();

    LoadBalancerConfig config_;
    DnsServer server_;

    struct Backend {
        std::string address;
        uint32_t weight;
        std::atomic<bool> healthy{true};
        std::atomic<uint64_t> requests{0};
        std::atomic<uint64_t> total_response_time_us{0};
    };
    std::vector<std::unique_ptr<Backend>> backends_;

    std::atomic<size_t> current_index_{0};
    std::atomic<bool> health_check_running_{false};
    std::thread health_check_thread_;
};

} // namespace dns
