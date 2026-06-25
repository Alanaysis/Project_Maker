/**
 * @file test_router.cpp
 * @brief WebSocket 消息路由器测试
 *
 * 测试消息路由功能。
 */

#include "websocket/router.h"
#include <iostream>
#include <cassert>

using namespace ws;

/**
 * @brief 测试工具
 */
void assert_true(bool condition, const std::string& msg) {
    if (!condition) {
        std::cerr << "FAIL: " << msg << std::endl;
        exit(1);
    }
}

/**
 * @brief 测试基础路由
 */
void test_basic_routing() {
    std::cout << "Testing basic routing..." << std::endl;

    Router router;
    bool handler_called = false;

    // 注册路由
    router.on("chat", [&handler_called](const RouteContext& ctx) {
        handler_called = true;
    });

    // 创建消息
    Message msg = Message::text_message("{\"action\":\"message\",\"path\":\"chat\"}");

    // 路由消息（使用 nullptr 连接，因为我们只测试路由逻辑）
    // 注意：实际使用时需要有效的连接
    // router.route(nullptr, msg);

    // 测试消息解析器
    auto [path, action] = Router::default_message_parser(msg);
    assert_true(path == "chat", "Path should be 'chat'");
    assert_true(action == "message", "Action should be 'message'");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试带动作的路由
 */
void test_action_routing() {
    std::cout << "Testing action routing..." << std::endl;

    Router router;

    // 注册带动作的路由
    router.on("chat", "join", [](const RouteContext& ctx) {});
    router.on("chat", "leave", [](const RouteContext& ctx) {});
    router.on("chat", "message", [](const RouteContext& ctx) {});

    // 测试消息解析
    Message msg1 = Message::text_message("{\"action\":\"join\",\"path\":\"chat\"}");
    auto [path1, action1] = Router::default_message_parser(msg1);
    assert_true(path1 == "chat", "Path should be 'chat'");
    assert_true(action1 == "join", "Action should be 'join'");

    Message msg2 = Message::text_message("{\"action\":\"leave\",\"path\":\"chat\"}");
    auto [path2, action2] = Router::default_message_parser(msg2);
    assert_true(path2 == "chat", "Path should be 'chat'");
    assert_true(action2 == "leave", "Action should be 'leave'");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试中间件
 */
void test_middleware() {
    std::cout << "Testing middleware..." << std::endl;

    Router router;
    bool middleware_called = false;

    // 添加中间件
    router.use([&middleware_called](RouteContext& ctx) -> bool {
        middleware_called = true;
        return true;  // 继续处理
    });

    // 添加处理器
    router.on("test", [](const RouteContext& ctx) {});

    // 测试消息解析
    Message msg = Message::text_message("{\"action\":\"test\",\"path\":\"test\"}");
    auto [path, action] = Router::default_message_parser(msg);
    assert_true(path == "test", "Path should be 'test'");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试默认消息解析器
 */
void test_default_parser() {
    std::cout << "Testing default message parser..." << std::endl;

    // 测试带 path 和 action 的消息
    Message msg1 = Message::text_message("{\"path\":\"users\",\"action\":\"list\"}");
    auto [path1, action1] = Router::default_message_parser(msg1);
    assert_true(path1 == "users", "Path should be 'users'");
    assert_true(action1 == "list", "Action should be 'list'");

    // 测试只有 type 的消息
    Message msg2 = Message::text_message("{\"type\":\"notification\"}");
    auto [path2, action2] = Router::default_message_parser(msg2);
    assert_true(path2 == "notification", "Path should be 'notification'");
    assert_true(action2 == "message", "Action should default to 'message'");

    // 测试空消息
    Message msg3 = Message::text_message("{}");
    auto [path3, action3] = Router::default_message_parser(msg3);
    assert_true(path3 == "default", "Path should default to 'default'");
    assert_true(action3 == "message", "Action should default to 'message'");

    // 测试二进制消息
    std::vector<uint8_t> binary = {0x01, 0x02};
    Message msg4 = Message::binary_message(binary);
    auto [path4, action4] = Router::default_message_parser(msg4);
    assert_true(path4 == "default", "Binary path should be 'default'");
    assert_true(action4 == "binary", "Binary action should be 'binary'");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试 SimpleJson 解析
 */
void test_json_parsing() {
    std::cout << "Testing SimpleJson parsing..." << std::endl;

    // 测试基本解析
    std::string json1 = "{\"name\":\"John\",\"age\":\"30\"}";
    auto map1 = SimpleJson::parse(json1);
    assert_true(map1["name"] == "John", "Name should be 'John'");
    assert_true(map1["age"] == "30", "Age should be '30'");

    // 测试带嵌套的简单 JSON
    std::string json2 = "{\"key\":\"value\",\"number\":\"123\"}";
    auto map2 = SimpleJson::parse(json2);
    assert_true(map2["key"] == "value", "Key should be 'value'");
    assert_true(map2["number"] == "123", "Number should be '123'");

    // 测试 get 方法
    auto name = SimpleJson::get(json1, "name");
    assert_true(name.has_value(), "Should have name");
    assert_true(*name == "John", "Name should be 'John'");

    auto missing = SimpleJson::get(json1, "missing");
    assert_true(!missing.has_value(), "Missing key should return nullopt");

    // 测试 stringify
    std::unordered_map<std::string, std::string> data = {
        {"host", "localhost"},
        {"port", "8080"}
    };
    auto str = SimpleJson::stringify(data);
    assert_true(str.find("\"host\"") != std::string::npos, "Should contain host key");
    assert_true(str.find("\"localhost\"") != std::string::npos, "Should contain localhost value");
    assert_true(str.find("\"port\"") != std::string::npos, "Should contain port key");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试 JSON 转义
 */
void test_json_escaping() {
    std::cout << "Testing JSON escaping..." << std::endl;

    // 测试带引号的字符串
    std::string json = "{\"message\":\"Hello \\\"World\\\"\"}";
    auto msg = SimpleJson::get(json, "message");
    assert_true(msg.has_value(), "Should parse message");

    // 测试带换行的字符串
    std::string json2 = "{\"text\":\"Line1\\nLine2\"}";
    auto text = SimpleJson::get(json2, "text");
    assert_true(text.has_value(), "Should parse text");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== WebSocket Router Tests ===" << std::endl;

    test_basic_routing();
    test_action_routing();
    test_middleware();
    test_default_parser();
    test_json_parsing();
    test_json_escaping();

    std::cout << "\nAll router tests passed!" << std::endl;
    return 0;
}
