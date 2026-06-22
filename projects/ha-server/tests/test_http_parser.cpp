/**
 * @file test_http_parser.cpp
 * @brief HTTP 解析器单元测试
 *
 * 测试 HTTP 请求和响应的解析：
 * - 请求行解析
 * - 请求头解析
 * - 请求体解析
 * - 错误处理
 */

#include "../include/http_parser.h"
#include <iostream>
#include <cassert>

using namespace ha_server;

/**
 * 测试简单的 GET 请求解析
 */
void test_simple_get_request() {
    std::cout << "Testing simple GET request..." << std::endl;

    std::string raw_request =
        "GET /index.html HTTP/1.1\r\n"
        "Host: example.com\r\n"
        "Connection: keep-alive\r\n"
        "\r\n";

    HttpRequest request;
    bool success = HttpParser::parse_request(
        raw_request.c_str(), raw_request.size(), request);

    assert(success);
    assert(request.method == "GET");
    assert(request.path == "/index.html");
    assert(request.version == "HTTP/1.1");
    assert(request.get_header("Host") == "example.com");
    assert(request.get_header("Connection") == "keep-alive");
    assert(request.keep_alive == true);
    assert(request.body.empty());

    std::cout << "  Passed: GET request parsed correctly" << std::endl;
}

/**
 * 测试带请求体的 POST 请求
 */
void test_post_request_with_body() {
    std::cout << "Testing POST request with body..." << std::endl;

    std::string body = "{\"name\":\"test\",\"value\":123}";
    std::string raw_request =
        "POST /api/data HTTP/1.1\r\n"
        "Host: example.com\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: " + std::to_string(body.size()) + "\r\n"
        "\r\n" +
        body;

    HttpRequest request;
    bool success = HttpParser::parse_request(
        raw_request.c_str(), raw_request.size(), request);

    assert(success);
    assert(request.method == "POST");
    assert(request.path == "/api/data");
    assert(request.get_header("Content-Type") == "application/json");
    assert(request.body == body);

    std::cout << "  Passed: POST request with body parsed correctly" << std::endl;
}

/**
 * 测试 HTTP/1.0 请求（默认关闭连接）
 */
void test_http10_request() {
    std::cout << "Testing HTTP/1.0 request..." << std::endl;

    std::string raw_request =
        "GET /index.html HTTP/1.0\r\n"
        "Host: example.com\r\n"
        "\r\n";

    HttpRequest request;
    bool success = HttpParser::parse_request(
        raw_request.c_str(), raw_request.size(), request);

    assert(success);
    assert(request.version == "HTTP/1.0");
    assert(request.keep_alive == false);  // HTTP/1.0 默认关闭

    std::cout << "  Passed: HTTP/1.0 request parsed correctly" << std::endl;
}

/**
 * 测试 Connection: close 头部
 */
void test_connection_close() {
    std::cout << "Testing Connection: close..." << std::endl;

    std::string raw_request =
        "GET /index.html HTTP/1.1\r\n"
        "Host: example.com\r\n"
        "Connection: close\r\n"
        "\r\n";

    HttpRequest request;
    bool success = HttpParser::parse_request(
        raw_request.c_str(), raw_request.size(), request);

    assert(success);
    assert(request.keep_alive == false);

    std::cout << "  Passed: Connection: close handled correctly" << std::endl;
}

/**
 * 测试错误的请求格式
 */
void test_invalid_request() {
    std::cout << "Testing invalid request..." << std::endl;

    std::string raw_request = "INVALID REQUEST FORMAT";

    HttpRequest request;
    bool success = HttpParser::parse_request(
        raw_request.c_str(), raw_request.size(), request);

    assert(!success);

    std::cout << "  Passed: Invalid request rejected" << std::endl;
}

/**
 * 测试分块解析
 */
void test_chunked_parsing() {
    std::cout << "Testing chunked parsing..." << std::endl;

    HttpParser parser;

    // 第一块数据
    std::string chunk1 = "GET /index.html HTT";
    int parsed1 = parser.parse(chunk1.c_str(), chunk1.size());
    assert(parsed1 == 0);  // 请求行不完整
    assert(!parser.is_complete());

    // 第二块数据
    std::string chunk2 = "P/1.1\r\nHost: example.com\r\n\r\n";
    int parsed2 = parser.parse(chunk2.c_str(), chunk2.size());
    assert(parser.is_complete());

    const HttpRequest& request = parser.get_request();
    assert(request.method == "GET");
    assert(request.path == "/index.html");

    std::cout << "  Passed: Chunked parsing works correctly" << std::endl;
}

/**
 * 测试响应序列化
 */
void test_response_serialization() {
    std::cout << "Testing response serialization..." << std::endl;

    HttpResponse response;
    response.status_code = 200;
    response.status_text = "OK";
    response.set_header("Content-Type", "text/plain");
    response.set_header("Connection", "keep-alive");
    response.body = "Hello, World!";

    std::string serialized = response.to_string();

    assert(serialized.find("HTTP/1.1 200 OK") != std::string::npos);
    assert(serialized.find("Content-Type: text/plain") != std::string::npos);
    assert(serialized.find("Connection: keep-alive") != std::string::npos);
    assert(serialized.find("Hello, World!") != std::string::npos);

    std::cout << "  Passed: Response serialized correctly" << std::endl;
}

/**
 * 测试错误响应
 */
void test_error_response() {
    std::cout << "Testing error response..." << std::endl;

    HttpResponse response = HttpResponse::error_response(503, "Service Unavailable");

    assert(response.status_code == 503);
    assert(response.status_text == "Service Unavailable");
    assert(response.body == "Service Unavailable");
    assert(response.get_header("Connection") == "close");

    std::string serialized = response.to_string();
    assert(serialized.find("503 Service Unavailable") != std::string::npos);

    std::cout << "  Passed: Error response created correctly" << std::endl;
}

/**
 * 测试请求序列化
 */
void test_request_serialization() {
    std::cout << "Testing request serialization..." << std::endl;

    HttpRequest request;
    request.method = "GET";
    request.path = "/index.html";
    request.version = "HTTP/1.1";
    request.headers["Host"] = "example.com";
    request.headers["Connection"] = "keep-alive";

    std::string serialized = request.to_string();

    assert(serialized.find("GET /index.html HTTP/1.1") != std::string::npos);
    assert(serialized.find("Host: example.com") != std::string::npos);
    assert(serialized.find("Connection: keep-alive") != std::string::npos);

    std::cout << "  Passed: Request serialized correctly" << std::endl;
}

int main() {
    std::cout << "=== HTTP Parser Tests ===" << std::endl;
    std::cout << std::endl;

    test_simple_get_request();
    std::cout << std::endl;

    test_post_request_with_body();
    std::cout << std::endl;

    test_http10_request();
    std::cout << std::endl;

    test_connection_close();
    std::cout << std::endl;

    test_invalid_request();
    std::cout << std::endl;

    test_chunked_parsing();
    std::cout << std::endl;

    test_response_serialization();
    std::cout << std::endl;

    test_error_response();
    std::cout << std::endl;

    test_request_serialization();
    std::cout << std::endl;

    std::cout << "=== All HTTP Parser Tests Passed ===" << std::endl;
    return 0;
}
