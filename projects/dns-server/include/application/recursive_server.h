#pragma once

/**
 * @file recursive_server.h
 * @brief 递归 DNS 服务器
 *
 * 实现递归 DNS 服务器功能：
 * - 接收客户端查询
 * - 执行递归解析
 * - 缓存结果
 * - 转发查询
 */

#include "../protocol/dns_server.h"
#include "../resolver/dns_resolver.h"
#include "../resolver/dns_cache.h"
#include "../security/access_control.h"
#include "../monitoring/dns_monitor.h"

#include <string>
#include <memory>

namespace dns {

// ============================================================================
// 递归服务器配置
// ============================================================================

struct RecursiveConfig {
    DnsServerConfig server_config;      // 服务器配置
    ResolverConfig resolver_config;     // 解析器配置
    CacheConfig cache_config;           // 缓存配置
    AclAction default_action = AclAction::ALLOW;  // 默认 ACL 动作
    std::string query_log_file;         // 查询日志文件
};

// ============================================================================
// 递归 DNS 服务器
// ============================================================================

class RecursiveServer {
public:
    explicit RecursiveServer(const RecursiveConfig& config);
    ~RecursiveServer();

    // 启动服务器
    bool start();

    // 停止服务器
    void stop();

    // 是否运行中
    bool is_running() const;

    // 获取解析器
    DnsResolver& resolver() { return resolver_; }

    // 获取统计信息
    DnsServer::Stats get_stats() const;

    // 清除缓存
    void clear_cache();

    // 获取缓存统计
    CacheStats get_cache_stats() const;

private:
    // 处理 DNS 查询
    DnsMessage handle_query(const DnsMessage& request,
                            const std::string& client_addr,
                            uint16_t client_port);

    RecursiveConfig config_;
    DnsServer server_;
    DnsResolver resolver_;
    AccessControlList acl_;
    std::unique_ptr<QueryLog> query_log_;
};

} // namespace dns
