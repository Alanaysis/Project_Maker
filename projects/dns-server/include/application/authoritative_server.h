#pragma once

/**
 * @file authoritative_server.h
 * @brief 权威 DNS 服务器
 *
 * 实现权威 DNS 服务器功能：
 * - 处理来自递归服务器的查询
 * - 返回权威回答
 * - 支持区域传输
 * - 支持动态更新
 */

#include "../protocol/dns_server.h"
#include "../zone/zone_manager.h"
#include "../security/access_control.h"
#include "../monitoring/dns_monitor.h"

#include <string>
#include <memory>

namespace dns {

// ============================================================================
// 权威服务器配置
// ============================================================================

struct AuthoritativeConfig {
    DnsServerConfig server_config;      // 服务器配置
    std::vector<ZoneConfig> zones;      // 区域配置
    AclAction default_action = AclAction::ALLOW;  // 默认 ACL 动作
    bool enable_transfer = true;        // 启用区域传输
    bool enable_update = false;         // 启用动态更新
    std::string query_log_file;         // 查询日志文件
};

// ============================================================================
// 权威 DNS 服务器
// ============================================================================

class AuthoritativeServer {
public:
    explicit AuthoritativeServer(const AuthoritativeConfig& config);
    ~AuthoritativeServer();

    // 启动服务器
    bool start();

    // 停止服务器
    void stop();

    // 是否运行中
    bool is_running() const;

    // 获取区域管理器
    ZoneManager& zone_manager() { return zone_manager_; }

    // 获取统计信息
    DnsServer::Stats get_stats() const;

    // 重新加载区域
    bool reload_zones();

private:
    // 处理 DNS 查询
    DnsMessage handle_query(const DnsMessage& request,
                            const std::string& client_addr,
                            uint16_t client_port);

    // 处理区域传输
    DnsMessage handle_transfer(const DnsMessage& request,
                                const std::string& client_addr);

    // 处理动态更新
    DnsMessage handle_update(const DnsMessage& request,
                              const std::string& client_addr);

    AuthoritativeConfig config_;
    DnsServer server_;
    ZoneManager zone_manager_;
    AccessControlList acl_;
    std::unique_ptr<QueryLog> query_log_;
};

} // namespace dns
