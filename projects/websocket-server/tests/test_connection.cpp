/**
 * @file test_connection.cpp
 * @brief WebSocket 连接测试
 *
 * 测试 WebSocket 连接的基本功能。
 * 注意：这些测试需要实际的网络连接。
 */

#include "websocket/server.h"
#include <iostream>
#include <thread>
#include <chrono>
#include <cassert>

using namespace ws;

/**
 * @brief 测试工具
 */
class TestRunner {
public:
    static void assert_eq(int expected, int actual, const std::string& msg) {
        if (expected != actual) {
            std::cerr << "FAIL: " << msg << " (expected " << expected
                      << ", got " << actual << ")" << std::endl;
            failures_++;
        }
    }

    static void assert_true(bool condition, const std::string& msg) {
        if (!condition) {
            std::cerr << "FAIL: " << msg << std::endl;
            failures_++;
        }
    }

    static int failures() { return failures_; }

private:
    static int failures_;
};

int TestRunner::failures_ = 0;

/**
 * @brief 测试服务器启动和停止
 */
void test_server_start_stop() {
    std::cout << "Testing server start/stop..." << std::endl;

    ServerConfig config;
    config.port = 18080;
    config.host = "127.0.0.1";

    Server server(config);

    // 测试启动
    bool started = server.start();
    TestRunner::assert_true(started, "Server should start successfully");

    if (started) {
        // 测试运行状态
        TestRunner::assert_true(server.is_running(), "Server should be running");

        // 停止服务器
        server.stop();
        TestRunner::assert_true(!server.is_running(), "Server should be stopped");
    }

    std::cout << "  Done" << std::endl;
}

/**
 * @brief 测试连接回调
 */
void test_connection_callbacks() {
    std::cout << "Testing connection callbacks..." << std::endl;

    ServerConfig config;
    config.port = 18081;
    config.host = "127.0.0.1";

    Server server(config);

    bool open_called = false;
    bool close_called = false;
    bool message_called = false;

    server.set_on_open([&open_called](ConnectionPtr conn) {
        open_called = true;
        std::cout << "  Connection opened: " << conn->id() << std::endl;
    });

    server.set_on_close([&close_called](ConnectionPtr conn, CloseCode code,
                                         const std::string& reason) {
        close_called = true;
        std::cout << "  Connection closed: " << conn->id() << std::endl;
    });

    server.set_on_message([&message_called](ConnectionPtr conn, const Message& msg) {
        message_called = true;
        std::cout << "  Message received: " << msg.text() << std::endl;

        // 回显消息
        conn->send_text(msg.text());
    });

    if (server.start()) {
        // 给服务器一些时间启动
        std::this_thread::sleep_for(std::chrono::milliseconds(100));

        // 停止服务器
        server.stop();
    }

    std::cout << "  Done" << std::endl;
}

/**
 * @brief 测试消息路由
 */
void test_message_routing() {
    std::cout << "Testing message routing..." << std::endl;

    Router router;

    bool handler1_called = false;
    bool handler2_called = false;

    // 注册路由
    router.on("chat", "message", [&handler1_called](const RouteContext& ctx) {
        handler1_called = true;
    });

    router.on("game", "move", [&handler2_called](const RouteContext& ctx) {
        handler2_called = true;
    });

    // 测试默认消息解析器
    Message msg1 = Message::text_message("{\"action\":\"message\",\"path\":\"chat\"}");
    auto [path1, action1] = Router::default_message_parser(msg1);

    TestRunner::assert_true(path1 == "chat", "Path should be 'chat'");
    TestRunner::assert_true(action1 == "message", "Action should be 'message'");

    std::cout << "  Done" << std::endl;
}

/**
 * @brief 测试房间系统
 */
void test_room_system() {
    std::cout << "Testing room system..." << std::endl;

    RoomManager room_mgr;

    // 测试创建房间
    auto room = room_mgr.create_room("test_room");
    TestRunner::assert_true(room != nullptr, "Room should be created");
    TestRunner::assert_true(room_mgr.has_room("test_room"), "Room should exist");

    // 测试房间列表
    auto names = room_mgr.room_names();
    TestRunner::assert_eq(1, names.size(), "Should have 1 room");

    // 测试销毁房间
    room_mgr.destroy_room("test_room");
    TestRunner::assert_true(!room_mgr.has_room("test_room"), "Room should be destroyed");

    std::cout << "  Done" << std::endl;
}

/**
 * @brief 测试速率限制
 */
void test_rate_limiter() {
    std::cout << "Testing rate limiter..." << std::endl;

    RateLimiter limiter(3, 1000);  // 每秒 3 个请求

    // 测试正常请求
    TestRunner::assert_true(limiter.allow("client1"), "First request should be allowed");
    TestRunner::assert_true(limiter.allow("client1"), "Second request should be allowed");
    TestRunner::assert_true(limiter.allow("client1"), "Third request should be allowed");
    TestRunner::assert_true(!limiter.allow("client1"), "Fourth request should be blocked");

    // 测试不同客户端
    TestRunner::assert_true(limiter.allow("client2"), "Different client should be allowed");

    // 测试剩余配额
    TestRunner::assert_eq(0, limiter.remaining("client1"), "Client1 should have 0 remaining");
    TestRunner::assert_eq(2, limiter.remaining("client2"), "Client2 should have 2 remaining");

    // 测试重置
    limiter.reset("client1");
    TestRunner::assert_true(limiter.allow("client1"), "After reset, request should be allowed");

    std::cout << "  Done" << std::endl;
}

/**
 * @brief 测试输入验证
 */
void test_input_validator() {
    std::cout << "Testing input validator..." << std::endl;

    InputValidator validator(1024, 512);

    // 测试正常文本
    Message msg1 = Message::text_message("Hello, World!");
    TestRunner::assert_true(validator.validate(msg1), "Normal text should be valid");

    // 测试过长文本
    std::string long_text(600, 'A');
    Message msg2 = Message::text_message(long_text);
    TestRunner::assert_true(!validator.validate(msg2), "Too long text should be invalid");

    // 测试正常二进制
    std::vector<uint8_t> binary = {0x01, 0x02, 0x03};
    Message msg3 = Message::binary_message(binary);
    TestRunner::assert_true(validator.validate(msg3), "Normal binary should be valid");

    // 测试过大二进制
    std::vector<uint8_t> large_binary(2000, 0x00);
    Message msg4 = Message::binary_message(large_binary);
    TestRunner::assert_true(!validator.validate(msg4), "Too large binary should be invalid");

    std::cout << "  Done" << std::endl;
}

/**
 * @brief 测试认证器
 */
void test_authenticator() {
    std::cout << "Testing authenticator..." << std::endl;

    SimpleTokenAuthenticator auth;

    // 添加令牌
    auth.add_token("valid_token", "user1");

    // 测试有效令牌
    auto result1 = auth.authenticate(nullptr, "valid_token");
    TestRunner::assert_true(result1.success, "Valid token should authenticate");
    TestRunner::assert_true(result1.user_id == "user1", "User ID should match");

    // 测试无效令牌
    auto result2 = auth.authenticate(nullptr, "invalid_token");
    TestRunner::assert_true(!result2.success, "Invalid token should fail");

    // 移除令牌
    auth.remove_token("valid_token");
    auto result3 = auth.authenticate(nullptr, "valid_token");
    TestRunner::assert_true(!result3.success, "Removed token should fail");

    std::cout << "  Done" << std::endl;
}

/**
 * @brief 测试 SimpleJson
 */
void test_simple_json() {
    std::cout << "Testing SimpleJson..." << std::endl;

    // 测试解析
    std::string json = "{\"name\":\"test\",\"value\":\"123\"}";
    auto map = SimpleJson::parse(json);

    TestRunner::assert_true(map["name"] == "test", "Name should be 'test'");
    TestRunner::assert_true(map["value"] == "123", "Value should be '123'");

    // 测试 get
    auto name = SimpleJson::get(json, "name");
    TestRunner::assert_true(name.has_value(), "Should have name");
    TestRunner::assert_true(*name == "test", "Name should be 'test'");

    // 测试 stringify
    std::unordered_map<std::string, std::string> data = {{"key", "value"}};
    auto str = SimpleJson::stringify(data);
    TestRunner::assert_true(str.find("\"key\"") != std::string::npos, "Should contain key");
    TestRunner::assert_true(str.find("\"value\"") != std::string::npos, "Should contain value");

    std::cout << "  Done" << std::endl;
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== WebSocket Connection Tests ===" << std::endl;

    test_server_start_stop();
    test_connection_callbacks();
    test_message_routing();
    test_room_system();
    test_rate_limiter();
    test_input_validator();
    test_authenticator();
    test_simple_json();

    std::cout << "\n=== Test Results ===" << std::endl;
    if (TestRunner::failures() == 0) {
        std::cout << "All tests passed!" << std::endl;
    } else {
        std::cout << TestRunner::failures() << " test(s) failed" << std::endl;
    }

    return TestRunner::failures();
}
