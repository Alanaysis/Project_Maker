/**
 * @file basic_server.cpp
 * @brief 基本 DNS 服务器示例
 *
 * 演示如何创建和运行一个基本的 DNS 服务器
 */

#include "protocol/dns_server.h"
#include "monitoring/dns_monitor.h"

#include <iostream>
#include <signal.h>

using namespace dns;

static std::atomic<bool> running{true};

void signal_handler(int sig) {
    std::cout << "\nReceived signal " << sig << ", shutting down..." << std::endl;
    running = false;
}

int main() {
    // 设置信号处理
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // 配置日志
    Logger::instance().set_level(LogLevel::DEBUG);
    Logger::instance().add_sink(std::make_unique<ConsoleSink>());

    std::cout << "=== DNS Server Example ===" << std::endl;

    // 创建服务器配置
    DnsServerConfig config;
    config.bind_address = "127.0.0.1";
    config.port = 5353;  // 使用非特权端口
    config.thread_pool_size = 4;
    config.enable_udp = true;
    config.enable_tcp = true;

    // 创建服务器
    DnsServer server(config);

    // 设置请求处理器
    server.set_handler([](const DnsMessage& request,
                           const std::string& client_addr,
                           uint16_t client_port) -> DnsMessage {
        // 创建响应
        auto response = DnsMessage::create_response(request, ResponseCode::NO_ERROR);

        if (request.questions().empty()) {
            response.header().rcode = ResponseCode::FORMAT_ERROR;
            return response;
        }

        const auto& question = request.questions()[0];
        auto name = question.name.to_string();
        auto type = question.type;

        std::cout << "Query from " << client_addr << ": "
                  << name << " " << record_type_to_string(type) << std::endl;

        // 简单的记录响应
        if (type == RecordType::A && name == "example.com") {
            ResourceRecord rr;
            rr.name = DnsName(name);
            rr.type = RecordType::A;
            rr.rclass = QueryClass::IN;
            rr.ttl = 3600;

            std::array<uint8_t, 4> addr = {93, 184, 216, 34};
            rr.rdata = addr;

            response.add_answer(rr);
            response.header().rcode = ResponseCode::NO_ERROR;
        } else if (type == RecordType::AAAA && name == "example.com") {
            ResourceRecord rr;
            rr.name = DnsName(name);
            rr.type = RecordType::AAAA;
            rr.rclass = QueryClass::IN;
            rr.ttl = 3600;

            std::array<uint8_t, 16> addr = {
                0x26, 0x06, 0x28, 0x00, 0x02, 0x20, 0x00, 0x01,
                0x02, 0x48, 0x18, 0x93, 0x25, 0xc8, 0x19, 0x46
            };
            rr.rdata = addr;

            response.add_answer(rr);
            response.header().rcode = ResponseCode::NO_ERROR;
        } else if (type == RecordType::MX && name == "example.com") {
            ResourceRecord rr;
            rr.name = DnsName(name);
            rr.type = RecordType::MX;
            rr.rclass = QueryClass::IN;
            rr.ttl = 3600;

            std::vector<uint8_t> data;
            uint16_t preference = 10;
            data.push_back((preference >> 8) & 0xFF);
            data.push_back(preference & 0xFF);
            auto mx_name = DnsName("mail.example.com");
            auto name_data = mx_name.serialize();
            data.insert(data.end(), name_data.begin(), name_data.end());
            rr.rdata = data;

            response.add_answer(rr);
            response.header().rcode = ResponseCode::NO_ERROR;
        } else {
            response.header().rcode = ResponseCode::NAME_ERROR;
        }

        return response;
    });

    // 启动服务器
    if (!server.start()) {
        std::cerr << "Failed to start server" << std::endl;
        return 1;
    }

    std::cout << "Server started on " << config.bind_address
              << ":" << config.port << std::endl;
    std::cout << "Press Ctrl+C to stop" << std::endl;

    // 运行直到收到信号
    while (running) {
        std::this_thread::sleep_for(std::chrono::seconds(1));

        // 显示统计信息
        auto stats = server.get_stats();
        std::cout << "\rQueries: " << stats.queries_received
                  << " | Processed: " << stats.queries_processed
                  << " | Failed: " << stats.queries_failed
                  << " | Avg time: " << std::fixed << std::setprecision(2)
                  << stats.avg_response_time_ms << "ms" << std::flush;
    }

    std::cout << std::endl;

    // 停止服务器
    server.stop();
    std::cout << "Server stopped" << std::endl;

    return 0;
}
