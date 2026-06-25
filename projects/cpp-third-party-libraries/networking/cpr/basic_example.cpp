/**
 * @file basic_example.cpp
 * @brief CPR HTTP 请求库基础示例
 * @details 展示 CPR 的基本用法
 *          CPR 是一个 C++ HTTP 请求库
 *          类似 Python 的 requests 库
 */

#include <iostream>
#include <string>
#include <cpr/cpr.h>

/**
 * @brief 基础 GET 请求示例
 * @details 展示如何发送 GET 请求
 */
void basic_get() {
    std::cout << "=== 基础 GET 请求 ===" << std::endl;

    // 发送 GET 请求
    cpr::Response r = cpr::Get(cpr::Url{"https://httpbin.org/get"});

    std::cout << "Status code: " << r.status_code << std::endl;
    std::cout << "Content type: " << r.header["content-type"] << std::endl;
    std::cout << "Body: " << r.text.substr(0, 200) << "..." << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 带参数的 GET 请求示例
 * @details 展示如何发送带参数的 GET 请求
 */
void get_with_params() {
    std::cout << "=== 带参数的 GET 请求 ===" << std::endl;

    // 使用 Parameters
    cpr::Response r = cpr::Get(
        cpr::Url{"https://httpbin.org/get"},
        cpr::Parameters{
            {"key1", "value1"},
            {"key2", "value2"}
        }
    );

    std::cout << "Status code: " << r.status_code << std::endl;
    std::cout << "URL: " << r.url << std::endl;

    std::cout << std::endl;
}

/**
 * @brief POST 请求示例
 * @details 展示如何发送 POST 请求
 */
void post_request() {
    std::cout << "=== POST 请求 ===" << std::endl;

    // 发送 POST 请求
    cpr::Response r = cpr::Post(
        cpr::Url{"https://httpbin.org/post"},
        cpr::Payload{
            {"key1", "value1"},
            {"key2", "value2"}
        }
    );

    std::cout << "Status code: " << r.status_code << std::endl;
    std::cout << "Body: " << r.text.substr(0, 200) << "..." << std::endl;

    std::cout << std::endl;
}

/**
 * @brief JSON 请求示例
 * @details 展示如何发送 JSON 请求
 */
void json_request() {
    std::cout << "=== JSON 请求 ===" << std::endl;

    // 发送 JSON 请求
    cpr::Response r = cpr::Post(
        cpr::Url{"https://httpbin.org/post"},
        cpr::Header{{"Content-Type", "application/json"}},
        cpr::Body{"{\"name\": \"Alice\", \"age\": 30}"}
    );

    std::cout << "Status code: " << r.status_code << std::endl;
    std::cout << "Body: " << r.text.substr(0, 200) << "..." << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 会话管理示例
 * @details 展示如何使用会话管理
 */
void session_example() {
    std::cout << "=== 会话管理 ===" << std::endl;

    // 创建会话
    cpr::Session session;
    session.SetUrl(cpr::Url{"https://httpbin.org/get"});
    session.SetHeader(cpr::Header{{"User-Agent", "CPR Example"}});

    // 发送请求
    cpr::Response r = session.Get();

    std::cout << "Status code: " << r.status_code << std::endl;
    std::cout << "User-Agent: " << r.header["user-agent"] << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 错误处理示例
 * @details 展示如何处理请求错误
 */
void error_handling() {
    std::cout << "=== 错误处理 ===" << std::endl;

    // 请求一个不存在的 URL
    cpr::Response r = cpr::Get(cpr::Url{"https://httpbin.org/status/404"});

    std::cout << "Status code: " << r.status_code << std::endl;

    if (r.status_code == 404) {
        std::cout << "Resource not found" << std::endl;
    } else if (r.status_code >= 400) {
        std::cout << "Client error" << std::endl;
    } else if (r.status_code >= 500) {
        std::cout << "Server error" << std::endl;
    } else {
        std::cout << "Success" << std::endl;
    }

    // 检查是否有网络错误
    if (r.error.code != cpr::ErrorCode::OK) {
        std::cout << "Network error: " << r.error.message << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief CPR 概念说明
 * @details 介绍 CPR 的核心概念
 */
void cpr_concepts() {
    std::cout << "=== CPR 概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "CPR 是 C++ Requests 的缩写。" << std::endl;
    std::cout << std::endl;

    std::cout << "主要特点：" << std::endl;
    std::cout << "  - 简洁的 API" << std::endl;
    std::cout << "  - 类似 Python requests" << std::endl;
    std::cout << "  - 支持 HTTP/HTTPS" << std::endl;
    std::cout << "  - 支持代理" << std::endl;
    std::cout << "  - 支持认证" << std::endl;
    std::cout << std::endl;

    std::cout << "常用方法：" << std::endl;
    std::cout << "  - cpr::Get()" << std::endl;
    std::cout << "  - cpr::Post()" << std::endl;
    std::cout << "  - cpr::Put()" << std::endl;
    std::cout << "  - cpr::Delete()" << std::endl;
    std::cout << "  - cpr::Patch()" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== CPR HTTP 请求库示例 ===" << std::endl;
    std::cout << std::endl;

    cpr_concepts();

    // 注意：以下示例需要网络连接
    // basic_get();
    // get_with_params();
    // post_request();
    // json_request();
    // session_example();
    // error_handling();

    std::cout << "=== 示例结束 ===" << std::endl;
    std::cout << std::endl;
    std::cout << "注意：完整的 CPR 示例需要网络连接" << std::endl;
    std::cout << "请取消注释 main() 中的函数调用来运行示例" << std::endl;

    return 0;
}