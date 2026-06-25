/**
 * @file authoritative_server.cpp
 * @brief 权威 DNS 服务器实现
 *
 * 实现权威 DNS 服务器功能：
 * - 处理来自递归服务器的查询
 * - 返回权威回答
 * - 支持区域传输
 * - 支持动态更新
 */

#include "application/authoritative_server.h"
#include "monitoring/dns_monitor.h"

namespace dns {

// ============================================================================
// AuthoritativeServer 实现
// ============================================================================

AuthoritativeServer::AuthoritativeServer(const AuthoritativeConfig& config)
    : config_(config) {
    // 配置 ACL
    acl_.set_default_action(config.default_action);
}

AuthoritativeServer::~AuthoritativeServer() {
    stop();
}

bool AuthoritativeServer::start() {
    // 加载区域
    for (const auto& zone_config : config_.zones) {
        if (!zone_manager_.load_zone(zone_config)) {
            DNS_LOG_ERROR("AuthoritativeServer",
                         "Failed to load zone: " + zone_config.zone_name);
            return false;
        }
    }

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
        DNS_LOG_ERROR("AuthoritativeServer", "Failed to start server");
        return false;
    }

    DNS_LOG_INFO("AuthoritativeServer", "Authoritative server started");
    return true;
}

void AuthoritativeServer::stop() {
    server_.stop();
    DNS_LOG_INFO("AuthoritativeServer", "Authoritative server stopped");
}

bool AuthoritativeServer::is_running() const {
    return server_.is_running();
}

DnsServer::Stats AuthoritativeServer::get_stats() const {
    return server_.get_stats();
}

bool AuthoritativeServer::reload_zones() {
    for (const auto& zone_config : config_.zones) {
        if (!zone_manager_.reload_zone(zone_config.zone_name)) {
            DNS_LOG_ERROR("AuthoritativeServer",
                         "Failed to reload zone: " + zone_config.zone_name);
            return false;
        }
    }
    return true;
}

DnsMessage AuthoritativeServer::handle_query(
    const DnsMessage& request,
    const std::string& client_addr,
    uint16_t client_port) {

    // 检查 ACL
    if (!acl_.check_query(client_addr, RecordType::ANY)) {
        DNS_LOG_WARN("AuthoritativeServer",
                     "Access denied for " + client_addr);
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

    DNS_LOG_DEBUG("AuthoritativeServer",
                  "Query: " + name + " " + record_type_to_string(type));

    // 处理区域传输请求
    if (type == RecordType::AXFR || type == RecordType::IXFR) {
        if (!acl_.check_transfer(client_addr)) {
            DNS_LOG_WARN("AuthoritativeServer",
                         "Transfer denied for " + client_addr);
            return DnsMessage::create_response(request, ResponseCode::REFUSED);
        }
        return handle_transfer(request, client_addr);
    }

    // 处理动态更新
    if (request.header().opcode == Opcode::UPDATE) {
        if (!acl_.check_update(client_addr)) {
            DNS_LOG_WARN("AuthoritativeServer",
                         "Update denied for " + client_addr);
            return DnsMessage::create_response(request, ResponseCode::REFUSED);
        }
        return handle_update(request, client_addr);
    }

    // 查找区域
    auto* zone = zone_manager_.find_zone(name);
    if (!zone) {
        DNS_LOG_DEBUG("AuthoritativeServer", "Zone not found for " + name);
        return DnsMessage::create_response(request, ResponseCode::NAME_ERROR);
    }

    // 查询记录
    auto records = zone->get_records(name, type);

    // 创建响应
    auto response = DnsMessage::create_response(request, ResponseCode::NO_ERROR);
    response.header().aa = true;  // 权威回答

    if (records.empty()) {
        // 没有找到记录，返回 SOA (用于否定回答)
        auto soa = zone->get_soa();
        if (soa) {
            response.add_authority(*soa);
        }
        response.header().rcode = ResponseCode::NAME_ERROR;
    } else {
        // 添加回答
        for (const auto& rr : records) {
            response.add_answer(rr);
        }

        // 添加授权记录 (NS)
        auto ns_records = zone->get_records(zone->name(), RecordType::NS);
        for (const auto& ns : ns_records) {
            response.add_authority(ns);
        }

        // 添加附加记录 (glue records)
        for (const auto& ns : ns_records) {
            if (std::holds_alternative<DnsName>(ns.rdata)) {
                auto ns_name = std::get<DnsName>(ns.rdata).to_string();
                auto a_records = zone->get_records(ns_name, RecordType::A);
                for (const auto& a : a_records) {
                    response.add_additional(a);
                }
            }
        }
    }

    // 记录查询日志
    if (query_log_) {
        query_log_->log_query(client_addr, name, type,
                              response.header().rcode,
                              response.answers().size(), 0.0);
    }

    return response;
}

DnsMessage AuthoritativeServer::handle_transfer(
    const DnsMessage& request,
    const std::string& client_addr) {

    if (request.questions().empty()) {
        return DnsMessage::create_response(request,
                                            ResponseCode::FORMAT_ERROR);
    }

    const auto& question = request.questions()[0];
    auto zone_name = question.name.to_string();

    auto* zone = zone_manager_.get_zone(zone_name);
    if (!zone) {
        return DnsMessage::create_response(request, ResponseCode::NAME_ERROR);
    }

    // 构造区域传输响应
    auto response = DnsMessage::create_response(request, ResponseCode::NO_ERROR);
    response.header().aa = true;

    // 添加 SOA 记录
    auto soa = zone->get_soa();
    if (soa) {
        response.add_answer(*soa);
    }

    // 添加所有记录
    auto records = zone->get_all_records();
    for (const auto& rr : records) {
        response.add_answer(rr);
    }

    // 再次添加 SOA 记录 (标记结束)
    if (soa) {
        response.add_answer(*soa);
    }

    DNS_LOG_INFO("AuthoritativeServer",
                 "Zone transfer for " + zone_name + " from " + client_addr);

    return response;
}

DnsMessage AuthoritativeServer::handle_update(
    const DnsMessage& request,
    const std::string& client_addr) {

    if (request.questions().empty()) {
        return DnsMessage::create_response(request,
                                            ResponseCode::FORMAT_ERROR);
    }

    const auto& question = request.questions()[0];
    auto zone_name = question.name.to_string();

    auto result = zone_manager_.handle_update(zone_name, request);

    DNS_LOG_INFO("AuthoritativeServer",
                 "Dynamic update for " + zone_name + " from " + client_addr +
                 ": " + response_code_to_string(result));

    return DnsMessage::create_response(request, result);
}

} // namespace dns
