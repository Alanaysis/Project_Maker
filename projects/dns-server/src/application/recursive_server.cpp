/**
 * @file recursive_server.cpp
 * @brief 递归 DNS 服务器实现
 *
 * 实现递归 DNS 服务器功能：
 * - 接收客户端查询
 * - 执行递归解析
 * - 缓存结果
 * - 转发查询
 */

#include "application/recursive_server.h"
#include "monitoring/dns_monitor.h"

namespace dns {

// ============================================================================
// RecursiveServer 实现
// ============================================================================

RecursiveServer::RecursiveServer(const RecursiveConfig& config)
    : config_(config), resolver_(config.resolver_config) {
    acl_.set_default_action(config.default_action);
}

RecursiveServer::~RecursiveServer() {
    stop();
}

bool RecursiveServer::start() {
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
        DNS_LOG_ERROR("RecursiveServer", "Failed to start server");
        return false;
    }

    DNS_LOG_INFO("RecursiveServer", "Recursive server started");
    return true;
}

void RecursiveServer::stop() {
    server_.stop();
    DNS_LOG_INFO("RecursiveServer", "Recursive server stopped");
}

bool RecursiveServer::is_running() const {
    return server_.is_running();
}

DnsServer::Stats RecursiveServer::get_stats() const {
    return server_.get_stats();
}

void RecursiveServer::clear_cache() {
    resolver_.clear_cache();
}

CacheStats RecursiveServer::get_cache_stats() const {
    return resolver_.get_cache_stats();
}

DnsMessage RecursiveServer::handle_query(
    const DnsMessage& request,
    const std::string& client_addr,
    uint16_t client_port) {

    // 检查 ACL
    if (!acl_.check_query(client_addr, RecordType::ANY)) {
        DNS_LOG_WARN("RecursiveServer", "Access denied for " + client_addr);
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

    DNS_LOG_DEBUG("RecursiveServer",
                  "Query: " + name + " " + record_type_to_string(type));

    // 执行递归解析
    auto result = resolver_.resolve(name, type);

    // 创建响应
    auto response = DnsMessage::create_response(request, result.status);

    // 添加回答
    for (const auto& rr : result.answers) {
        response.add_answer(rr);
    }

    // 添加授权记录
    for (const auto& rr : result.authorities) {
        response.add_authority(rr);
    }

    // 添加附加记录
    for (const auto& rr : result.additionals) {
        response.add_additional(rr);
    }

    // 设置递归可用标志
    response.header().ra = true;

    // 记录查询日志
    if (query_log_) {
        query_log_->log_query(client_addr, name, type,
                              result.status, result.answers.size(),
                              result.resolve_time.count());
    }

    DNS_LOG_DEBUG("RecursiveServer",
                  "Response: " + name + " -> " +
                  std::to_string(result.answers.size()) + " answers" +
                  (result.from_cache ? " (cached)" : ""));

    return response;
}

} // namespace dns
