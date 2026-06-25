/**
 * @file client_example.cpp
 * @brief cpp-httplib HTTP 客户端示例
 * @details 展示如何使用 cpp-httplib 创建 HTTP 客户端
 */

#include <iostream>
#include <string>
#include <httplib.h>

/**
 * @brief 基础 GET 请求示例
 * @details 展示如何发送 GET 请求
 */
void basic_get() {
    std::cout << "=== 基础 GET 请求 ===" << std::endl;

    httplib::Client cli("httpbin.org");

    auto res = cli.Get("/get");
    if (res) {
        std::cout << "Status: " << res->status << std::endl;
        std::cout << "Body: " << res->body.substr(0, 200) << "..." << std::endl;
    } else {
        std::cerr << "Request failed" << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief 带参数的 GET 请求示例
 * @details 展示如何发送带参数的 GET 请求
 */
void get_with_params() {
    std::cout << "=== 带参数的 GET 请求 ===" << std::endl;

    httplib::Client cli("httpbin.org");

    httplib::Params params;
    params.emplace("key1", "value1");
    params.emplace("key2", "value2");

    auto res = cli.Get("/get", params, httplib::Headers{});
    if (res) {
        std::cout << "Status: " << res->status << std::endl;
        std::cout << "Body: " << res->body.substr(0, 200) << "..." << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief POST 请求示例
 * @details 展示如何发送 POST 请求
 */
void post_request() {
    std::cout << "=== POST 请求 ===" << std::endl;

    httplib::Client cli("httpbin.org");

    httplib::Params params;
    params.emplace("name", "alice");
    params.emplace("age", "30");

    auto res = cli.Post("/post", params);
    if (res) {
        std::cout << "Status: " << res->status << std::endl;
        std::cout << "Body: " << res->body.substr(0, 200) << "..." << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief JSON 请求示例
 * @details 展示如何发送 JSON 请求
 */
void json_request() {
    std::cout << "=== JSON 请求 ===" << std::endl;

    httplib::Client cli("httpbin.org");

    std::string json_body = R"({"name": "Alice", "age": 30})";

    auto res = cli.Post("/post", json_body, "application/json");
    if (res) {
        std::cout << "Status: " << res->status << std::endl;
        std::cout << "Body: " << res->body.substr(0, 200) << "..." << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief cpp-httplib 概念说明
 * @details 介绍 cpp-httplib 的核心概念
 */
void httplib_concepts() {
    std::cout << "=== cpp-httplib 概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "cpp-httplib 是一个简单易用的 HTTP 库。" << std::endl;
    std::cout << std::endl;

    std::cout << "主要特点：" << std::endl;
    std::cout << "  - 单头文件库" << std::endl;
    std::cout << "  - 简单易用的 API" << std::endl;
    std::cout << "  - 支持 HTTP/HTTPS" << std::endl;
    std::cout << "  - 支持服务器和客户端" << std::endl;
    std::cout << std::endl;

    std::cout << "常用方法：" << std::endl;
    std::cout << "  - Get() - GET 请求" << std::endl;
    std::cout << "  - Post() - POST 请求" << std::endl;
    std::cout << "  - Put() - PUT 请求" << std::endl;
    std::cout << "  - Delete() - DELETE 请求" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== cpp-httplib HTTP 客户端示例 ===" << std::endl;
    std::cout << std::endl;

    httplib_concepts();

    // 注意：以下示例需要网络连接
    // basic_get();
    // get_with_params();
    // post_request();
    // json_request();

    std::cout << "=== 示例结束 ===" << std::endl;
    std::cout << std::endl;
    std::cout << "注意：完整的 httplib 示例需要网络连接" << std::endl;
    std::cout << "请取消注释 main() 中的函数调用来运行示例" << std::endl;

    return 0;
}