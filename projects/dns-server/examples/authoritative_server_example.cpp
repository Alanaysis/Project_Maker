/**
 * @file authoritative_server_example.cpp
 * @brief 权威 DNS 服务器示例
 *
 * 演示如何创建和运行一个权威 DNS 服务器
 */

#include "application/authoritative_server.h"
#include "monitoring/dns_monitor.h"

#include <iostream>
#include <signal.h>

using namespace dns;

static std::atomic<bool> running{true};

void signal_handler(int sig) {
    running = false;
}

int main() {
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // 配置日志
    Logger::instance().set_level(LogLevel::INFO);
    Logger::instance().add_sink(std::make_unique<ConsoleSink>());

    std::cout << "=== Authoritative DNS Server Example ===" << std::endl;

    // 创建区域文件内容
    std::string zone_content = R"(
$ORIGIN example.com.
$TTL 3600

@       IN  SOA   ns1.example.com. admin.example.com. (
                  2024010101  ; Serial
                  3600        ; Refresh
                  900         ; Retry
                  604800      ; Expire
                  86400       ; Minimum TTL
                  )

@       IN  NS    ns1.example.com.
@       IN  NS    ns2.example.com.

ns1     IN  A     192.168.1.1
ns2     IN  A     192.168.1.2

@       IN  A     93.184.216.34
@       IN  AAAA  2606:2800:220:1:248:1893:25c8:1946

www     IN  CNAME example.com.
mail    IN  A     192.168.1.10

@       IN  MX    10 mail.example.com.
@       IN  MX    20 mail2.example.com.

@       IN  TXT   "v=spf1 mx ~all"

_http   IN  SRV   10 60 80 www.example.com.
)";

    // 创建区域
    ZoneFileParser parser;
    auto zone = parser.parse_string(zone_content, "example.com");
    if (!zone) {
        std::cerr << "Failed to parse zone: " << parser.error_message() << std::endl;
        return 1;
    }

    // 配置权威服务器
    AuthoritativeConfig config;
    config.server_config.bind_address = "127.0.0.1";
    config.server_config.port = 5354;
    config.server_config.thread_pool_size = 4;
    config.default_action = AclAction::ALLOW;
    config.enable_transfer = true;
    config.enable_update = true;

    // 添加区域配置
    ZoneConfig zone_config;
    zone_config.zone_name = "example.com";
    zone_config.type = ZoneType::PRIMARY;
    zone_config.allow_transfer = true;
    zone_config.transfer_allowed = {"192.168.1.0/24"};
    zone_config.allow_update = true;
    zone_config.update_allowed = {"192.168.1.0/24"};
    config.zones.push_back(zone_config);

    // 创建服务器
    AuthoritativeServer server(config);

    // 添加区域
    server.zone_manager().add_zone(std::move(*zone));

    // 启动服务器
    if (!server.start()) {
        std::cerr << "Failed to start server" << std::endl;
        return 1;
    }

    std::cout << "Authoritative server started on 127.0.0.1:5354" << std::endl;
    std::cout << "Serving zone: example.com" << std::endl;
    std::cout << "Press Ctrl+C to stop" << std::endl;

    // 运行直到收到信号
    while (running) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    server.stop();
    std::cout << "Server stopped" << std::endl;

    return 0;
}
