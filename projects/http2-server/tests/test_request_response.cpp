/**
 * @file test_request_response.cpp
 * @brief HTTP 请求/响应测试
 */

#include "http2_request.h"
#include "http2_response.h"
#include <iostream>
#include <cassert>

using namespace http2;

void test_request_basic() {
    std::cout << "Testing basic request..." << std::endl;

    HttpRequest request;

    request.set_method(HttpMethod::GET);
    request.set_path("/api/data");
    request.set_query("key=value&page=1");
    request.set_stream_id(1);

    assert(request.get_method() == HttpMethod::GET);
    assert(request.get_method_string() == "GET");
    assert(request.get_path() == "/api/data");
    assert(request.get_query() == "key=value&page=1");
    assert(request.get_stream_id() == 1);

    std::cout << "  PASSED" << std::endl;
}

void test_request_method_string() {
    std::cout << "Testing request method string..." << std::endl;

    HttpRequest request;

    request.set_method("GET");
    assert(request.get_method() == HttpMethod::GET);

    request.set_method("POST");
    assert(request.get_method() == HttpMethod::POST);

    request.set_method("PUT");
    assert(request.get_method() == HttpMethod::PUT);

    request.set_method("DELETE");
    assert(request.get_method() == HttpMethod::DELETE_);

    request.set_method("HEAD");
    assert(request.get_method() == HttpMethod::HEAD);

    request.set_method("OPTIONS");
    assert(request.get_method() == HttpMethod::OPTIONS);

    request.set_method("PATCH");
    assert(request.get_method() == HttpMethod::PATCH);

    request.set_method("UNKNOWN");
    assert(request.get_method() == HttpMethod::UNKNOWN);

    std::cout << "  PASSED" << std::endl;
}

void test_request_headers() {
    std::cout << "Testing request headers..." << std::endl;

    HttpRequest request;

    request.set_header("Content-Type", "application/json");
    request.set_header("Authorization", "Bearer token123");

    assert(request.has_header("content-type"));
    assert(request.has_header("Content-Type"));
    assert(request.has_header("CONTENT-TYPE"));

    assert(request.get_header("content-type") == "application/json");
    assert(request.get_header("authorization") == "Bearer token123");

    assert(!request.has_header("X-Custom"));

    std::cout << "  PASSED" << std::endl;
}

void test_request_body() {
    std::cout << "Testing request body..." << std::endl;

    HttpRequest request;

    // 字符串正文
    request.set_body("Hello, World!");
    assert(request.get_body_string() == "Hello, World!");
    assert(request.get_body_size() == 13);

    // 字节正文
    std::vector<uint8_t> bytes = {0x01, 0x02, 0x03};
    request.set_body(bytes);
    assert(request.get_body_size() == 3);
    assert(request.get_body() == bytes);

    std::cout << "  PASSED" << std::endl;
}

void test_request_query_params() {
    std::cout << "Testing request query parameters..." << std::endl;

    HttpRequest request;

    request.set_query("name=Alice&age=30&city=New%20York");
    request.parse_query_string();

    assert(request.get_query_param("name") == "Alice");
    assert(request.get_query_param("age") == "30");
    assert(request.get_query_param("city") == "New York");
    assert(request.get_query_param("unknown") == "");

    std::cout << "  PASSED" << std::endl;
}

void test_response_basic() {
    std::cout << "Testing basic response..." << std::endl;

    HttpResponse response;

    response.set_status(HttpStatusCode::OK);
    assert(response.get_status() == HttpStatusCode::OK);
    assert(response.get_status_code() == 200);
    assert(response.get_status_message() == "OK");

    response.set_status(404);
    assert(response.get_status() == HttpStatusCode::NOT_FOUND);
    assert(response.get_status_message() == "Not Found");

    std::cout << "  PASSED" << std::endl;
}

void test_response_headers() {
    std::cout << "Testing response headers..." << std::endl;

    HttpResponse response;

    response.set_header("Content-Type", "application/json");
    response.set_header("X-Custom", "value");

    assert(response.has_header("content-type"));
    assert(response.get_header("content-type") == "application/json");
    assert(response.get_header("x-custom") == "value");

    // 测试快捷方法
    response.set_content_type("text/html");
    assert(response.get_header("content-type") == "text/html");

    response.set_content_length(1024);
    assert(response.get_header("content-length") == "1024");

    std::cout << "  PASSED" << std::endl;
}

void test_response_body() {
    std::cout << "Testing response body..." << std::endl;

    HttpResponse response;

    // 字符串正文
    response.set_body("Hello, World!");
    assert(response.get_body_string() == "Hello, World!");
    assert(response.get_body_size() == 13);
    assert(response.get_header("content-length") == "13");

    // 追加正文
    response.append_body(" More text.");
    assert(response.get_body_string() == "Hello, World! More text.");

    std::cout << "  PASSED" << std::endl;
}

void test_response_cache_control() {
    std::cout << "Testing response cache control..." << std::endl;

    HttpResponse response;

    response.set_cache_control("max-age=3600");
    assert(response.get_header("cache-control") == "max-age=3600");

    response.set_etag("\"abc123\"");
    assert(response.get_header("etag") == "\"abc123\"");

    response.set_last_modified("Wed, 21 Oct 2025 07:28:00 GMT");
    assert(response.get_header("last-modified") == "Wed, 21 Oct 2025 07:28:00 GMT");

    response.set_expires("Thu, 01 Dec 2025 16:00:00 GMT");
    assert(response.get_header("expires") == "Thu, 01 Dec 2025 16:00:00 GMT");

    std::cout << "  PASSED" << std::endl;
}

void test_response_cors() {
    std::cout << "Testing response CORS..." << std::endl;

    HttpResponse response;

    response.set_cors_headers();

    assert(response.get_header("access-control-allow-origin") == "*");
    assert(!response.get_header("access-control-allow-methods").empty());
    assert(!response.get_header("access-control-allow-headers").empty());
    assert(response.get_header("access-control-max-age") == "86400");

    // 自定义来源
    response.set_cors_headers("https://example.com");
    assert(response.get_header("access-control-allow-origin") == "https://example.com");

    std::cout << "  PASSED" << std::endl;
}

void test_response_stream_id() {
    std::cout << "Testing response stream ID..." << std::endl;

    HttpResponse response;

    response.set_stream_id(5);
    assert(response.get_stream_id() == 5);

    std::cout << "  PASSED" << std::endl;
}

void test_status_codes() {
    std::cout << "Testing status codes..." << std::endl;

    HttpResponse response;

    // 测试各种状态码
    struct StatusTest {
        HttpStatusCode code;
        int numeric;
        std::string message;
    };

    std::vector<StatusTest> tests = {
        {HttpStatusCode::OK, 200, "OK"},
        {HttpStatusCode::CREATED, 201, "Created"},
        {HttpStatusCode::NO_CONTENT, 204, "No Content"},
        {HttpStatusCode::MOVED_PERMANENTLY, 301, "Moved Permanently"},
        {HttpStatusCode::NOT_MODIFIED, 304, "Not Modified"},
        {HttpStatusCode::BAD_REQUEST, 400, "Bad Request"},
        {HttpStatusCode::UNAUTHORIZED, 401, "Unauthorized"},
        {HttpStatusCode::FORBIDDEN, 403, "Forbidden"},
        {HttpStatusCode::NOT_FOUND, 404, "Not Found"},
        {HttpStatusCode::METHOD_NOT_ALLOWED, 405, "Method Not Allowed"},
        {HttpStatusCode::TOO_MANY_REQUESTS, 429, "Too Many Requests"},
        {HttpStatusCode::INTERNAL_SERVER_ERROR, 500, "Internal Server Error"},
        {HttpStatusCode::NOT_IMPLEMENTED, 501, "Not Implemented"},
        {HttpStatusCode::BAD_GATEWAY, 502, "Bad Gateway"},
        {HttpStatusCode::SERVICE_UNAVAILABLE, 503, "Service Unavailable"},
    };

    for (const auto& test : tests) {
        response.set_status(test.code);
        assert(response.get_status_code() == test.numeric);
        assert(response.get_status_message() == test.message);
    }

    std::cout << "  PASSED" << std::endl;
}

int main() {
    std::cout << "Running HTTP Request/Response Tests..." << std::endl;
    std::cout << std::endl;

    test_request_basic();
    test_request_method_string();
    test_request_headers();
    test_request_body();
    test_request_query_params();
    test_response_basic();
    test_response_headers();
    test_response_body();
    test_response_cache_control();
    test_response_cors();
    test_response_stream_id();
    test_status_codes();

    std::cout << std::endl;
    std::cout << "All request/response tests PASSED!" << std::endl;

    return 0;
}
